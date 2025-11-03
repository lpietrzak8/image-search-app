import requests
import os
from io import BytesIO
from transformers import CLIPProcessor, CLIPModel
import torch
import math
from PIL import Image
from key_words import getKeyWords

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=True)

text = "Huge snowy mountains"

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

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


def getImagesRankedBatches(text, model, processor):
    key_words = getKeyWords(text)
    images, names = get_images("resources")

    ranked = []
    batch_size = 100
    x = math.ceil(len(images) / batch_size)

    for i in batch(images, batch_size):
        ranked += getImagesSimilarity(i, key_words, model, processor)
    return images, names, ranked

def getImagesRanked(text, model, processor):
    key_words = getKeyWords(text)
    images, names = get_images("resources")
    return images, names, getImagesSimilarity(images, key_words, model, processor)


def getImagesSimilarity(images, key_words, model, processor):
    
    inputs = processor(text=key_words, images=images, return_tensors="pt", padding=True)

    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    combined = 0
    for idx in range(len(key_words)):
        combined += logits_per_image[:, idx]
    
    return torch.argsort(combined, descending=True)



images, names, ranked = getImagesRankedBatches(text, model, processor)

for rank, idx in enumerate(ranked[:100]):
    print(f"{rank+1}. Image {names[idx]}")
    
# print("Label probabilities:", probs)