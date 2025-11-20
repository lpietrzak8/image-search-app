import os
import requests
from search_utils import fetch_images_tag
from direct_redis import DirectRedis

redis = os.getenv("REDIS_IN_USE", "false")
redis_host = "redis"
redis_port = 6379
redis_client = DirectRedis(host=redis_host, port=redis_port)

model_host = os.getenv("MODEL_HOST")
model_port = os.getenv("MODEL_PORT")


class Searcher:    
    def get_similar_images(self, keyword, semantic_query, pixabay_max, top_k):
        if redis == "true":
            images_redis_key = keyword + "_images"
            urls_redis_key = keyword + "_urls"

            if redis_client.exists(images_redis_key) and redis_client.exists(urls_redis_key):
                keyword_images = redis_client.get(images_redis_key)
                keyword_image_urls = redis_client.get(urls_redis_key)
            else:
                (keyword_images, keyword_image_urls) = fetch_images_tag(
                    keyword, pixabay_max
                )
                redis_client.set(images_redis_key, keyword_images)
                redis_client.set(urls_redis_key, keyword_image_urls)
        else:
            (keyword_images, keyword_image_objects) = fetch_images_tag(keyword, pixabay_max)
        
        response = requests.post(
            f"http://{model_host}:{model_port}/similarity",
            json={
                "images": keyword_images,
                "query": semantic_query,
                "top_k": top_k
            }
        )
        response.raise_for_status()
        result = response.json()

        indices = result["indices"]
        scores = result["scores"]
        
        top_imgs = [keyword_image_objects[i] for i in indices]
        return (top_imgs, scores)