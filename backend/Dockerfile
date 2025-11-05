FROM python:3.13-slim

WORKDIR /app

COPY ./app .

RUN pip install --no-cache-dir -r requirements.txt setuptools
RUN python -m nltk.downloader punkt stopwords

EXPOSE 5000

CMD ["python3", "app.py"]
