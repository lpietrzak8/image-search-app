from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import torch
from PIL import Image
import os
import io
import base64
import requests
from model import ClipModel
import logging
from ranking import rank_images
from cache import get_or_create_embedding
from db_connector import init_db
import time
from cache import compute_hash_from_image
from db_connector import get_embedding_by_hash, save_embedding


os.makedirs("/app/cache", exist_ok=True)
init_db()
print("Embedding cache initialized..")

app = FastAPI()



clip_model = ClipModel()
logging.info("CLIP model loaded successfully.")

class SimilarityRequest(BaseModel):
    images: List[str]
    query: str
    top_k: int = 5

class SimilarityResponse(BaseModel):
    indices: List[int]
    scores: List[float]

def load_image(image_source:str):
    if os.path.exists(image_source):
        return Image.open(image_source).convert("RGB")
    
    if image_source.startswith("http"):
        try:
            response = requests.get(image_source, timeout=10)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Error occured during download of image from URL {image_source}: {e}")
    
    try:
        image_bytes = base64.b64decode(image_source)
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise ValueError(f"False image data: {e}")
        
@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/similarity", response_model=SimilarityResponse)
async def compute_similarity(req: SimilarityRequest):
    try:
        images = [load_image(img) for img in req.images]
        if not images:
            return SimilarityResponse(indices=[], scores=[])

        text_emb = clip_model.compute_text_embedding(req.query)
        text_emb = text_emb / text_emb.norm()

        
        embeddings = [None] * len(images)
        miss_indices = []
        miss_images = []

        for i, img in enumerate(images):
            img_hash = compute_hash_from_image(img)
            cached = get_embedding_by_hash(img_hash)
            if cached is not None:
                t = torch.tensor(cached, dtype=torch.float32)
                if t.ndim == 1:
                    t = t.unsqueeze(0)
                embeddings[i] = t
            else:
                miss_indices.append((i, img_hash))
                miss_images.append(img)

        
        if miss_images:
            inputs = clip_model.processor(images=miss_images, return_tensors="pt")
            with torch.no_grad():
                batch_embs = clip_model.model.get_image_features(**inputs)
            batch_embs = batch_embs / batch_embs.norm(dim=-1, keepdim=True)

            for j, (i, img_hash) in enumerate(miss_indices):
                emb = batch_embs[j].unsqueeze(0)
                save_embedding(img_hash, emb.squeeze(0).tolist())
                embeddings[i] = emb

        img_embs = torch.cat(embeddings)
        similarities = (img_embs @ text_emb.T).squeeze(1)
        scores = similarities.tolist()
        k = min(req.top_k, similarities.shape[0])
        top_indices = torch.topk(similarities, k).indices.tolist()
        top_scores = [scores[i] for i in top_indices]

        return SimilarityResponse(indices=top_indices, scores=top_scores)
    except Exception as e:
        logging.exception("Error during similarity computation")
        raise HTTPException(status_code=500, detail=str(e))