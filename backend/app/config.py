import os
from flask import url_for

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
CLIP_MOUNT_PATH = "/data/images"

def get_secret(name):
    file_var = os.getenv(f"{name}_FILE")
    if file_var and os.path.exists(file_var):
        with open(file_var, 'r') as pw_file:
            return pw_file.read().strip()
    return os.getenv(name)

def build_posts_array(posts):
    results = []
    for post in posts:
        results.append({
            "id": post.id,
            "author": post.author,
            "description": post.description,
            "keywords": [kw.name for kw in post.keywords],
            "image_url": url_for("serve_image", filename=post.image_path, _external=True)
        })
    return results