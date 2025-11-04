def rank_images(model, query, image_embeddings, image_files):
    text_emb = model.compute_text_embedding(query)

    sims = (image_embeddings @ text_emb.T).squeeze()
    top_idx = sims.argsort(descending=True)

    return [(image_files[i], float(sims[i])) for i in top_idx]

def print_ranking(ranking, size):
    for img, score in ranking[:size]:
        print(score, img)
    