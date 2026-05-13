import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
import torch
from unittest.mock import MagicMock


def _make_model_with_text_emb(text_emb_tensor):
    model = MagicMock()
    model.compute_text_embedding.return_value = text_emb_tensor
    return model


def test_rank_images_returns_sorted_by_score():
    from ranking import rank_images

    text_emb = torch.tensor([[1.0, 0.0]])
    image_embeddings = torch.tensor([
        [0.0, 1.0],
        [1.0, 0.0],
        [0.707, 0.707],
    ])
    image_files = ["low.jpg", "high.jpg", "mid.jpg"]

    model = _make_model_with_text_emb(text_emb)
    result = rank_images(model, "query", image_embeddings, image_files)

    assert result[0][0] == "high.jpg"
    filenames = [r[0] for r in result]
    assert filenames.index("high.jpg") < filenames.index("mid.jpg")
    assert filenames.index("mid.jpg") < filenames.index("low.jpg")


def test_rank_images_scores_are_floats():
    from ranking import rank_images

    text_emb = torch.tensor([[1.0, 0.0]])
    image_embeddings = torch.tensor([[0.5, 0.5], [1.0, 0.0]])
    image_files = ["a.jpg", "b.jpg"]

    model = _make_model_with_text_emb(text_emb)
    result = rank_images(model, "query", image_embeddings, image_files)

    for _, score in result:
        assert isinstance(score, float)


def test_rank_images_single_image():
    from ranking import rank_images

    text_emb = torch.tensor([[1.0, 0.0]])
    image_embeddings = torch.tensor([[1.0, 0.0]])
    image_files = ["only.jpg"]

    model = _make_model_with_text_emb(text_emb)
    result = rank_images(model, "query", image_embeddings, image_files)

    assert len(result) == 1
    assert result[0][0] == "only.jpg"
    assert abs(result[0][1] - 1.0) < 1e-5


def test_rank_images_length_matches_input():
    from ranking import rank_images

    text_emb = torch.tensor([[1.0, 0.0]])
    image_embeddings = torch.rand(5, 2)
    image_files = [f"img{i}.jpg" for i in range(5)]

    model = _make_model_with_text_emb(text_emb)
    result = rank_images(model, "query", image_embeddings, image_files)

    assert len(result) == 5


def test_print_ranking_prints_correct_count(capsys):
    from ranking import print_ranking

    ranking = [("a.jpg", 0.9), ("b.jpg", 0.7), ("c.jpg", 0.5)]
    print_ranking(ranking, 2)

    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split("\n") if l]
    assert len(lines) == 2


def test_print_ranking_prints_all_when_size_equals_len(capsys):
    from ranking import print_ranking

    ranking = [("x.jpg", 0.8), ("y.jpg", 0.6)]
    print_ranking(ranking, 2)

    captured = capsys.readouterr()
    assert "x.jpg" in captured.out
    assert "y.jpg" in captured.out
