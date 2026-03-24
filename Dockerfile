FROM python:3.11-slim

# Instala Chromium e todas as dependências necessárias
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    chromium \
    chromium-driver \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libxss1 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    fonts-liberation \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Cria symlink para que o código que procura "google-chrome" encontre o Chromium
RUN ln -sf /usr/bin/chromium /usr/bin/google-chrome || true

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
