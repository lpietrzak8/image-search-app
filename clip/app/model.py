import os
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image
import time
import pickle
from torchvision.transforms import Resize, CenterCrop, Normalize, ToTensor
from peft import LoraConfig, get_peft_model, PeftModel, PeftConfig


class ClipModel:
    def __init__(self, model_path="openai/clip-vit-base-patch32"):
        # self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        # self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=True)
        # self.model = CLIPModel.from_pretrained(model_path)
        # self.processor = CLIPProcessor.from_pretrained(model_path, use_fast=True)

        is_lora = os.path.isfile(os.path.join(model_path, "adapter_config.json"))

        if is_lora:
            print(">> Loading LoRA adapter:", model_path)

            config = PeftConfig.from_pretrained(model_path)

            base_model_name = config.base_model_name_or_path
            print(">> Base CLIP model:", base_model_name)

            self.model = CLIPModel.from_pretrained(base_model_name)

            self.model = PeftModel.from_pretrained(self.model, model_path)

            self.model = self.model.merge_and_unload()

            self.processor = CLIPProcessor.from_pretrained(base_model_name)
        else:
            print(">> Loading base CLIP model:", model_path)
            self.model = CLIPModel.from_pretrained(model_path)
            self.processor = CLIPProcessor.from_pretrained(model_path, use_fast=True)

    
    # def get_image_embedding(self, image):
    #     device = next(self.model.parameters()).device
    #     with torch.no_grad():
    #         print("yeah im doing it")
    #         if hasattr(self.model, "get_image_features"):
    #             print("kill yourself gpt if")
    #             inputs = self.processor(images=image, return_tensors="pt")
    #             emb = self.model.get_image_features(**inputs)
    #         else:
    #             transform = torch.nn.Sequential(
    #             Resize(224),
    #             CenterCrop(224)
    #             )

    #             img_tensor = ToTensor()(image)

    #             img_tensor = transform(img_tensor)

    #             img_tensor = Normalize(
    #                 mean=self.processor.image_processor.image_mean,
    #                 std=self.processor.image_processor.image_std
    #             )(img_tensor)

    #             pixel_values = img_tensor.unsqueeze(0).to(device)
    #             emb = self.model.vision_model(pixel_values).pooler_output

    #     emb = emb / emb.norm(dim=-1, keepdim=True)
    #     return emb
    
    def get_image_embedding(self, image):
        device = next(self.model.parameters()).device
        inputs = self.processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            emb = self.model.get_image_features(**inputs)
        return emb / emb.norm(dim=-1, keepdim=True)
    

    def compute_image_embeddings(self, image_folder, output_file="clip/embeddings.pkl"):
        embeddings = []
        image_files = []

        for fname in os.listdir(image_folder):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                path = os.path.join(image_folder, fname)
                img = Image.open(path).convert("RGB")

                # inputs = self.processor(images=img, return_tensors="pt")
                # with torch.no_grad():
                #     image_emb = self.model.get_image_features(**inputs)

                # image_emb = image_emb / image_emb.norm()

                image_emb = self.get_image_embedding(img)
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

