# Image Search

Semantic image search using CLIP embeddings.

## Developed by

- Franciszek Frycz
- Łukasz Pietrzak
- Emilia Wójcik

## Our Mission

In a world increasingly shaped by artificial intelligence, we believe that true creativity still begins with real people.

Our mission is to connect technology with genuine human artistry — making it easier than ever to find authentic, high-quality photographs created by talented photographers around the world.

We celebrate the craft, emotion, and perspective that only real artists can capture.

By combining intelligent search tools with a curated database of human-made photography, we aim to honor and support the photographers who bring meaning, beauty, and authenticity to visual storytelling.

Because while AI can generate images, only humans can create art.

## Architecture

Frontend (React + Vite)
↓
Nginx (reverse proxy)
↓
Flask API (backend)
↓
CLIP Service (embeddings + similarity)

## Features

- Semantic image search
- Adding photos protected by reCAPTCHA v3
- Embedding generation and catching
- CLIP model training script
- Multi-provider image featching
- Live progress updates via Server-Sent Events
- Reverse proxy via Nginx
- Dockerized enviroment
- AI generated images filtering
- Blacklisting system
- Last searched photos catching with redis

## Technologies

- Docker
- Docker Compose
- Python 3.13
- React 18
- Vite 4.4.5
- Mysql 8
- Redis
- CLIP
