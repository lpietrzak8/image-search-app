import requests
import os
from io import BytesIO
from transformers import CLIPProcessor, CLIPModel
import torch
import math
from PIL import Image
import matplotlib.pyplot as plt


import time
import pickle
from model import ClipModel
import ranking
from datasets import load_dataset


dataset = load_dataset("arampacha/rsicd")
train_subset = dataset['train']
eval_subset = dataset['valid']
start_time = time.time()
# "/Volumes/SANDISK/clip-arampacha-finetuned"
clipModel = ClipModel("app/clip-lora-output")


print(f"clip model loaded in")
if not os.path.isfile("embeddings_subset2.pkl"):
    embeddings = []
    files = []

    for i in range(len(eval_subset)):
        print(f"im doing {i}")
        item = eval_subset[i]
        pil_image = item['image'].convert("RGB")
        emb = clipModel.get_image_embedding(pil_image)
        embeddings.append(emb.cpu())
        files.append(f"rsicd_{i}.jpg")

    embeddings = torch.vstack(embeddings)
    with open("embeddings_subset2.pkl", "wb") as f:
        pickle.dump((embeddings, files), f)



image_embeddings, image_files = clipModel.load_embeddings("embeddings_subset2.pkl")

query="tall buildings"
results = ranking.rank_images(clipModel, query, image_embeddings, image_files)

ranking.print_ranking(results, 10)



dataset = load_dataset("arampacha/rsicd")
train_subset = dataset['train']


top_results = results[:10]

plt.figure(figsize=(15, 5), num=query)
for i, (fname, score) in enumerate(top_results):
   
    idx = int(fname.split('_')[1].split('.')[0])
    img = eval_subset[idx]['image'].convert("RGB")

    ax = plt.subplot(2, 5, i + 1)
    plt.imshow(img)
    plt.title(f"{fname}\n{score:.2f}")
    plt.axis("off")

plt.tight_layout()
plt.show()
    
# print("--- %s seconds ---" % (time.time() - start_time))