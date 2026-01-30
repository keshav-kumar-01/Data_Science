FROM python:3.8-alpine

WORKDIR /app

COPY app/ /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD python app.py
