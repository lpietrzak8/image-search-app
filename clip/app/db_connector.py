import sqlite3
import numpy as np
import os

DB_PATH = "/app/cache/embeddings_cache.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS image_embeddings (
            image_hash TEXT PRIMARY KEY,
            embedding BLOB
        )
    """)
    conn.commit()
    conn.close()

def save_embedding(image_hash: str, embedding: list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    emb_array = np.array(embedding, dtype=np.float32)
    c.execute("INSERT OR REPLACE INTO image_embeddings (image_hash, embedding) VALUES (?, ?)",
              (image_hash, emb_array.tobytes()))
    conn.commit()
    conn.close()

def get_embedding_by_hash(image_hash: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT embedding FROM image_embeddings WHERE image_hash = ?", (image_hash,))
    row = c.fetchone()
    conn.close()

    if row is None:
        return None

    emb_bytes = row[0]
    emb_array = np.frombuffer(emb_bytes, dtype=np.float32)
    return emb_array