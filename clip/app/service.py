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

        text_emb = clip_model.compute_text_embedding(req.query)
        # start = time.time()
        img_embs = torch.cat([get_or_create_embedding(img, clip_model) for img in images])
        # print("Cache hit:", time.time() - start)
        
        img_embs = img_embs / img_embs.norm(dim=-1, keepdim=True)
        text_emb = text_emb / text_emb.norm()

        similarities = (img_embs @ text_emb.T).squeeze(1)
        scores = similarities.tolist()

        top_k = min(req.top_k, len(scores))
        top_indices = torch.topk(similarities, top_k).indices.tolist()
        top_scores = [scores[i] for i in top_indices]

        return SimilarityResponse(indices=top_indices, scores=top_scores)

    except Exception as e:
        logging.exception("Error during similarity computation")
        raise HTTPException(status_code=500, detail=str(e))