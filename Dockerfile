FROM python:3.14-slim

# Instalar dependências do Chrome e Chromium
RUN apt-get update && apt-get install -y \
    chromium-browser \
    chromium-driver \
    curl \
    gnupg \
    unzip \
    wget \
    xvfb \
    libx11-6 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libnss3 \
    libgconf-2-4 \
    libappindicator1 \
    libindicator7 \
    libgbm1 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 4000

# Comando para iniciar a aplicação
CMD ["python", "app.py"]
