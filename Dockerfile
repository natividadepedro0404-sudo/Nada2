FROM python:3.14

# Instalar dependências do sistema para Chrome/Chromium
RUN apt-get update && apt-get install -y \
    chromium-browser \
    chromium-driver \
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
