from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Table, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship

db = SQLAlchemy()

post_keywords = Table(
    'post_keywords',
    db.Model.metadata,
    Column('post_id', Integer, ForeignKey('posts.id')),
    Column('keyword_id', Integer, ForeignKey('keywords.id'))
)

class Post(db.Model):
    __tablename__='posts'
    id = Column(Integer, primary_key=True)

    provider = Column(String(64), nullable=False)

    author_name = Column(String(64), nullable=False)
    author_url = Column(String(512), nullable=True)

    description = Column(String(512), nullable=False)

    image_url = Column(String(512), nullable=False)
    source_url = Column(String(512), nullable=False, unique=True)

    created_at = Column(DateTime, server_default=db.func.now())
    
    keywords = relationship("Keyword", secondary=post_keywords, back_populates="posts")

class Keyword(db.Model):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    posts = relationship("Post", secondary=post_keywords, back_populates="keywords")

class BlacklistedImage(db.Model):
    __tablename__='blacklist_images'

    id = Column(Integer, primary_key=True)

    provider = Column(String(32), nullable=False)
    source_url = Column(String(512), nullable=False, unique=True)

    status = Column(
        Enum("suspended", "blocked", name="blacklist_status"),
        nullable=False,
        default="suspended"
    )

    reason = Column(String(225), nullable=True)

    created_at = Column(DateTime, server_default=db.func.now())
    updated_at = Column(
        DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

class UserSavedPhoto(db.Model):
    __tablename__ = 'user_saved_photos'

    id = Column(Integer, primary_key=True)
    
    user_id = Column(String(255), nullable=False)
    
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    post = relationship("Post")
    created_at = Column(DateTime, server_default=db.func.now())