import hashlib
import torch
from io import BytesIO
from PIL import Image
import base64
import os
import io
from db_connector import get_embedding_by_hash, save_embedding
from model import ClipModel
import numpy as np
import time
import logging
from contextlib import contextmanager

@contextmanager
def timer(label):
    start = time.perf_counter()
    yield
    elapsed = (time.perf_counter() - start) * 1000
    logging.warning(f"[TIMER] {label}: {elapsed:.2f}ms")


def compute_hash_from_image(image: Image.Image) -> str:
    arr = np.asarray(image, dtype=np.uint8)
    return hashlib.sha256(arr.tobytes()).hexdigest()

def get_or_create_embedding(image: Image.Image, clip_model):
   
    with timer("compute_hash"):
        img_hash = compute_hash_from_image(image)
    with timer("db lookup"):
        cached = get_embedding_by_hash(img_hash)
    if cached is not None:
        logging.warning("[TIMER] cache HIT")
        t = torch.tensor(cached, dtype=torch.float32)
        if t.ndim == 1:
            t = t.unsqueeze(0)
        return t

    logging.warning("[TIMER] cache MISS — running inference")
    with timer("clip inference"):
        inputs = clip_model.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            emb = clip_model.model.get_image_features(**inputs)
        emb = emb / emb.norm(dim=-1, keepdim=True)

    with timer("save_embedding"):
        save_embedding(img_hash, emb.squeeze(0).tolist())
        
    return emb