from io import BytesIO
from PIL import Image
from config import get_secret, UPLOAD_FOLDER
import requests
import logging
from db_connector import Keyword
import os
from flask import url_for, current_app

ORIGINAL_API = "https://pixabay.com/api/?key="

API_KEY = get_secret('PIXABAY_API_KEY')

PIXABAY_API = ORIGINAL_API + API_KEY

def fetch_images_tag(search_keyword, num_images):
    query = (
        PIXABAY_API
        + "&q="
        + search_keyword.lower()
        + "&image_type=photo&safesearch=true&per_page="
        + str(num_images)
    )
    logging.info(
        f"Making requests to Pixabay for {num_images} images to fetch with {search_keyword} keyword."
    )

    response = requests.get(query)
    logging.info(f"Fetched search results")
    output = response.json()

    all_image_paths = []
    all_image_urls = []
    pixabay_folder = os.path.join(UPLOAD_FOLDER, "pixabay")
    os.makedirs(pixabay_folder, exist_ok=True)

    for each in output.get("hits", []):
        image_url = each.get("webformatURL")
        try:
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
            local_filename = f"{search_keyword}_{os.path.basename(image_url).split('?')[0]}"
            local_path = os.path.join(pixabay_folder, local_filename)
            image.save(local_path)
            all_image_paths.append(local_path)
            all_image_urls.append(image_url)
        except Exception as e:
            logging.warning(f"Failed to fetch {image_url}: {e}")
    
    logging.info(f"Fetched indyvidual results.")

    logging.info(f"Searching database for keyword")
    with current_app.app_context():
        keyword = Keyword.query.filter_by(name=search_keyword).first()

        if keyword:
            db_images = 0
            for post in keyword.posts:
                local_path = os.path.join(UPLOAD_FOLDER, post.image_path)
                if os.path.exists(local_path):
                    all_image_paths.append(local_path)
                    image_url = url_for("serve_image", filename=post.image_path, _external=True)
                    all_image_urls.append(image_url)
                    db_images += 1

            logging.info(f"Fetched {db_images} images for keyword '{search_keyword}'.")
        else:
            logging.info(f"No local images found for keyword '{search_keyword}'.")

    return (all_image_paths, all_image_urls)