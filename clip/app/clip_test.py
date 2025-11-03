import requests
import os
from io import BytesIO
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image
from key_words import getKeyWords

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=True)

text = "big black dog looking at the camera"

def get_images(folder_path):
    images = []
    names = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(folder_path, filename)
            img = Image.open(path).convert("RGB")
            images.append(img)
            names.append(filename)
    return images, names


def getImagesSimilarity(text, model, processor):
    key_words = getKeyWords(text)
    images, names = get_images("resources")
    inputs = processor(text=key_words, images=images, return_tensors="pt", padding=True)

    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    combined = 0
    for idx in range(len(key_words)):
        combined += logits_per_image[:, idx]
    
    return images, names, torch.argsort(combined, descending=True)



images, names, ranked = getImagesSimilarity(text, model, processor)

for rank, idx in enumerate(ranked):
    print(f"{rank+1}. Image {names[idx]}")
    
# print("Label probabilities:", probs)