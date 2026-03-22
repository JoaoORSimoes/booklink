FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 6000

CMD ["python", "app.py"]
