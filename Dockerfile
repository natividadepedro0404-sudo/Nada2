FROM selenium/standalone-chrome:latest

USER root

# Instalar Python e pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Criar e usar virtualenv (evita conflito com pacotes do sistema)
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Expor porta
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:4000/ || exit 1

# Comando para iniciar a aplicação
CMD ["python3", "app.py"]
