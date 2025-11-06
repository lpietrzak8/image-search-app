import os
from PIL import Image

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