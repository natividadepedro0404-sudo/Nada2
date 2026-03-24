FROM debian:12

# Instalar Python, pip e build essentials (necessários para compilar pacotes Python)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    curl \
    wget \
    gnupg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip, setuptools e wheel
RUN pip3 install --upgrade pip setuptools wheel

# Instalar Chromium (não chromium-browser, apenas chromium)
RUN apt-get update && apt-get install -y \
    chromium \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libicu72 \
    libjpeg62-turbo \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpng16-16 \
    libpulse0 \
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
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt e instalar dependências Python
COPY requirements.txt .
RUN echo "=== Instalando dependências Python ===" && \
    pip3 install --no-cache-dir -r requirements.txt && \
    echo "=== Dependências instaladas com sucesso ===" || \
    (echo "=== Erro ao instalar dependências ===" && exit 1)

# Copiar código da aplicação
COPY . .

# Definir permissões
RUN chmod +x /app/app.py

# Expor porta
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:4000/ || exit 1

# Comando para iniciar a aplicação
CMD ["python3", "app.py"]
