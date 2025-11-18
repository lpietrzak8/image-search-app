import hashlib
import torch
from io import BytesIO
from PIL import Image
import base64
import os
import io
from db_connector import get_embedding_by_hash, save_embedding
from model import ClipModel

def compute_hash_from_image(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return hashlib.sha256(buf.getvalue()).hexdigest()

def get_or_create_embedding(image: Image.Image, clip_model):
    img_hash = compute_hash_from_image(image)
    cached = get_embedding_by_hash(img_hash)
    if cached is not None:
        return torch.tensor(cached)

    inputs = clip_model.processor(images=image, return_tensors="pt")
    with torch.no_grad():
        emb = clip_model.model.get_image_features(**inputs)
    
    emb = emb / emb.norm(dim=-1, keepdim=True)
    save_embedding(img_hash, emb.tolist())
    return emb