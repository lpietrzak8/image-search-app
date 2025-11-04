import os
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image
from backend.app.key_words import getKeyWords
import time
import pickle


class ClipModel:
    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=True)
    
    def compute_image_embeddings(self, image_folder, output_file="clip/embeddings.pkl"):
        embeddings = []
        image_files = []

        for fname in os.listdir(image_folder):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                path = os.path.join(image_folder, fname)
                img = Image.open(path).convert("RGB")

                inputs = self.processor(images=img, return_tensors="pt")
                with torch.no_grad():
                    image_emb = self.model.get_image_features(**inputs)

                image_emb = image_emb / image_emb.norm()
                embeddings.append(image_emb.cpu())
                image_files.append(fname)

        embeddings = torch.vstack(embeddings)

        with open(output_file, "wb") as f:
            pickle.dump((embeddings, image_files), f)


        return embeddings, image_files

    def load_embeddings(self, path="clip/embeddings.pkl"):
        with open(path, "rb") as f:
            image_embeddings, image_files = pickle.load(f)

        return image_embeddings, image_files

    def compute_text_embedding(self, text):
        inputs = self.processor(text=[text], return_tensors="pt")
        with torch.no_grad():
            text_emb = self.model.get_text_features(**inputs)

        return text_emb / text_emb.norm()

