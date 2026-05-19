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

## Testing

The project includes unit tests for the backend, CLIP service, and frontend. All tests can be run without starting the full Docker stack.

---

### Backend — pytest

**Location:** `backend/tests/` | **Coverage: 56%** | **78 tests**

| File                        | What is tested                                                                                                                  |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `test_config.py`            | `get_secret`, `allowed_file`, `verify_recaptcha`, `build_posts_array`                                                           |
| `test_key_words.py`         | `getKeyWords` — RAKE keyword extraction                                                                                         |
| `test_api_providers.py`     | `looks_like_ai`, `saveImage`, `PixabayProvider.fetch`, `PexelsProvider.fetch`, `UnsplashProvider.fetch`, `build_providers_list` |
| `test_search_utils.py`      | `fetch_images_tag` — aggregating results from providers and local DB                                                            |
| `test_searcher.py`          | `Searcher.get_similar_images` — CLIP API call, Redis cache hit/miss                                                             |
| `test_app.py`               | Flask routes: search, posts, image upload, blacklist                                                                            |
| `test_blacklist_service.py` | `get_blocked_urls`                                                                                                              |

```bash
cd backend
pip install -r tests/requirements-test.txt   # once
pytest                                        # run tests
pytest --cov=app tests/ --cov-report=term-missing  # with coverage report
```

---

### CLIP Service — pytest

**Location:** `clip/tests/` | **Coverage: 57%** | **35 tests**

| File                        | What is tested                                                           |
| --------------------------- | ------------------------------------------------------------------------ |
| `test_utils.py`             | `batch`, `get_images`                                                    |
| `test_ranking.py`           | `rank_images`, `print_ranking`                                           |
| `test_clip_db_connector.py` | `init_db`, `save_embedding`, `get_embedding_by_hash`                     |
| `test_cache.py`             | `compute_hash_from_image`, `get_or_create_embedding`                     |
| `test_service.py`           | `load_image` (file / URL / base64), `/similarity` endpoint, `/` endpoint |

```bash
cd clip
pip install -r tests/requirements-test.txt   # once
pytest                                        # run tests
pytest --cov=app tests/ --cov-report=term-missing  # with coverage report
```

> `model.py` and `clip_test.py` are not covered — they require a GPU and the `transformers` library.

---

### Frontend — Vitest + React Testing Library

**Location:** `frontend/src/test/` | **Coverage: 90%** | **98 tests**

| File                      | What is tested                                                      |
| ------------------------- | ------------------------------------------------------------------- |
| `Navbar.test.tsx`         | Logo, nav links, hamburger button, mobile menu toggle               |
| `Post.test.tsx`           | Modal rendering, save photo, suspend flag, close actions            |
| `HomePage.test.tsx`       | Search input, API calls, SSE events, results display                |
| `ContributePage.test.tsx` | Form validation, file upload, reCAPTCHA, success/error states       |
| `MissionPage.test.tsx`    | Static content rendering                                            |
| `LogInPage.test.tsx`      | Login/register buttons, keycloak calls, redirect when authenticated |
| `MyAccountPage.test.tsx`  | Tabs, saved photos, delete photo, account info, logout              |
| `AdminPanel.test.tsx`     | Post moderation, approve/reject/delete, filters, auth guard         |
| `App.test.tsx`            | Keycloak init, loading state, routing to all pages                  |

> `keycloak.ts` and `main.tsx` are excluded from coverage — they are entry-point/config files with no testable logic.

```bash
cd frontend
npm install                    # once
npm test                       # single run
npm run test:watch             # watch mode
npx vitest run --coverage      # run with coverage report
```
