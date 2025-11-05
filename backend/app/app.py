import os
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from flask_healthz import healthz, HealthError
import json
from werkzeug.utils import secure_filename
from db_connector import db, Post, Keyword
from config import get_secret, build_posts_array, UPLOAD_FOLDER
from searcher import Searcher
from key_words import getKeyWords

MAX_SEARCH = 30

app = Flask(__name__)
app.register_blueprint(healthz, url_prefix="/")

cors = CORS(
    app,
    resources={
        r"/search/*": {"origin": "*"},
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

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{db_password}@database:3306/photos_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

searcher = Searcher()

@app.route("/api/search", methods=['GET'])
def get_images():
    query = request.args.get("s_query").lower()
    tag = getKeyWords(query)[0] # pozniej mozna dodac sprawdzanie dla kazdego znalezionego keyworda
    top_k = request.args.get("k")

    (top_urls, top_scores) = searcher.get_similar_images(
        tag, query, MAX_SEARCH, int(top_k)
    )
    return jsonify({"top_urls": top_urls, "top_scores": top_scores})

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

@app.route('/health', methods=['GET'])
def healthcheck():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)