import requests
import os
import logging
from config import UPLOAD_FOLDER, CLIP_MOUNT_PATH, get_secret
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from flask import url_for
from abc import ABC, abstractmethod
import re
import uuid
from requests.exceptions import HTTPError

AI_KEYWORDS = ["ai", "generated", "midjourney", "stable diffusion", "dall-e", "sora", "flux", "deepai"]

def looks_like_ai(metadata):
    text = " ".join([
        metadata.get("description", ""),
        metadata.get("alt", ""),
        " ".join(metadata.get("tags", []))
    ]).lower()
    return any(k in text for k in AI_KEYWORDS)

class APIProvider(ABC):
    API_UPLOADS_FOLDER = ""
    def __init__(self, api_key):
        self.api_key = api_key

    def saveImage(self, image_url, keyword, extension="jpg"):
        os.makedirs(self.API_UPLOADS_FOLDER, exist_ok=True)

        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content)).convert("RGB")

        safe_keyword = re.sub(r"[^a-zA-Z0-9_-]", "_", keyword.lower())
        filename = f"{safe_keyword}_{uuid.uuid4().hex}.{extension}"
        local_path = os.path.join(self.API_UPLOADS_FOLDER, filename)
        
        image.save(local_path)
        return local_path, filename

    @abstractmethod
    def fetch(self, keyword, num_images):
        pass


class PixabayProvider(APIProvider):
    PIXABAY_ORIGINAL_API = "https://pixabay.com/api/"
    API_UPLOADS_FOLDER = os.path.join(UPLOAD_FOLDER, "pixabay")
    
    def __init__(self, api_key):
        super().__init__(api_key)


    def fetch(self, keyword, num_images):

        logging.info(f"Fetching up to {num_images} images for keyword '{keyword}' from Pixabay.")

        try:
            response = requests.get(
                self.PIXABAY_ORIGINAL_API,
                params={
                    "key": self.api_key,
                    "q": keyword.lower(),
                    "safesearch": "true",
                    "per_page": num_images
                },
                timeout=10)
            
            response.raise_for_status()
            output = response.json()

            clip_paths = []
            posts_json = []

            for hit in output.get("hits", []):
                if looks_like_ai(hit):
                    continue

                image_url = hit.get("webformatURL")
                author = hit.get("user")

                if not image_url:
                    continue

                local_path, filename = self.saveImage(image_url, keyword)
                
                clip_path = local_path.replace(UPLOAD_FOLDER, CLIP_MOUNT_PATH, 1)
                clip_paths.append(clip_path)

                public_url = url_for("serve_image", filename=f"pixabay/{filename}")
                
                posts_json.append({
                    "id": f"pixabay-{hit.get("id")}",
                    "author": {
                        "name": author,
                        "url": None
                    },
                    "description": None,
                    "keywords": [keyword],
                    "image_url": public_url,
                    "source_url": hit.get("pageURL"),
                    "provider": "pixabay"})
        except  HTTPError as e:
            logging.error(f"Failed to fetch from Pixabay. Error message: {e}")    
        except (requests.RequestException, OSError, UnidentifiedImageError) as e:
            logging.warning(f"Failed to fetch {image_url}: {e}")
        
        logging.info(f"Fetched {len(posts_json)} images from Pixabay.")
        return clip_paths, posts_json

class PexelsProvider(APIProvider):
    PEXELS_URL = "https://api.pexels.com/v1/search"
    API_UPLOADS_FOLDER = os.path.join(UPLOAD_FOLDER, "pexels")
    
    def __init__(self, api_key):
        super().__init__(api_key)
        self.HEADERS = {"Authorization": api_key}
    
    def fetch(self, keyword, num_images):
        clip_paths = []
        posts_json = []
        
        try:
            response = requests.get(
                self.PEXELS_URL,
                headers=self.HEADERS,
                params={
                    "query": keyword,
                    "per_page": num_images
                    },
                    timeout=10)
            
            response.raise_for_status()
            output = response.json()
            
            for photo in output.get("photos", []):
                if looks_like_ai(photo):
                    continue

                image_url = photo["src"]["original"]
                author = photo["photographer"]

                if not image_url:
                    continue
                local_path, filename = self.saveImage(image_url, keyword)
                
                clip_path = local_path.replace(UPLOAD_FOLDER, CLIP_MOUNT_PATH, 1)
                clip_paths.append(clip_path)

                public_url = url_for("serve_image", filename=f"pexels/{filename}")
                
                posts_json.append({
                    "id": f"pexels-{photo.get("id")}",
                    "author": {
                        "name": author,
                        "url": photo.get("photographer_url")
                    },
                    "description": photo.get("description"),
                    "keywords": [keyword],
                    "image_url": public_url,
                    "source_url": photo.get("url"),
                    "provider": "pexels"})
        
        except  HTTPError as e:
            logging.error(f"Failed to fetch from Pexels. Error message: {e}")
        except (requests.RequestException, OSError, UnidentifiedImageError) as e:
            logging.warning(f"Failed to fetch {image_url}: {e}")
        
        logging.info(f"Fetched {len(posts_json)} images from Pexels.")
        return clip_paths, posts_json

class UnsplashProvider(APIProvider):
    UNSPLASH_API = f"https://api.unsplash.com/search/photos"
    API_UPLOADS_FOLDER = os.path.join(UPLOAD_FOLDER, "unsplash")
    
    def __init__(self, api_key):
        super().__init__(api_key)
        self.HEADERS = {
            "Authorization": f"Client-ID {api_key}",
            "Accept-Version": "v1"
            }
    

    def fetch(self, keyword, num_images):
        clip_paths = []
        posts_json = []

        logging.info(f"Fetching up to {num_images} images for keyword '{keyword}' from Unsplash.")

        try:
            response = requests.get(
                self.UNSPLASH_API, 
                headers=self.HEADERS,
                params={
                    "query": keyword.lower(),
                    "per_page": min(num_images, 10)
                },
                timeout=10)
            
            response.raise_for_status()
            output = response.json()

            for result in output.get("results", []):
                image_url = result["urls"]["regular"]
                
                if not image_url:
                    continue

                requests.get(
                    result["links"]["download"],
                    headers=self.HEADERS,
                    timeout=5
                )

                local_path, filename = self.saveImage(image_url, keyword)
                
                clip_path = local_path.replace(UPLOAD_FOLDER, CLIP_MOUNT_PATH, 1)
                clip_paths.append(clip_path)

                public_url = url_for("serve_image", filename=f"unsplash/{filename}")
                
                posts_json.append({
                    "id": f"unsplash-{result.get("id")}",
                    "author": {
                        "name": result["user"]["name"],
                        "url": result["user"]["links"]["html"]
                    },
                    "description": result.get("description"),
                    "keywords": [keyword],
                    "image_url": public_url,
                    "source_url": result.get("links").get("html"),
                    "provider": "unsplash"})
        except  HTTPError as e:
            logging.error(f"Failed to fetch from Unsplash API. Error message: {e}")
        except (requests.RequestException, OSError, UnidentifiedImageError) as e:
            logging.warning(f"Failed to fetch {image_url}: {e}")
        
        logging.info(f"Fetched {len(posts_json)} images from Unsplash.")
        return clip_paths, posts_json
        
    
def build_providers_list():
    providers = []

    if get_secret('PIXABAY_API_KEY'):
        providers.append(PixabayProvider(get_secret('PIXABAY_API_KEY')))
    
    if get_secret('UNSPLASH_API_KEY'):
        providers.append(UnsplashProvider(get_secret('UNSPLASH_API_KEY')))
    
    if get_secret('PEXELS_API_KEY'):
        providers.append(PexelsProvider(get_secret('PEXELS_API_KEY')))

    return providers


API_PROVIDERS = build_providers_list()