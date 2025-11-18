FROM python:3.13-slim

WORKDIR /app

COPY ./app .

RUN pip install --no-cache-dir -r requirements.txt setuptools
# RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
# RUN python -m nltk.downloader punkt stopwords
# RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"
RUN [ "python", "-c", "import nltk; nltk.download('punkt'); nltk.download('stopwords')" ]


EXPOSE 5000

CMD ["python3", "app.py"]
