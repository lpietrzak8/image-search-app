FROM python:3.13-slim

WORKDIR /app

COPY ./app .

RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "4000", "--reload"]