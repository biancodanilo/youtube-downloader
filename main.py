import os
import sys
import uuid
import re
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

def sanitize_filename(name):
    if not name:
        return "download"
    # Remove ou substitui caracteres proibidos no sistema de arquivos
    cleaned = re.sub(r'[\\/:*?"<>|]', '-', str(name))
    cleaned = cleaned.strip().strip('.')
    return cleaned if cleaned else "download"

def format_duration(seconds):
    if not seconds:
        return "Desconhecido"
    try:
        seconds = int(seconds)
        mins, secs = divmod(seconds, 60)
        hrs, mins = divmod(mins, 60)
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "Desconhecido"

def run_batch_download_thread(task_id, items, format_type):
    total_items = len(items)
    tasks[task_id] = {
        'state': 'downloading',
        'current_index': 1,
        'total_items': total_items,
        'current_title': '',
        'percent': 0.0,
        'overall_percent': 0.0,
        'speed': '0B/s',
        'eta': '00:00',
        'completed_count': 0,
        'failed_count': 0,
        'error': None
    }
    
    for idx, item in enumerate(items):
        url = item.get('url')
        raw_title = item.get('custom_title') or item.get('title') or f"video_{idx + 1}"
        custom_title = sanitize_filename(raw_title)
        
        tasks[task_id]['current_index'] = idx + 1
        tasks[task_id]['current_title'] = custom_title
        tasks[task_id]['percent'] = 0.0
        
        def ydl_hook(d):
            if d['status'] == 'downloading':
                percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
                try:
                    percent = float(percent_str)
                except ValueError:
                    percent = 0.0
                
                tasks[task_id]['percent'] = percent
                overall = ((idx + (percent / 100.0)) / total_items) * 100.0
                tasks[task_id]['overall_percent'] = round(overall, 1)
                tasks[task_id]['speed'] = d.get('_speed_str', 'N/A').strip()
                tasks[task_id]['eta'] = d.get('_eta_str', 'N/A').strip()
            elif d['status'] == 'finished':
                tasks[task_id]['state'] = 'processing'

        ydl_opts = {
            'outtmpl': f'downloads/{custom_title}.%(ext)s',
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
            tasks[task_id]['state'] = 'downloading'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            tasks[task_id]['completed_count'] += 1
        except Exception as e:
            tasks[task_id]['failed_count'] += 1
            print(f"[Erro no item {idx + 1}] {custom_title}: {e}")

    tasks[task_id]['state'] = 'completed'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/fetch_info', methods=['POST'])
def api_fetch_info():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'Por favor, forneça um link do YouTube válido.'}), 400
        
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # Extração rápida de playlists/vídeos
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        items = []
        entries = info.get('entries')
        
        if entries is not None:
            # É uma playlist
            playlist_title = info.get('title', 'Playlist do YouTube')
            for entry in entries:
                if not entry:
                    continue
                entry_id = entry.get('id', '')
                entry_url = entry.get('url') or (f"https://www.youtube.com/watch?v={entry_id}" if entry_id else url)
                items.append({
                    'id': entry_id,
                    'url': entry_url,
                    'title': entry.get('title', 'Sem título'),
                    'uploader': entry.get('uploader', info.get('uploader', 'Desconhecido')),
                    'duration': format_duration(entry.get('duration'))
                })
            return jsonify({
                'is_playlist': True,
                'playlist_title': playlist_title,
                'items': items
            })
        else:
            # É um vídeo individual
            video_title = info.get('title', 'Sem título')
            items.append({
                'id': info.get('id', ''),
                'url': info.get('webpage_url') or url,
                'title': video_title,
                'uploader': info.get('uploader', 'Desconhecido'),
                'duration': format_duration(info.get('duration'))
            })
            return jsonify({
                'is_playlist': False,
                'playlist_title': video_title,
                'items': items
            })
            
    except Exception as e:
        return jsonify({'error': f"Erro ao consultar o link: {str(e)}"}), 400

@app.route('/api/download_batch', methods=['POST'])
def api_download_batch():
    data = request.get_json() or {}
    items = data.get('items', [])
    format_type = data.get('format', 'mp4').strip()
    
    if not items or not isinstance(items, list):
        return jsonify({'error': 'Nenhum item válido selecionado para download.'}), 400
        
    task_id = str(uuid.uuid4())
    
    # Inicia a thread de download em lote
    thread = threading.Thread(target=run_batch_download_thread, args=(task_id, items, format_type))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'total_items': len(items)
    })

@app.route('/api/progress/<task_id>', methods=['GET'])
def api_progress(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Tarefa de download não encontrada.'}), 404
    return jsonify(task)

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
