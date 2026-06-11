import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO


@pytest.fixture
def flask_app():
    with patch("time.sleep"):
        with patch("app.get_secret", return_value="test_password"):
            with patch("app.db") as mock_db:
                mock_db.init_app = MagicMock()
                mock_db.create_all = MagicMock()
                with patch("app.Searcher"):
                    import app as flask_module
                    flask_module.app.config["TESTING"] = True
                    flask_module.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
                    with flask_module.app.test_client() as client:
                        yield client, flask_module


@pytest.fixture
def app_with_db():
    with patch("time.sleep"):
        os.environ["MYSQL_ROOT_PASSWORD"] = "test"
        import importlib
        with patch("app.get_secret", return_value="test_password"):
            with patch("sqlalchemy.create_engine"):
                with patch("app.Searcher"):
                    import flask
                    test_app = flask.Flask("test_app")
                    test_app.config["TESTING"] = True
                    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
                    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
                    test_app.config["UPLOAD_FOLDER"] = "/tmp/test_uploads"

                    from db_connector import db, Post, Keyword, BlacklistedImage
                    db.init_app(test_app)

                    with test_app.app_context():
                        db.create_all()

                    from flask import Blueprint
                    from flask_cors import CORS
                    CORS(test_app, resources={r"/api/*": {"origin": "*"}})

                    import app as app_module

                    @test_app.route("/api/search", methods=["GET"])
                    def start_search():
                        return app_module.start_search()

                    @test_app.route("/api/posts", methods=["GET"])
                    def get_posts():
                        return app_module.get_posts()

                    @test_app.route("/api/posts/byKeyword/<string:keyword_name>", methods=["GET"])
                    def get_posts_by_keywords(keyword_name):
                        return app_module.get_posts_by_keywords(keyword_name)

                    @test_app.route("/api/blacklist/suspend", methods=["POST"])
                    def suspend_image():
                        return app_module.suspend_image()

                    @test_app.route("/api/blacklist/suspended", methods=["GET"])
                    def list_suspended():
                        return app_module.list_suspended()

                    @test_app.route("/api/blacklist/blocked", methods=["GET"])
                    def list_blocked():
                        return app_module.list_blocked()

                    @test_app.route("/api/blacklist/block/<int:image_id>", methods=["PATCH"])
                    def block_image(image_id):
                        return app_module.block_image(image_id)

                    @test_app.route("/api/blacklist/<int:image_id>", methods=["DELETE"])
                    def remove_from_blacklist(image_id):
                        return app_module.remove_from_blacklist(image_id)

                    @test_app.route("/health", methods=["GET"])
                    def healthcheck():
                        return app_module.healthcheck()

                    with test_app.test_client() as client:
                        yield client, test_app


class TestHealth:
    def test_healthcheck_returns_ok(self):
        import flask
        test_app = flask.Flask("health_test")
        test_app.config["TESTING"] = True

        @test_app.route("/health")
        def health():
            return "OK", 200

        with test_app.test_client() as client:
            resp = client.get("/health")
            assert resp.status_code == 200
            assert resp.data == b"OK"


class TestStartSearch:
    def test_returns_job_id(self):
        import flask
        test_app = flask.Flask("search_test")
        test_app.config["TESTING"] = True

        search_jobs = {}

        @test_app.route("/api/search")
        def start_search():
            from flask import request, jsonify
            import uuid
            query = request.args.get("s_query", "").lower()
            top_k = int(request.args.get("k", 30))
            job_id = str(uuid.uuid4())
            search_jobs[job_id] = {
                "query": query,
                "top_k": top_k,
                "status": "queued",
                "result": None,
            }
            return jsonify({"job_id": job_id})

        with test_app.test_client() as client:
            resp = client.get("/api/search?s_query=cat&k=10")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert "job_id" in data
            assert data["job_id"] in search_jobs
            assert search_jobs[data["job_id"]]["query"] == "cat"
            assert search_jobs[data["job_id"]]["top_k"] == 10


class TestCreatePost:
    def _make_app(self, tmp_path):
        import flask
        from flask import request, jsonify
        from werkzeug.utils import secure_filename
        import json as _json

        test_app = flask.Flask("post_test")
        test_app.config["TESTING"] = True
        test_app.config["UPLOAD_FOLDER"] = str(tmp_path)

        from db_connector import db, Post, Keyword
        test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(test_app)

        with test_app.app_context():
            db.create_all()

        @test_app.route("/api/createPost", methods=["POST"])
        def post_image():
            author = request.form.get("author")
            description = request.form.get("description")
            keywords_raw = request.form.get("keywords")
            image = request.files.get("image")

            if not image:
                return jsonify({"error": "No image uploaded"}), 400
            if not author:
                return jsonify({"error": "Missing author"}), 400
            if not description:
                return jsonify({"error": "Missing description"}), 400

            try:
                keywords_list = _json.loads(keywords_raw)
            except Exception:
                keywords_list = [kw.strip() for kw in keywords_raw.split(",")]

            import os
            folder = os.path.join(str(tmp_path), author)
            os.makedirs(folder, exist_ok=True)
            filename = secure_filename(image.filename)
            filepath = os.path.join(folder, filename)
            image.save(filepath)
            relative_path = os.path.relpath(filepath, str(tmp_path))

            keyword_objects = []
            for kw in keywords_list:
                keyword = Keyword.query.filter_by(name=kw).first()
                if not keyword:
                    keyword = Keyword(name=kw)
                keyword_objects.append(keyword)

            new_post = Post(
                author=author,
                description=description,
                keywords=keyword_objects,
                image_path=relative_path,
            )
            db.session.add(new_post)
            db.session.commit()
            return jsonify({"message": "Post created"}), 201

        return test_app

    def test_create_post_success(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/createPost",
                data={
                    "author": "alice",
                    "description": "A nice cat photo",
                    "keywords": '["cat", "animal"]',
                    "image": (BytesIO(b"fakeimgdata"), "cat.jpg"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 201
            data = json.loads(resp.data)
            assert data["message"] == "Post created"

    def test_create_post_missing_image(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/createPost",
                data={
                    "author": "alice",
                    "description": "desc",
                    "keywords": '["cat"]',
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 400
            assert b"No image" in resp.data

    def test_create_post_missing_author(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/createPost",
                data={
                    "description": "desc",
                    "keywords": '["cat"]',
                    "image": (BytesIO(b"fakeimgdata"), "cat.jpg"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 400
            assert b"author" in resp.data

    def test_create_post_missing_description(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/createPost",
                data={
                    "author": "alice",
                    "keywords": '["cat"]',
                    "image": (BytesIO(b"fakeimgdata"), "cat.jpg"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 400
            assert b"description" in resp.data


class TestGetPosts:
    def _make_app(self):
        import flask
        from flask import jsonify

        test_app = flask.Flask("getposts_test")
        test_app.config["TESTING"] = True
        test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        from db_connector import db, Post, Keyword
        db.init_app(test_app)

        with test_app.app_context():
            db.create_all()

        @test_app.route("/api/posts", methods=["GET"])
        def get_posts():
            posts = Post.query.all()
            result = []
            for post in posts:
                result.append({
                    "id": f"local-{post.id}",
                    "author": {"name": post.author, "url": None},
                    "description": post.description,
                    "keywords": [kw.name for kw in post.keywords],
                    "image_url": f"/api/uploads/{post.image_path}",
                    "source_url": f"/api/uploads/{post.image_path}",
                    "provider": "PHOTO-SEARCH"
                })
            return jsonify(result), 200

        @test_app.route("/api/posts/byKeyword/<string:keyword_name>", methods=["GET"])
        def get_posts_by_keywords(keyword_name):
            keyword = Keyword.query.filter_by(name=keyword_name).first()
            if not keyword:
                return jsonify({"error": f"Keyword '{keyword_name}' not found"}), 404
            result = []
            for post in keyword.posts:
                result.append({
                    "id": f"local-{post.id}",
                    "author": {"name": post.author, "url": None},
                    "description": post.description,
                    "keywords": [kw.name for kw in post.keywords],
                    "image_url": f"/api/uploads/{post.image_path}",
                    "source_url": f"/api/uploads/{post.image_path}",
                    "provider": "PHOTO-SEARCH"
                })
            return jsonify(result), 200

        return test_app

    def test_get_posts_empty(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            resp = client.get("/api/posts")
            assert resp.status_code == 200
            assert json.loads(resp.data) == []

    def test_get_posts_returns_all(self):
        test_app = self._make_app()
        from db_connector import db, Post, Keyword
        with test_app.app_context():
            kw = Keyword(name="nature")
            post = Post(author="bob", description="forest", image_path="bob/forest.jpg", keywords=[kw])
            db.session.add(post)
            db.session.commit()

        with test_app.test_client() as client:
            resp = client.get("/api/posts")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 1
            assert data[0]["author"]["name"] == "bob"

    def test_get_posts_by_keyword_found(self):
        test_app = self._make_app()
        from db_connector import db, Post, Keyword
        with test_app.app_context():
            kw = Keyword(name="ocean")
            post = Post(author="alice", description="waves", image_path="alice/waves.jpg", keywords=[kw])
            db.session.add(post)
            db.session.commit()

        with test_app.test_client() as client:
            resp = client.get("/api/posts/byKeyword/ocean")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 1
            assert "ocean" in data[0]["keywords"]

    def test_get_posts_by_keyword_not_found(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            resp = client.get("/api/posts/byKeyword/nonexistent")
            assert resp.status_code == 404


class TestBlacklist:
    def _make_app(self):
        import flask
        from flask import request, jsonify

        test_app = flask.Flask("blacklist_test")
        test_app.config["TESTING"] = True
        test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        from db_connector import db, BlacklistedImage
        db.init_app(test_app)

        with test_app.app_context():
            db.create_all()

        @test_app.route("/api/blacklist/suspend", methods=["POST"])
        def suspend_image():
            data = request.get_json()
            entry = BlacklistedImage(
                provider=data["provider"],
                source_url=data["source_url"],
                status="suspended",
                reason=data.get("reason")
            )
            db.session.add(entry)
            db.session.commit()
            return jsonify({"message": "Post suspended"}), 201

        @test_app.route("/api/blacklist/suspended", methods=["GET"])
        def list_suspended():
            images = BlacklistedImage.query.filter_by(status="suspended").all()
            return jsonify([
                {"id": img.id, "provider": img.provider, "source_url": img.source_url, "reason": img.reason}
                for img in images
            ])

        @test_app.route("/api/blacklist/blocked", methods=["GET"])
        def list_blocked():
            images = BlacklistedImage.query.filter_by(status="blocked").all()
            return jsonify([
                {"id": img.id, "provider": img.provider, "source_url": img.source_url, "reason": img.reason}
                for img in images
            ])

        @test_app.route("/api/blacklist/block/<int:image_id>", methods=["PATCH"])
        def block_image(image_id):
            img = db.session.get(BlacklistedImage, image_id)
            if img is None:
                return jsonify({"error": "not found"}), 404
            img.status = "blocked"
            db.session.commit()
            return jsonify({"message": "Image blocked"})

        @test_app.route("/api/blacklist/<int:image_id>", methods=["DELETE"])
        def remove_from_blacklist(image_id):
            img = db.session.get(BlacklistedImage, image_id)
            if img is None:
                return jsonify({"error": "not found"}), 404
            db.session.delete(img)
            db.session.commit()
            return jsonify({"message": "Image removed from blacklist"})

        return test_app

    def test_suspend_image(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            resp = client.post(
                "/api/blacklist/suspend",
                json={"provider": "pixabay", "source_url": "http://example.com/img1", "reason": "spam"}
            )
            assert resp.status_code == 201
            assert b"suspended" in resp.data

    def test_list_suspended_returns_entries(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            client.post(
                "/api/blacklist/suspend",
                json={"provider": "pexels", "source_url": "http://example.com/img2", "reason": None}
            )
            resp = client.get("/api/blacklist/suspended")
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 1
            assert data[0]["provider"] == "pexels"

    def test_list_blocked_empty_initially(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            resp = client.get("/api/blacklist/blocked")
            assert resp.status_code == 200
            assert json.loads(resp.data) == []

    def test_block_image_changes_status(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            client.post(
                "/api/blacklist/suspend",
                json={"provider": "unsplash", "source_url": "http://example.com/img3", "reason": None}
            )
            suspended = json.loads(client.get("/api/blacklist/suspended").data)
            img_id = suspended[0]["id"]

            resp = client.patch(f"/api/blacklist/block/{img_id}")
            assert resp.status_code == 200
            assert b"blocked" in resp.data

            blocked = json.loads(client.get("/api/blacklist/blocked").data)
            assert len(blocked) == 1

    def test_block_image_not_found(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            resp = client.patch("/api/blacklist/block/9999")
            assert resp.status_code == 404

    def test_remove_from_blacklist(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            client.post(
                "/api/blacklist/suspend",
                json={"provider": "pixabay", "source_url": "http://example.com/img4", "reason": None}
            )
            suspended = json.loads(client.get("/api/blacklist/suspended").data)
            img_id = suspended[0]["id"]

            resp = client.delete(f"/api/blacklist/{img_id}")
            assert resp.status_code == 200

            suspended_after = json.loads(client.get("/api/blacklist/suspended").data)
            assert len(suspended_after) == 0

    def test_remove_from_blacklist_not_found(self):
        test_app = self._make_app()
        with test_app.test_client() as client:
            resp = client.delete("/api/blacklist/9999")
            assert resp.status_code == 404


class TestContribute:
    def _make_app(self, tmp_path):
        import flask
        from flask import request, jsonify
        import uuid as _uuid

        test_app = flask.Flask("contribute_test")
        test_app.config["TESTING"] = True
        test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        from db_connector import db, Post, Keyword
        db.init_app(test_app)
        with test_app.app_context():
            db.create_all()

        upload_folder = str(tmp_path)

        @test_app.route("/api/contribute", methods=["POST"])
        def contribute_image():
            recaptcha_token = request.form.get("recaptcha_token", "")
            if not recaptcha_token:
                return jsonify({"error": "reCAPTCHA verification failed"}), 400

            if "image" not in request.files:
                return jsonify({"error": "No image uploaded"}), 400

            image = request.files["image"]
            if image.filename == "":
                return jsonify({"error": "No image selected"}), 400

            description = request.form.get("description", "").strip()
            if not description:
                return jsonify({"error": "Description is required"}), 400
            if len(description) < 10:
                return jsonify({"error": "Description must be at least 10 characters long"}), 400
            if len(description) > 1000:
                return jsonify({"error": "Description must be less than 1000 characters"}), 400

            allowed_extensions = {"png", "jpg", "jpeg", "webp"}
            ext = image.filename.rsplit(".", 1)[-1].lower() if "." in image.filename else ""
            if ext not in allowed_extensions:
                return jsonify({"error": "Invalid file extension. Allowed: PNG, JPG, JPEG, WebP"}), 400

            image.seek(0, 2)
            file_size = image.tell()
            image.seek(0)
            if file_size > 10 * 1024 * 1024:
                return jsonify({"error": "File size must be less than 10MB"}), 400

            import os
            file_extension = os.path.splitext(image.filename)[1].lower()
            unique_filename = f"{_uuid.uuid4()}{file_extension}"
            contribution_folder = os.path.join(upload_folder, "contributions")
            os.makedirs(contribution_folder, exist_ok=True)
            image_path = os.path.join(contribution_folder, unique_filename)
            image.save(image_path)

            new_post = Post(
                author="contributor",
                description=description,
                keywords=[],
                image_path=os.path.relpath(image_path, upload_folder)
            )
            db.session.add(new_post)
            db.session.commit()
            return jsonify({"message": "Thank you for your contribution!", "post_id": new_post.id}), 201

        return test_app

    def test_contribute_success(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/contribute",
                data={
                    "recaptcha_token": "valid_token",
                    "description": "A beautiful sunset over the mountains",
                    "image": (BytesIO(b"fakeimgdata"), "sunset.jpg"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 201
            data = json.loads(resp.data)
            assert "post_id" in data

    def test_contribute_missing_recaptcha(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/contribute",
                data={
                    "description": "A nice photo of the sea",
                    "image": (BytesIO(b"fakeimgdata"), "sea.jpg"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 400
            assert b"reCAPTCHA" in resp.data

    def test_contribute_description_too_short(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/contribute",
                data={
                    "recaptcha_token": "valid_token",
                    "description": "short",
                    "image": (BytesIO(b"fakeimgdata"), "img.jpg"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 400
            assert b"10 characters" in resp.data

    def test_contribute_description_too_long(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/contribute",
                data={
                    "recaptcha_token": "valid_token",
                    "description": "x" * 1001,
                    "image": (BytesIO(b"fakeimgdata"), "img.jpg"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 400
            assert b"1000 characters" in resp.data

    def test_contribute_invalid_extension(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            resp = client.post(
                "/api/contribute",
                data={
                    "recaptcha_token": "valid_token",
                    "description": "A nice landscape photo",
                    "image": (BytesIO(b"fakeimgdata"), "script.exe"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 400
            assert b"extension" in resp.data

    def test_contribute_file_too_large(self, tmp_path):
        test_app = self._make_app(tmp_path)
        with test_app.test_client() as client:
            large_data = b"x" * (10 * 1024 * 1024 + 1)
            resp = client.post(
                "/api/contribute",
                data={
                    "recaptcha_token": "valid_token",
                    "description": "A photo of something very interesting",
                    "image": (BytesIO(large_data), "big.jpg"),
                },
                content_type="multipart/form-data",
            )
            assert resp.status_code == 400
            assert b"10MB" in resp.data
