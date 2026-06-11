import os
from flask import Flask, request, jsonify, g, send_from_directory, stream_with_context, Response, url_for
from flask_cors import CORS
from flask_healthz import healthz, HealthError
import json
from werkzeug.utils import secure_filename
from db_connector import db, Post, Keyword, BlacklistedImage, UserSavedPhoto
from config import get_secret, build_posts_array, UPLOAD_FOLDER, verify_recaptcha, allowed_file
from API_providers import API_PROVIDERS
from searcher import Searcher
from key_words import getKeyWords
from keycloak_config import *
from services.blacklist_service import get_blocked_and_suspended_urls
from sqlalchemy.orm import joinedload
import time
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed


from contextlib import contextmanager

@contextmanager
def timer(label):
    start = time.perf_counter()
    yield
    elapsed = (time.perf_counter() - start) * 1000
    print(f"[TIMER] {label}: {elapsed:.2f}ms", flush=True)

MAX_SEARCH = 30
search_jobs = {}

app = Flask(__name__)
app.register_blueprint(healthz, url_prefix="/")

cors = CORS(
    app,
    resources={
        r"/api/*": {"origin": "*"},
        r"/health/*": {"origin": "*"},
    }
)


def printok():
    print("Everything is ok")

def liveness():
    try:
        printok()
    except Exception:
        raise HealthError("Can't connect to the file")

def readiness():
    try:
        printok()
    except Exception:
        raise HealthError("Can't connect to the file")

app.config.update(
    HEALTHZ = {
        "alive": "app.liveness",
        "ready": "app.readiness",
    }
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db_password = get_secret('MYSQL_ROOT_PASSWORD')

logging.info("Waiting for database and clip to fully start.")
time.sleep(5)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{db_password}@database:3306/photos_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

searcher = Searcher(API_PROVIDERS)

@app.route("/api/search", methods=['GET'])
def start_search():
    query = request.args.get("s_query").lower()
    top_k = int(request.args.get("k", 30))

    job_id = str(uuid.uuid4())

    search_jobs[job_id] = {
        "query": query,
        "top_k": top_k,
        "status": "queued",
        "result": None,
    }

    return jsonify({"job_id": job_id})

def search_generator(job_id):
    job = search_jobs[job_id]

    query = job["query"].lower()
    top_k = job["top_k"]

    keywords = getKeyWords(query)

    if not keywords:
        yield {"event": "error", "data": f"No results for '{query}"}
        return
    
        
    all_results = []
    tags = keywords + ([query] if len(keywords) > 1 else [])
    total = len(tags)

    yield {
        "event": "progress",
        "data": {"current": 0, "total": total, "percent": 0, "tag": tags[0]},
    }

    def fetch_tag(tag):
        with app.app_context():
            with timer(f"get_similar_images [{tag}]"):
                return tag, searcher.get_similar_images(tag, query, MAX_SEARCH, top_k)

    with ThreadPoolExecutor(max_workers=len(tags)) as executor:
        futures = {executor.submit(fetch_tag, tag): tag for tag in tags}
        done = 0
        for future in as_completed(futures):
            tag, result = future.result()
            if result:
                top_images, top_scores = result
                for image, score in zip(top_images, top_scores):
                    all_results.append((image, score))
            done += 1
            yield {
                "event": "progress",
                "data": {
                    "current": done,
                    "total": total,
                    "percent": int(done / total * 100),
                    "tag": tag,
                },
            }
    
    seen = set()
    deduped = []
    for image, score in all_results:
        key = image.get("source_url")
        if key not in seen:
            seen.add(key)
            deduped.append((image, score))

    deduped.sort(key=lambda x: x[1], reverse=True)
    final_results = deduped[:top_k]
    final_images = [item[0] for item in final_results]
    
    job["result"] = final_images

    yield {
        "event": "done",
        "data": final_images
    }

@app.get("/api/search/stream/<job_id>")
def stream_search(job_id):

    def event_stream():
        for payload in search_generator(job_id):
            yield f"event: {payload['event']}\n"
            yield f"data: {json.dumps(payload['data'])}\n\n"
    
    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

@app.route('/api/createPost', methods=['POST'])
def post_image():
    author = request.form.get("author")
    description = request.form.get("description")
    keywords_raw = request.form.get("keywords")
    image = request.files.get("image")

    if not image:
        return jsonify({"error": "No image uploaded"}), 400
    if not author:
        return jsonify({"error": "Missing author"}), 400
    if not description:
        return jsonify({"error": "Missing description"}), 400
    
    try:
        keywords_list = json.loads(keywords_raw)
    except Exception:
        keywords_list = [kw.strip() for kw in keywords_raw.split(",")]

    folder = os.path.join(UPLOAD_FOLDER, author)
    os.makedirs(folder, exist_ok=True)

    filename = secure_filename(image.filename)
    filepath = os.path.join(folder, filename)
    image.save(filepath)

    relative_path = os.path.relpath(filepath, UPLOAD_FOLDER)

    keyword_objects = []
    for kw in keywords_list:
        keyword = Keyword.query.filter_by(name=kw).first()
        if not keyword:
            keyword = Keyword(name=kw)
        keyword_objects.append(keyword)

    new_post = Post(
            provider="PHOTO-SEARCH",
            author_name=author,
            author_url=None,
            description=description,
            image_path=relative_path,
            image_url=url_for("serve_image", filename=relative_path),
            source_url=url_for("serve_image", filename=relative_path),
            keywords=keyword_objects,
            status="pending"
        )
    db.session.add(new_post)
    db.session.commit()

    return jsonify({"message": "Post created"}), 201

@app.route('/api/posts/byKeyword/<string:keyword_name>', methods=["GET"])
def get_posts_by_keywords(keyword_name):
    keyword = Keyword.query.filter_by(name=keyword_name).first()

    if not keyword:
        return jsonify({"error": f"Keyword '{keyword_name}' not found"}), 404
    
    posts = keyword.posts
    return jsonify(build_posts_array(posts)), 200


@app.route('/api/admin/posts', methods=["GET"])
@require_admin
def get_posts():
    provider = request.args.get('provider')
    status = request.args.get('status')

    if provider and status:
        posts = Post.query.filter_by(provider=provider, status=status).all()
    elif provider:
        posts = Post.query.filter_by(provider=provider).all()
    elif status:
        posts = Post.query.filter_by(status=status).all()
    else:
        posts = Post.query.all()
    return jsonify(build_posts_array(posts)), 200

@app.route('/api/admin/posts/<post_id>/approve', methods=["PUT"])
@require_admin
def approve_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status="approved"
    db.session.commit()

    return jsonify({"message": f"Image {post_id} approved"})

@app.route('/api/admin/posts/<post_id>/reject', methods=["PUT"])
@require_admin
def reject_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status="rejected"
    db.session.commit()

    return jsonify({"message": f"Image {post_id} rejected"})


@app.route('/api/admin/posts/<post_id>', methods=["DELETE"])
@require_admin
def delete_post(post_id):
    img = Post.query.get_or_404(post_id)
    path = img.image_path

    try:
        if not path:
            db.session.delete(img)
            db.session.commit()

            return jsonify({"message": "Post deleted"})
    
        full_path = os.path.join(UPLOAD_FOLDER, path)
        
        os.remove(full_path)
        
        db.session.delete(img)
        db.session.commit()

        return jsonify({"message": "Post deleted"})
    except OSError as e:
        return jsonify({"message": f"{full_path} cannot be removed.", 
                        "e": str(e)}), 404
    except Exception:
        return jsonify({"message": "Something went wrong"})

@app.route('/api/uploads/<path:filename>')
def serve_image(filename):
    safe_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(safe_path):
        return jsonify({"error": f"Image '{filename}' not found"}), 404
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/contribute', methods=['POST'])
def contribute_image():
    """Handle image contribution with reCAPTCHA verification."""
    try:
        # Get reCAPTCHA token
        recaptcha_token = request.form.get('recaptcha_token', '')
        
        # Verify reCAPTCHA
        if not verify_recaptcha(recaptcha_token):
            return jsonify({"error": "reCAPTCHA verification failed"}), 400
        
        # Check if image is uploaded
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        image = request.files['image']
        if image.filename == '':
            return jsonify({"error": "No image selected"}), 400
        
        # Get description
        description = request.form.get('description', '').strip()
        if not description:
            return jsonify({"error": "Description is required"}), 400
        
        if len(description) < 10:
            return jsonify({"error": "Description must be at least 10 characters long"}), 400
        
        if len(description) > 1000:
            return jsonify({"error": "Description must be less than 1000 characters"}), 400
        
        # Validate image file
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
        allowed_mimetypes = {'image/png', 'image/jpeg', 'image/webp'}
        
        if not allowed_file(image.filename, allowed_extensions):
            return jsonify({"error": "Invalid file extension. Allowed: PNG, JPG, JPEG, WebP"}), 400
        
        if not hasattr(image, 'mimetype') or image.mimetype not in allowed_mimetypes:
            return jsonify({"error": "Invalid file type. Must be an image"}), 400
        
        # Check file size (max 10MB)
        image.seek(0, os.SEEK_END)
        file_size = image.tell()
        image.seek(0)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({"error": "File size must be less than 10MB"}), 400
        
        # Generate unique filename
        file_extension = os.path.splitext(image.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create contribution folder
        contribution_folder = os.path.join(UPLOAD_FOLDER, "contributions")
        os.makedirs(contribution_folder, exist_ok=True)
        
        # Save image
        image_path = os.path.join(contribution_folder, unique_filename)
        image.save(image_path)
        
        # Extract keywords from description
        keywords = getKeyWords(description)
        keyword_objects = []
        for kw in keywords if keywords else []:
            keyword = Keyword.query.filter_by(name=kw).first()
            if not keyword:
                keyword = Keyword(name=kw)
            keyword_objects.append(keyword)
        
        image_path = os.path.relpath(image_path, UPLOAD_FOLDER)
        # Create database entry
        new_post = Post(
            provider="PHOTO-SEARCH",
            author_name="contributor",
            author_url=None,
            description=description,
            image_path=image_path,
            image_url=url_for("serve_image", filename=image_path),
            source_url=url_for("serve_image", filename=image_path),
            keywords=keyword_objects,
            status="pending"
        )
        db.session.add(new_post)
        db.session.commit()
        
        logging.info(f"New contribution: post_id={new_post.id}, filename={unique_filename}")
        
        return jsonify({
            "message": "Thank you for your contribution!",
            "post_id": new_post.id
        }), 201
        
    except Exception as e:
        logging.error(f"Contribution error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/blacklist/suspend", methods=['POST'])
def suspend_image():
    data = request.get_json()

    existing = BlacklistedImage.query.filter_by(source_url=data["source_url"]).first()

    if existing:
        if existing.status == "blocked":
            return jsonify({
                "message": "Post already blocked"
            }), 200
        
        return jsonify({
            "message": "Post already suspended"
        }), 200

    entry = BlacklistedImage(
        provider=data["provider"],
        source_url=data["source_url"],
        image_url=data["image_url"],
        description=data["description"],
        status="suspended",
        reason=data.get("reason")
    )

    db.session.add(entry)
    db.session.commit()

    return jsonify({"message": "Post suspended"}), 201

@app.route("/api/blacklist/suspended", methods=['GET'])
@require_admin
def list_suspended():
    images = BlacklistedImage.query.filter_by(status="suspended"
    ).order_by(
        BlacklistedImage.created_at.desc()
    ).all()


    return jsonify([
        {
            "id": img.id,
            "provider": img.provider,
            "source_url": img.source_url,
            "image_url": img.image_url,
            "description": img.description,
            "reason": img.reason,
            "status": "blacklisted"
        }
        for img in images
    ])

@app.route("/api/blacklist/blocked", methods=['GET'])
@require_admin
def list_blocked():    
    images = BlacklistedImage.query.filter_by(
        status="blocked"
    ).order_by(
        BlacklistedImage.updated_at.desc()
    ).all()
    
    return jsonify([
        {
            "id": img.id,
            "provider": img.provider,
            "source_url": img.source_url,
            "image_url": img.image_url,
            "description": img.description,
            "reason": img.reason,
            "status": "blacklisted"
        }
        for img in images
    ])

@app.route("/api/blacklist/block/<int:image_id>", methods=['PATCH'])
@require_admin
def block_image(image_id):
    img = BlacklistedImage.query.get_or_404(image_id)
    img.status = "blocked"
    db.session.commit()

    return jsonify({"message": "Image blocked"})

@app.route("/api/blacklist/<int:image_id>", methods=['DELETE'])
@require_admin
def remove_from_blacklist(image_id):
    img = BlacklistedImage.query.get_or_404(image_id)
    db.session.delete(img)
    db.session.commit()

    return jsonify({"message": "Image removed from blacklist"})

@app.route('/api/user/photos', methods=['GET'])
@require_auth
def get_user_photos():
    """Get all saved photos for the authenticated user."""
    saved_relations = (
        UserSavedPhoto.query
        .options(joinedload(UserSavedPhoto.post))
        .filter_by(user_id=g.user_id)
        .order_by(UserSavedPhoto.created_at.desc())
        .all()
    )

    photos = [rel.post for rel in saved_relations]
    
    blocked_urls = get_blocked_and_suspended_urls()
    filtered_photos = filter(
        lambda photo: photo.source_url not in blocked_urls,
        photos)
    
    return build_posts_array(filtered_photos)

@app.route('/api/user/photos', methods=['POST'])
@require_auth
def save_user_photo():
    """Save a photo to the user's account."""
    data = request.get_json()

    if not data or not data.get('source_url'):
        return jsonify({"error": "source_url is required"}), 400

    post = Post.query.filter_by(
        provider=data["provider"],
        source_url=data['source_url']
    ).first()

    if not post:

        post = Post(
            provider = data["provider"],

            author_name = data["author"]["name"],
            author_url = data["author"]["url"],

            description = data["description"] or "",

            image_url = data["image_url"],
            source_url = data["source_url"]
        )
        
        db.session.add(post)

    for keyword_name in data.get("keywords", []):

        keyword = Keyword.query.filter_by(
            name=keyword_name
        ).first()

        if not keyword:
            keyword = Keyword(name=keyword_name)
            db.session.add(keyword)
        
        if keyword not in post.keywords:
            post.keywords.append(keyword)

        db.session.flush()
    
    existing_saved = UserSavedPhoto.query.filter_by(
        user_id=g.user_id,
        post_id=post.id
    ).first()

    if existing_saved:
        return jsonify({"error": "Photo already saved", "id": existing_saved.id}), 409

    saved_photo = UserSavedPhoto(
        user_id=g.user_id,
        post_id=post.id
    )

    db.session.add(saved_photo)
    db.session.commit()

    return jsonify({"message": "Photo saved", "id": saved_photo.id}), 201

@app.route('/api/user/photos/<int:post_id>', methods=['DELETE'])
@require_auth
def delete_user_photo(post_id):
    """Remove a photo from the user's account."""
    photo = UserSavedPhoto.query.filter_by(id=post_id, user_id=g.user_id).first()

    if not photo:
        return jsonify({"error": "Photo not found"}), 404

    db.session.delete(photo)

    remaining = UserSavedPhoto.query.filter_by(post_id=post_id).count()

    if remaining == 0:
        post = Post.query.get(post_id)
        if post and post.provider != "PHOTO-SEARCH":
            db.session.delete(post)
    
    db.session.commit()


    return jsonify({"message": "Photo removed"}), 200

@app.route('/health', methods=['GET'])
def healthcheck():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)