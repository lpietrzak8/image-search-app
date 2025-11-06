from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Table, ForeignKey
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
    author = Column(String(64), nullable=False)
    keywords = relationship("Keyword", secondary=post_keywords, back_populates="posts")
    description = Column(String(512), nullable=False)
    image_path = Column(String(512), nullable=False)

class Keyword(db.Model):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    posts = relationship("Post", secondary=post_keywords, back_populates="keywords")