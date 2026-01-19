import os
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from flask_healthz import healthz, HealthError
import json
from werkzeug.utils import secure_filename
from db_connector import db, Post, Keyword, BlacklistedImage
from config import get_secret, build_posts_array, UPLOAD_FOLDER, verify_recaptcha, allowed_file
from API_providers import API_PROVIDERS
from searcher import Searcher
from key_words import getKeyWords
import time
import logging
import uuid

MAX_SEARCH = 30

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
def get_images():
    query = request.args.get("s_query").lower()
    keywords = getKeyWords(query)
    top_k = int(request.args.get("k"))

    if not keywords:
        return jsonify({"error_message": f"No results for '{query}'."}), 404
    
    all_results = []

    for tag in keywords:
        
        top_images, top_scores = searcher.get_similar_images(
            tag, query, MAX_SEARCH, top_k
        )

        for image, score in zip(top_images, top_scores):
            all_results.append((image, score))
    
    all_results.sort(key = lambda x: x[1], reverse=True)

    final_results = all_results[:top_k]

    final_images = [item[0] for item in final_results]
    return jsonify(final_images)

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
        author=author,
        description=description,
        keywords=keyword_objects,
        image_path=relative_path,
    )
    db.session.add(new_post)
    db.session.commit()

    return jsonify({"message": "Post created"}), 201


@app.route('/api/posts', methods=["GET"])
def get_posts():
    posts = Post.query.all()
    return jsonify(build_posts_array(posts)), 200

@app.route('/api/posts/byKeyword/<string:keyword_name>', methods=["GET"])
def get_posts_by_keywords(keyword_name):
    keyword = Keyword.query.filter_by(name=keyword_name).first()

    if not keyword:
        return jsonify({"error": f"Keyword '{keyword_name}' not found"}), 404
    
    posts = keyword.posts
    return jsonify(build_posts_array(posts)), 200


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
        
        # Create database entry
        new_post = Post(
            author="contributor",
            description=description,
            keywords=keyword_objects,
            image_path=os.path.relpath(image_path, UPLOAD_FOLDER)
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

@app.route("/blacklist/suspend", methods=['POST'])
def suspend_image():
    data = request.get_json()

    entry = BlacklistedImage(
        provider=data["provider"],
        source_url=data["source_url"],
        status="suspended",
        reason=data.get("reason")
    )

    db.session.add(entry)
    db.session.commit()

    return jsonify({"message": "Post suspended"}), 201

@app.route("/blacklist/suspended", methods=['GET'])
def list_suspended():
    images = BlacklistedImage.query.filter_by(status="suspended").all()
    
    return jsonify([
        {
            "id": img.id,
            "provider": img.provider,
            "source_url": img.source_url,
            "reason": img.reason
        }
        for img in images
    ])

@app.route("/blacklist/blocked", methods=['GET'])
def list_suspended():
    images = BlacklistedImage.query.filter_by(status="blocked").all()
    
    return jsonify([
        {
            "id": img.id,
            "provider": img.provider,
            "source_url": img.source_url,
            "reason": img.reason
        }
        for img in images
    ])

@app.route("/blacklist/block/<int:image_id>", methods=['PATCH'])
def block_image(image_id):
    img = BlacklistedImage.query.get_or_404(image_id)
    img.status = "blocked"
    db.session.commit()

    return jsonify({"message": "Image blocked"})

@app.route("/blacklist/<int:image_id>", methods=['DELETE'])
def remove_from_blacklist(image_id):
    img = BlacklistedImage.query.get_or_404(image_id)
    db.session.delete(img)
    db.session.commit()

    return jsonify({"message": "Image removed from blacklist"})

@app.route('/health', methods=['GET'])
def healthcheck():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)