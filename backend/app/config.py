import os
from flask import url_for
import logging
import requests

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
CLIP_MOUNT_PATH = "/data/images"

def get_secret(name):
    file_var = os.getenv(f"{name}_FILE")
    if file_var and os.path.exists(file_var):
        with open(file_var, 'r') as pw_file:
            return pw_file.read().strip()
    return os.getenv(name)

CAPTHCHA_KEY = get_secret('CAPTCHA_KEY')

def build_posts_array(posts):
    results = []
    for post in posts:
        results.append({
            "id": f"local-{post.id}",
            "author": {
                "name": post.author,
                "url": None
            },
            "description": post.description,
            "keywords": [kw.name for kw in post.keywords],
            "image_url": url_for("serve_image", filename=post.image_path),
            "source_url": url_for("serve_image", filename=post.image_path),
            "provider": "PHOTO-SEARCH"
        })
    return results

def verify_recaptcha(token):
    """Verify reCAPTCHA token with Google API."""
    if not token:
        return False
    
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': CAPTHCHA_KEY,
                'response': token
            },
            timeout=5
        )
        
        result = response.json()
        logging.info(f"reCAPTCHA verification: success={result.get('success')}, score={result.get('score')}")
        
        # For v3, check score (0.0 - 1.0, higher is better)
        if result.get('success') and result.get('score', 0) >= 0.5:
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"reCAPTCHA verification error: {str(e)}")
        return False

def allowed_file(filename, allowed_extensions):
    """Check if file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions