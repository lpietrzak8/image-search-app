import requests
import os
from io import BytesIO
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image

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

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


images, names = get_images("../resources")
inputs = processor(text=["dog", "black"], images=images, return_tensors="pt", padding=True)

outputs = model(**inputs)
logits_per_image = outputs.logits_per_image
probs = logits_per_image
combined = 0.8*probs[:, 0] + 0.2*probs[:, 1]

ranked = torch.argsort(combined, descending=True)

for rank, idx in enumerate(ranked):
    print(f"{rank+1}. Image {names[idx]} Score: {combined[idx]:.3f}")
    
# print("Label probabilities:", probs)