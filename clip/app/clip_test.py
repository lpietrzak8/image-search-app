import requests
import os
from io import BytesIO
from transformers import CLIPProcessor, CLIPModel
import torch
import math
from PIL import Image
from backend.app.key_words import getKeyWords

import time
import pickle
from model import ClipModel
import ranking
start_time = time.time()

clipModel = ClipModel()


if not os.path.isfile("clip/embeddings.pkl"):
   clipModel.compute_image_embeddings("resources")


image_embeddings, image_files = clipModel.load_embeddings("clip/embeddings.pkl")

results = ranking.rank_images(clipModel, "city", image_embeddings, image_files)

ranking.print_ranking(results, 10)
    
# print("--- %s seconds ---" % (time.time() - start_time))