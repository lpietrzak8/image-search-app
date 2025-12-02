from io import BytesIO
from PIL import Image
from config import get_secret, UPLOAD_FOLDER, CLIP_MOUNT_PATH, build_posts_array
import requests
import logging
from db_connector import Keyword
import os
from flask import url_for, current_app

ORIGINAL_API = "https://pixabay.com/api/?key="
API_KEY = get_secret('PIXABAY_API_KEY')
PIXABAY_API = ORIGINAL_API + API_KEY


def fetch_images_tag(search_keyword, num_images):
    logging.info(
        f"Fetching up to {num_images} images for keyword '{search_keyword}' from Pixabay."
    )

    query = (
        PIXABAY_API
        + "&q="
        + search_keyword.lower()
        + "&image_type=photo&safesearch=true&per_page="
        + str(num_images)
    )

    response = requests.get(query)
    output = response.json()

    all_clip_paths = []
    all_posts_json = []
    pixabay_folder = os.path.join(UPLOAD_FOLDER, "pixabay")
    os.makedirs(pixabay_folder, exist_ok=True)

    for hit in output.get("hits", []):
        image_url = hit.get("webformatURL")
        author = hit.get("user")

        if not image_url:
            continue

        try:
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
            
            filename = f"{search_keyword}_{os.path.basename(image_url).split('?')[0]}"
            local_path = os.path.join(pixabay_folder, filename)
            image.save(local_path)
            
            clip_path = local_path.replace(UPLOAD_FOLDER, CLIP_MOUNT_PATH, 1)
            all_clip_paths.append(clip_path)

            public_url = url_for("serve_image", filename=f"pixabay/{filename}", _external=True)
            
            all_posts_json.append({
                "id": f"pixabay-{hit.get("id")}",
                "author": author,
                "description": None,
                "keywords": [search_keyword],
                "image_url": public_url,
                "source_url": hit.get("pageURL")})
        
        except Exception as e:
            logging.warning(f"Failed to fetch {image_url}: {e}")
    
    logging.info(f"Fetched {len(all_posts_json)} images from Pixabay.")

    logging.info(f"Searching database for keyword '{search_keyword}")
    
    with current_app.app_context():
        keyword = Keyword.query.filter_by(name=search_keyword).first()

        if keyword:
            db_images_count = 0
            local_images = []

            for post in keyword.posts:
                local_path = os.path.join(UPLOAD_FOLDER, post.image_path)
                
                if os.path.exists(local_path):
                    clip_path = local_path.replace(UPLOAD_FOLDER, CLIP_MOUNT_PATH, 1)
                    all_clip_paths.append(clip_path)

                    local_images.append(post)
                    db_images_count += 1
            
            logging.info(f"Fetched {db_images_count} images for keyword '{search_keyword}'.")

            local_posts_json = build_posts_array(local_images)
            
            all_posts_json.extend(local_posts_json)
        else:
            logging.info(f"No local images found for keyword '{search_keyword}'.")

    return (all_clip_paths, all_posts_json)