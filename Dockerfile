# Usa uma imagem oficial do Python em versão slim (leve)
FROM python:3.11-slim

# Instala o ffmpeg e utilitários necessários, depois limpa o cache do apt para economizar espaço
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho no container
WORKDIR /app

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do servidor e os templates HTML
COPY main.py .
COPY templates/ ./templates/

# Cria a pasta onde os downloads serão salvos dentro do contêiner
RUN mkdir downloads

# Informa ao Docker que o contêiner escuta na porta 5000
EXPOSE 5000

# Executa o script com saída não-bufferizada (unbuffered)
ENTRYPOINT ["python", "-u", "main.py"]
