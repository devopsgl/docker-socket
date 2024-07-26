# Python 3.9 tabanlı bir image kullan
FROM python:3.12

# Çalışma dizinini belirle
WORKDIR /app

# Gerekli dosyaları container'a kopyala
COPY requirements.txt requirements.txt
COPY app.py app.py

# Bağımlılıkları yükle
RUN pip install -r requirements.txt

# Flask uygulamasını başlat
CMD ["python", "app.py"]
