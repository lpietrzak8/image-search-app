from config import UPLOAD_FOLDER, CLIP_MOUNT_PATH, build_posts_array
import logging
from db_connector import db, Post, Keyword
import os
from flask import current_app
from services.blacklist_service import get_blocked_and_suspended_urls



def save_posts_to_db(posts_json):
    with current_app.app_context():
        for post_data in posts_json:
            source_url = post_data.get("source_url")
            if not source_url:
                continue

            post = Post.query.filter_by(source_url=source_url).first()
            if not post:
                post = Post(
                    provider=post_data["provider"],
                    author_name=(post_data["author"]["name"] or "")[:64],
                    author_url=post_data["author"].get("url"),
                    description=(post_data.get("description") or "")[:512],
                    image_url=post_data["image_url"],
                    source_url=source_url,
                    image_path=post_data.get("image_path"),
                )
                db.session.add(post)

            for kw_name in post_data.get("keywords", []):
                keyword = Keyword.query.filter_by(name=kw_name).first()
                if not keyword:
                    keyword = Keyword(name=kw_name)
                    db.session.add(keyword)
                if keyword not in post.keywords:
                    post.keywords.append(keyword)

            db.session.flush()

        try:
            db.session.commit()
            logging.info(f"Saved {len(posts_json)} posts to DB.")
        except Exception as e:
            db.session.rollback()
            try:
                db.session.commit()
                logging.info(f"Saved {len(posts_json)} posts to DB (retry).")
            except Exception as e2:
                logging.error(f"Failed to save posts to DB: {e2}")
                db.session.rollback()


def fetch_images_tag(search_keyword, num_images, api_providers):
    all_clip_paths = []
    all_posts_json = []
    blocked_urls = get_blocked_and_suspended_urls()
    

    logging.info(f"Searching database for keyword '{search_keyword}")
    
    with current_app.app_context():
        keyword = Keyword.query.filter_by(name=search_keyword).first()

        print(f"Keyword count: {Keyword.query.count()}",flush=True)

        if keyword:
            print(f"[DB] keyword found: {keyword.name}", flush=True)
        else:
            print(f"[DB] keyword NOT found: {search_keyword}", flush=True)

        if keyword:
            db_images_count = 0
            local_images = []

            for post in keyword.posts:

                if not post.image_path or post.status in ["pending", "rejected"]:
                    continue

                local_path = os.path.join(UPLOAD_FOLDER, post.image_path)
                
                if os.path.exists(local_path):
                    clip_path = local_path.replace(UPLOAD_FOLDER, CLIP_MOUNT_PATH, 1)
                    all_clip_paths.append(clip_path)

                    local_images.append(post)
                    db_images_count += 1

            if len(local_images) >= num_images:
                print(f"[DB] cache for '{search_keyword}': {len(local_images)} imgs, skipping API", flush=True)
                all_posts_json = build_posts_array(local_images)
                return (all_clip_paths, all_posts_json)
            
            
            print(f"[DB] only {len(local_images)} images in DB for '{search_keyword}', fetching from APIs", flush=True)
            if local_images:
                all_posts_json.extend(build_posts_array(local_images))

    for provider in api_providers:
        clip_paths, posts_json = provider.fetch(search_keyword, num_images, blocked_urls)
        all_clip_paths.extend(clip_paths)
        all_posts_json.extend(posts_json)

    if all_posts_json:
        try:
            save_posts_to_db(all_posts_json)
        except Exception as e:
            logging.error(f"save_posts_to_db failed: {e}")

    return (all_clip_paths, all_posts_json)