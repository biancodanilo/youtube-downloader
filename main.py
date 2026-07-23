import os
import sys
import uuid
import threading
import yt_dlp
from flask import Flask, render_template, request, jsonify

# Inicializa o ffmpeg estático para desenvolvimento local
try:
    import static_ffmpeg
    print("[+] Inicializando FFmpeg...")
    static_ffmpeg.add_paths()
except Exception as e:
    print(f"[Aviso] Não foi possível carregar o static-ffmpeg: {e}")

app = Flask(__name__)

# Dicionário global para guardar o progresso das tarefas de download
tasks = {}

def format_duration(seconds):
    if not seconds:
        return "Desconhecido"
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def run_download_thread(task_id, url, format_type):
    tasks[task_id] = {
        'state': 'downloading',
        'percent': 0,
        'speed': '0B/s',
        'eta': '00:00',
        'error': None
    }
    
    def ydl_hook(d):
        if d['status'] == 'downloading':
            # Limpar e obter a porcentagem de download
            percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
            try:
                percent = float(percent_str)
            except ValueError:
                percent = 0.0
            
            tasks[task_id]['percent'] = percent
            tasks[task_id]['speed'] = d.get('_speed_str', 'N/A').strip()
            tasks[task_id]['eta'] = d.get('_eta_str', 'N/A').strip()
        elif d['status'] == 'finished':
            tasks[task_id]['state'] = 'processing'
            
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'progress_hooks': [ydl_hook],
        'quiet': True,
        'no_warnings': True,
    }
    
    if format_type == 'mp4':
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    elif format_type == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        tasks[task_id]['state'] = 'completed'
    except Exception as e:
        tasks[task_id]['state'] = 'failed'
        tasks[task_id]['error'] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    format_type = data.get('format', 'mp4').strip()
    
    if not url:
        return jsonify({'error': 'Por favor, forneça um link do YouTube válido.'}), 400
        
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        title = info.get('title', 'Sem título')
        duration = info.get('duration')
        uploader = info.get('uploader', 'Desconhecido')
        
        task_id = str(uuid.uuid4())
        
        # Inicia a thread de download em segundo plano
        thread = threading.Thread(target=run_download_thread, args=(task_id, url, format_type))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'title': title,
            'duration': format_duration(duration),
            'uploader': uploader
        })
        
    except Exception as e:
        return jsonify({'error': f"Erro ao obter informações do vídeo: {str(e)}"}), 400

@app.route('/api/progress/<task_id>', methods=['GET'])
def api_progress(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Tarefa de download não encontrada.'}), 404
    return jsonify(task)

if __name__ == '__main__':
    # Criar pasta 'downloads' se não existir
    os.makedirs('downloads', exist_ok=True)
    # Rodar servidor web acessível na rede local
    app.run(host='0.0.0.0', port=5000, debug=False)
