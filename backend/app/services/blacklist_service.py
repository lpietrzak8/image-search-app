from db_connector import db
from db_connector import BlacklistedImage

def get_blocked_urls():
    return {
            b.source_url
            for b in db.session.query(BlacklistedImage.source_url)
            .filter_by(status="blocked")
            .all()
    }