from config import get_secret
import requests
import os
import logging
from config import UPLOAD_FOLDER, CLIP_MOUNT_PATH
from io import BytesIO
from PIL import Image
from flask import url_for
from abc import ABC, abstractmethod
import re

class APIProvider(ABC):
    API_UPLOADS_FOLDER = ""

    @classmethod
    def saveImage(cls, image_url, keyword):
        os.makedirs(cls.API_UPLOADS_FOLDER, exist_ok=True)

        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content)).convert("RGB")

        safe_keyword = re.sub(r"[^a-zA-Z0-9_-]", "_", keyword.lower())
        filename = f"{safe_keyword}_{os.path.basename(image_url).split('?')[0]}"
        local_path = os.path.join(cls.API_UPLOADS_FOLDER, filename)
        
        image.save(local_path)
        return local_path, filename

    @classmethod
    @abstractmethod
    def fetch(cls, keyword, num_images):
        pass


class PixabayProvider(APIProvider):
    PIXABAY_ORIGINAL_API = "https://pixabay.com/api/?key="
    PIXABAY_API_KEY = get_secret('PIXABAY_API_KEY')
    PIXABAY_API = PIXABAY_ORIGINAL_API + PIXABAY_API_KEY

    API_UPLOADS_FOLDER = os.path.join(UPLOAD_FOLDER, "pixabay")
    
    @classmethod
    def fetch(cls, keyword, num_images):
        query = (
            cls.PIXABAY_API
            + "&q="
            + keyword.lower()
            + "&image_type=photo&safesearch=true&per_page="
            + str(num_images)
        )

        logging.info(f"Fetching up to {num_images} images for keyword '{keyword}' from Pixabay.")


        response = requests.get(query)
        response.raise_for_status()
        output = response.json()

        clip_paths = []
        posts_json = []

        for hit in output.get("hits", []):
            image_url = hit.get("webformatURL")
            author = hit.get("user")

            if not image_url:
                continue

            try:
                local_path, filename = cls.saveImage(image_url, keyword)
                
                clip_path = local_path.replace(UPLOAD_FOLDER, CLIP_MOUNT_PATH, 1)
                clip_paths.append(clip_path)

                public_url = url_for("serve_image", filename=f"pixabay/{filename}")
                
                posts_json.append({
                    "id": f"pixabay-{hit.get("id")}",
                    "author": author,
                    "description": None,
                    "keywords": [keyword],
                    "image_url": public_url,
                    "source_url": hit.get("pageURL")})
            
            except Exception as e:
                logging.warning(f"Failed to fetch {image_url}: {e}")
        
        logging.info(f"Fetched {len(posts_json)} images from Pixabay.")
        return clip_paths, posts_json

class PixelsProvider(APIProvider):
    PIXELS_URL = "https://api.pexels.com/v1/search"
    PIXELS_API_KEY = get_secret('PIXELS_API_KEY')
    API_UPLOADS_FOLDER = os.path.join(UPLOAD_FOLDER, "pixels")

    HEADERS = {"Authorization": PIXELS_API_KEY}
    
    @classmethod
    def fetch(cls, keyword, num_images):
        params = {"query": keyword, "per_page": num_images}
        response = requests.get(cls.PIXELS_URL, headers=cls.HEADERS, params=params, timeout=10)
        response.raise_for_status()
        output = response.json()
        
        os.makedirs(cls.API_UPLOADS_FOLDER, exist_ok=True)

        clip_paths = []
        posts_json = []
        
        for photo in output.get("photos", []):
            image_url = photo["src"]["original"]
            author = photo["photographer"]

            if not image_url:
                continue

            try:

                local_path, filename = cls.saveImage(image_url, keyword)
                
                clip_path = local_path.replace(UPLOAD_FOLDER, CLIP_MOUNT_PATH, 1)
                clip_paths.append(clip_path)

                public_url = url_for("serve_image", filename=f"pixels/{filename}")
                
                posts_json.append({
                    "id": f"pixels-{photo.get("id")}",
                    "author": author,
                    "description": photo.get("description"),
                    "keywords": [keyword],
                    "image_url": public_url,
                    "source_url": photo.get("url")})
            
            except Exception as e:
                logging.warning(f"Failed to fetch {image_url}: {e}")
        
        logging.info(f"Fetched {len(posts_json)} images from Pixels.")
        return clip_paths, posts_json

# class UnsplashProvider(APIProvider):
    


API_PROVIDERS = [
    PixabayProvider,
      PixelsProvider
      ]