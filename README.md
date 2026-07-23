# 🎬 YouTube Downloader - Documentação do Projeto

Este projeto é uma aplicação web simples, rápida e moderna para download de vídeos e áudios do YouTube, construída em **Python (Flask)** utilizando a biblioteca **yt-dlp** e **FFmpeg**.

---

## 💡 Como Funciona

A aplicação é dividida em duas partes principais: **Frontend** (Interface Web) e **Backend** (API Flask com Threads assíncronas).

### 1. Interface Web (Frontend)
- O usuário insere o link do vídeo do YouTube no formulário.
- Seleciona o formato desejado:
  - **MP4** (Vídeo em alta qualidade + Áudio mesclado).
  - **MP3** (Apenas o áudio extraído e convertido para 192kbps).
- Ao clicar em baixar, o navegador envia uma requisição `POST` e inicia o acompanhamento em tempo real do progresso.

### 2. API e Motor de Download (Backend)
1. **Extração de Informações (`POST /api/download`)**:
   - Valida a URL e obtém dados preliminares do vídeo (título, duração, autor) sem baixá-lo.
   - Gera um ID único de tarefa (`task_id`) com `uuid`.
   - Inicia uma **Thread em segundo plano** para processar o download sem travar a interface do usuário.
2. **Download em Segundo Plano**:
   - A thread utiliza a biblioteca `yt-dlp` com um hook de progresso (`progress_hooks`).
   - Atualiza continuamente o estado da tarefa (porcentagem conclusiva, velocidade de download e tempo estimado ETA) em um dicionário global em memória.
   - Se for formato **MP3**, aciona o pós-processador do **FFmpeg** para extrair a faixa de áudio.
3. **Consulta de Progresso (`GET /api/progress/<task_id>`)**:
   - A interface faz requisições periódicas (*polling*) a essa rota para atualizar a barra de progresso em tempo real na tela.
4. **Armazenamento**:
   - Os arquivos baixados são gravados na pasta de destino `downloads/`.

---

## 📋 Pré-requisitos

Para rodar o projeto, você precisará de:

- **Modo Local (Python)**:
  - Python 3.8 ou superior instalado.
  - FFmpeg (ou a biblioteca `static-ffmpeg` que baixa os binários automaticamente).
- **Modo Docker / Portainer**:
  - Docker Desktop instalado e rodando.

---

## 🚀 Como Instalar e Executar

Você pode rodar este projeto de **duas formas**: diretamente no Python local ou através do Docker / Portainer.

---

### Opção 1: Execução Local (Python)

1. **Abra o terminal/PowerShell** na pasta do projeto:
   ```bash
   cd c:\Python\youtube-downloader
   ```

2. **(Opcional) Crie e ative um ambiente virtual**:
   ```bash
   python -m venv venv
   # No Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # No Windows (CMD):
   .\venv\Scripts\activate.bat
   ```

3. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Caso não tenha o FFmpeg instalado no sistema, você pode instalar o `static-ffmpeg` rodando `pip install static-ffmpeg`).*

4. **Inicie o servidor Flask**:
   ```bash
   python main.py
   ```

5. **Acesse no seu navegador**:
   - Endereço local: `http://localhost:5000`
   - Acesso pela rede local: `http://<IP-DO-SEU-PC>:5000`

---

### Opção 2: Execução com Docker e Portainer

O projeto conta com um script automatizado (`gerar_docker.bat`) para facilitar a criação e exportação da imagem para o Portainer.

#### Passo a passo via Script (`gerar_docker.bat`):

1. Certifique-se de que o **Docker Desktop** está rodando.
2. Dê um duplo clique no arquivo [`gerar_docker.bat`](file:///c:/Python/youtube-downloader/gerar_docker.bat) ou rode no terminal:
   ```cmd
   .\gerar_docker.bat
   ```
3. O script irá:
   - Criar a imagem Docker com o nome `youtube-downloader`.
   - Exportar a imagem para o arquivo `youtube-downloader.tar`.
4. **Importar no Portainer**:
   - Acesse seu servidor Portainer (ex: `http://srv/#/`).
   - Vá no menu **Images** -> **Import image**.
   - Faça o upload do arquivo `youtube-downloader.tar` gerado na pasta do projeto.
5. **Criar e Iniciar o Container**:
   - Crie um novo Container no Portainer apontando para a imagem `youtube-downloader`.
   - Mapeie a porta de entrada `5000:5000`.
   - (Recomendado) Monte um Volume ou Bind da pasta `/app/downloads` para salvar os arquivos baixados no host.

#### Rodando diretamente via Linha de Comando (Docker CLI):

```bash
# 1. Construir a imagem Docker
docker build -t youtube-downloader .

# 2. Rodar o container expondo a porta 5000 e mapeando a pasta de downloads
docker run -d -p 5000:5000 -v %cd%/downloads:/app/downloads --name yt-downloader youtube-downloader
```

---

## 📁 Estrutura de Arquivos do Projeto

- 📄 [`main.py`](file:///c:/Python/youtube-downloader/main.py): Código principal do servidor Flask, gerenciamento de threads de download, endpoints da API e integração com `yt-dlp`.
- 📄 [`Dockerfile`](file:///c:/Python/youtube-downloader/Dockerfile): Instruções para construir a imagem Docker baseada em `python:3.11-slim` com `ffmpeg` pré-instalado.
- ⚙️ [`gerar_docker.bat`](file:///c:/Python/youtube-downloader/gerar_docker.bat): Script em lote (batch) do Windows para compilar a imagem Docker e gerar o pacote `.tar` para importação no Portainer.
- 📄 [`requirements.txt`](file:///c:/Python/youtube-downloader/requirements.txt): Lista de dependências Python (`Flask`, `yt-dlp`).
- 📁 `templates/`: Contém as telas HTML da aplicação web (`index.html`).
- 📁 `downloads/`: Pasta onde os arquivos baixados (vídeos MP4 e áudios MP3) são armazenados.

---

## 🛠️ Tecnologias Utilizadas

- **[Python 3.11](https://www.python.org/)**
- **[Flask](https://flask.palletsprojects.com/)**: Framework web leve para Python.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**: Biblioteca avançada para download de mídias do YouTube e centenas de outros sites.
- **[FFmpeg](https://ffmpeg.org/)**: Utilitário para conversão e mesclagem de áudio/vídeo.
- **[Docker](https://www.docker.com/)**: Conteinerização da aplicação.
