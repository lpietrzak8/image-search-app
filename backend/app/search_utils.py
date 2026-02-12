from config import UPLOAD_FOLDER, CLIP_MOUNT_PATH, build_posts_array
import logging
from db_connector import Keyword
import os
from flask import current_app
from services.blacklist_service import get_blocked_urls



def fetch_images_tag(search_keyword, num_images, api_providers):
    all_clip_paths = []
    all_posts_json = []

    blocked_urls = get_blocked_urls()
    for provider in api_providers:
        clip_paths, posts_json = provider.fetch(search_keyword, num_images, blocked_urls)
        all_clip_paths.extend(clip_paths)
        all_posts_json.extend(posts_json)

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