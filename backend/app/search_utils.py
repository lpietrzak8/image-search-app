from io import BytesIO
from PIL import Image
from config import get_secret
import requests
import logging
import time
import os

ORIGINAL_API = "https://pixabay.com/api/?key="

API_KEY = get_secret('PIXABAY_API_KEY')

PIXABAY_API = ORIGINAL_API + API_KEY

def fetch_images_tag(pixabay_search_keyword, num_images):
    query = (
        PIXABAY_API
        + "&q="
        + pixabay_search_keyword.lower()
        + "&image_type=photo&safesearch=true&per_page="
        + str(num_images)
    )
    logging.info(
        f"Making requests to Pixabay for {num_images} images to fetch with {pixabay_search_keyword} keyword."
    )

    response = requests.get(query)
    logging.info(f"Fetched search results")
    output = response.json()

    all_images = []
    all_image_urls = []
    for each in output["hits"]:
        image_url = each["wenformatURL"]
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content)).convert("RGB")
        all_images.append(image)
        all_image_urls.append(image_url)
    
    logging.info(f"Fetched indyvidual results.")

    return (all_images, all_image_urls)