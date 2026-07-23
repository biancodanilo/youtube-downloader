@echo off
echo ============================================================
echo   GERADOR DE DOCKER PARA IMPORTACAO (yt-dlp) - By Antigravity
echo ============================================================
echo.

REM Verifica se o docker esta disponivel no sistema
where docker >nul 2>nul
if errorlevel 1 (
    echo [ERRO] O Docker nao esta instalado ou nao esta no seu PATH.
    echo Certifique-se de que o Docker Desktop esta instalado, aberto e rodando.
    echo.
    echo Para instalar o Docker, acesse: https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo [+] 1/2 Construindo a imagem Docker local ('youtube-downloader')...
docker build -t youtube-downloader .
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao construir a imagem Docker.
    pause
    exit /b 1
)

echo.
echo [+] 2/2 Exportando a imagem para 'youtube-downloader.tar'...
docker save -o youtube-downloader.tar youtube-downloader
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao salvar a imagem em arquivo .tar.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [SUCESSO] Arquivo 'youtube-downloader.tar' gerado com exito!
echo.
echo O que fazer agora:
echo 1. Acesse o Portainer em http://srv/#/
echo 2. Va em 'Images' -^> 'Import image'
echo 3. Faca o upload do arquivo 'youtube-downloader.tar' que esta nesta pasta.
echo ============================================================
echo.
pause
