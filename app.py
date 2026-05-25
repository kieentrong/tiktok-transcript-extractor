import os
import sys
import json
import time
import random
import traceback
import subprocess
from flask import Flask, render_template, request, jsonify, Response

# Thêm đường dẫn dự án vào sys.path để import từ download_and_parse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from download_and_parse import (
    sanitize_filename,
    clean_vtt,
    transcribe_audio_with_whisper,
    TRANSCRIPTS_DIR,
    TEMP_DIR,
    VIDEOS_JSON,
    SUMMARY_MD
)

import yt_dlp

app = Flask(__name__)

# Cấu hình CORS thủ công cho phép Tauri Webview kết nối an toàn
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        return response

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    return response

# Cờ kiểm soát dừng tiến trình cào dữ liệu
should_stop = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan_channel():
    try:
        data = request.json
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'status': 'error', 'message': 'Vui lòng cung cấp URL kênh.'}), 400
            
        ydl_opts = {
            'extract_flat': True,
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = info.get('entries', [])
            channel_name = info.get('title') or info.get('uploader') or "Kênh TikTok"
            
            return jsonify({
                'status': 'success',
                'channel_name': channel_name,
                'count': len(entries)
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_process():
    global should_stop
    should_stop = True
    return jsonify({'status': 'success', 'message': 'Đã gửi yêu cầu dừng tiến trình.'})

@app.route('/api/open-folder', methods=['POST'])
def open_transcripts_folder():
    try:
        if os.path.exists(TRANSCRIPTS_DIR):
            # Lệnh mở thư mục trên macOS (Finder)
            subprocess.run(['open', TRANSCRIPTS_DIR], check=True)
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Thư mục transcripts chưa tồn tại.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/start')
def start_extraction():
    url = request.args.get('url', '').strip()
    no_sub_option = request.args.get('no_sub_option', 'B') # 'B' = Whisper, 'A' = Bỏ qua
    
    if not url:
        return Response("data: " + json.dumps({'type': 'error', 'message': 'Không tìm thấy URL kênh.'}) + "\n\n", mimetype='text/event-stream')
        
    global should_stop
    should_stop = False
    
    def event_generator():
        global should_stop
        
        yield "data: " + json.dumps({'type': 'log', 'message': 'Đang kết nối tới TikTok để lấy danh sách video...'}) + "\n\n"
        
        # 1. Quét danh sách video
        ydl_opts_scan = {
            'extract_flat': True,
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True
        }
        
        videos = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts_scan) as ydl:
                info = ydl.extract_info(url, download=False)
                entries = info.get('entries', [])
                for entry in entries:
                    videos.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'url': entry.get('url'),
                        'duration': entry.get('duration'),
                        'description': entry.get('description'),
                        'timestamp': entry.get('timestamp')
                    })
                    
            # Lưu danh sách video làm lịch sử backup
            with open(VIDEOS_JSON, 'w', encoding='utf-8') as f:
                json.dump(videos, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            yield "data: " + json.dumps({'type': 'error', 'message': f'Lỗi quét danh sách video: {str(e)}'}) + "\n\n"
            return
            
        total_videos = len(videos)
        yield "data: " + json.dumps({'type': 'log', 'message': f'Quét thành công! Tìm thấy tổng cộng {total_videos} video.'}) + "\n\n"
        
        # Thống kê tiến trình
        stats = {'sub': 0, 'whisper': 0, 'skip': 0, 'fail': 0}
        results = []
        
        # 2. Vòng lặp xử lý từng video
        for i, video in enumerate(videos, 1):
            if should_stop:
                yield "data: " + json.dumps({'type': 'log', 'message': '⚠️ Đã dừng tiến trình cào dữ liệu theo yêu cầu của bạn.'}) + "\n\n"
                break
                
            video_id = video.get('id')
            title = video.get('title', f"Video {video_id}")
            video_url = video.get('url')
            
            safe_title = sanitize_filename(title)
            output_filename = f"{safe_title} - {video_id}.txt"
            output_path = os.path.join(TRANSCRIPTS_DIR, output_filename)
            
            yield "data: " + json.dumps({'type': 'log', 'message': f'[{i}/{total_videos}] Đang xử lý: {title}'}) + "\n\n"
            
            # Checkpoint: Đã có sẵn file kết quả
            if os.path.exists(output_path):
                stats['skip'] += 1
                results.append({'id': video_id, 'title': title, 'status': 'skipped', 'method': 'exists'})
                
                # Gửi cập nhật tiến độ
                percent = int((i / total_videos) * 100)
                yield "data: " + json.dumps({
                    'type': 'progress',
                    'percent': percent,
                    'current': i,
                    'total': total_videos,
                    'stats': stats
                }) + "\n\n"
                continue
                
            # Thêm delay ngẫu nhiên an toàn chống rate limit
            time.sleep(random.uniform(1.0, 2.5))
            
            # Thử tải phụ đề tiếng Việt
            vtt_temp_pattern = os.path.join(TEMP_DIR, f"{video_id}.%(ext)s")
            ydl_opts_sub = {
                'nocheckcertificate': True,
                'writesubtitles': True,
                'subtitleslangs': ['vie-VN', 'vi', 'vie'],
                'skip_download': True,
                'outtmpl': vtt_temp_pattern,
                'quiet': True,
                'no_warnings': True,
            }
            
            native_sub_success = False
            try:
                with yt_dlp.YoutubeDL(ydl_opts_sub) as ydl:
                    ydl.download([video_url])
                    
                # Tìm kiếm file .vtt
                vtt_file = None
                for ext in ['vtt', 'vie-VN.vtt', 'vi.vtt', 'vie.vtt']:
                    possible_path = os.path.join(TEMP_DIR, f"{video_id}.{ext}")
                    if os.path.exists(possible_path):
                        vtt_file = possible_path
                        break
                        
                if vtt_file:
                    with open(vtt_file, 'r', encoding='utf-8') as f:
                        vtt_content = f.read()
                        
                    clean_text = clean_vtt(vtt_content)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(clean_text)
                        
                    try:
                        os.remove(vtt_file)
                    except:
                        pass
                        
                    stats['sub'] += 1
                    native_sub_success = True
                    results.append({'id': video_id, 'title': title, 'status': 'success', 'method': 'native_sub'})
                    yield "data: " + json.dumps({'type': 'log', 'message': '   -> Tải và lưu phụ đề gốc tiếng Việt thành công!'}) + "\n\n"
            except Exception as e:
                pass
                
            # Nếu không có phụ đề tiếng Việt
            if not native_sub_success:
                if no_sub_option == 'A':
                    # Phương án A: Bỏ qua
                    stats['fail'] += 1
                    results.append({'id': video_id, 'title': title, 'status': 'failed', 'error': 'Không có phụ đề tiếng Việt (Chế độ bỏ qua)'})
                    yield "data: " + json.dumps({'type': 'log', 'message': '   -> Video không có phụ đề tiếng Việt. Bỏ qua theo tùy chọn của bạn.'}) + "\n\n"
                else:
                    # Phương án B: Chạy Whisper
                    yield "data: " + json.dumps({'type': 'log', 'message': '   -> Không tìm thấy phụ đề tiếng Việt. Đang tải âm thanh để dùng Whisper AI...'}) + "\n\n"
                    
                    audio_temp_pattern = os.path.join(TEMP_DIR, f"{video_id}.%(ext)s")
                    ydl_opts_audio = {
                        'nocheckcertificate': True,
                        'format': 'bestaudio/best',
                        'outtmpl': audio_temp_pattern,
                        'quiet': True,
                        'no_warnings': True,
                    }
                    
                    audio_file = None
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                            info_dict = ydl.extract_info(video_url, download=True)
                            filename = ydl.prepare_filename(info_dict)
                            if os.path.exists(filename):
                                audio_file = filename
                            else:
                                for file in os.listdir(TEMP_DIR):
                                    if file.startswith(video_id) and not file.endswith('.vtt'):
                                        audio_file = os.path.join(TEMP_DIR, file)
                                        break
                                        
                        if audio_file and os.path.exists(audio_file):
                            yield "data: " + json.dumps({'type': 'log', 'message': '   -> Đang phân tích giọng nói tiếng Việt bằng Whisper AI local...'}) + "\n\n"
                            
                            # Transcribe
                            clean_text = transcribe_audio_with_whisper(audio_file)
                            
                            with open(output_path, 'w', encoding='utf-8') as f:
                                f.write(clean_text)
                                
                            try:
                                os.remove(audio_file)
                            except:
                                pass
                                
                            stats['whisper'] += 1
                            results.append({'id': video_id, 'title': title, 'status': 'success', 'method': 'whisper'})
                            yield "data: " + json.dumps({'type': 'log', 'message': '   -> Phân tích giọng nói bằng Whisper và lưu transcript thành công!'}) + "\n\n"
                        else:
                            raise Exception("Không tải được âm thanh thô.")
                    except Exception as err:
                        stats['fail'] += 1
                        results.append({'id': video_id, 'title': title, 'status': 'failed', 'error': str(err)})
                        yield "data: " + json.dumps({'type': 'log', 'message': f'   ❌ Lỗi dịch Whisper: {str(err)}'}) + "\n\n"
                        
            # Cập nhật tiến độ sau khi hoàn thành 1 video
            percent = int((i / total_videos) * 100)
            yield "data: " + json.dumps({
                'type': 'progress',
                'percent': percent,
                'current': i,
                'total': total_videos,
                'stats': stats
            }) + "\n\n"
            
        # 3. Tạo báo cáo tổng hợp sau khi kết thúc
        try:
            success_sub = stats['sub']
            success_whisper = stats['whisper']
            skipped = stats['skip']
            failed = stats['fail']
            
            summary_content = f"""# Báo Cáo Kết Quả Cào Transcript Kênh TikTok (Giao diện Web GUI)

Tài liệu báo cáo tiến độ và kết quả phân tích transcript kênh TikTok.

---

## 📖 Lịch sử Thay đổi (Changelog)

| Phiên bản | Ngày | Tác giả | Nội dung thay đổi |
| :--- | :--- | :--- | :--- |
| **v2.0.0** | 25/05/2026 | Antigravity | Xuất kết quả hoàn thành từ ứng dụng Web GUI. |

---

## 📊 Thống kê Chung
- **Tổng số video trong kênh**: {total_videos}
- **Tổng số đã xử lý thành công**: {success_sub + success_whisper + skipped}
  - *Tải phụ đề gốc từ TikTok*: {success_sub} video
  - *Dịch âm thanh bằng Whisper local*: {success_whisper} video
  - *Đã có sẵn (Bỏ qua)*: {skipped} video
- **Thất bại**: {failed} video

---

## 📂 Danh sách Chi tiết Trạng thái từng Video

| STT | Video ID | Tiêu đề Video | Trạng thái | Phương pháp | Chi tiết / Lỗi |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
            for idx, r in enumerate(results, 1):
                status_icon = "✅ Thành công" if r.get('status') in ['success', 'skipped'] else "❌ Thất bại"
                method_str = "Phụ đề gốc" if r.get('method') == 'native_sub' else ("Whisper" if r.get('method') == 'whisper' else ("Đã có sẵn" if r.get('method') == 'exists' else "N/A"))
                error_msg = r.get('error', '-')
                summary_content += f"| {idx} | `{r.get('id')}` | {r.get('title')} | {status_icon} | {method_str} | {error_msg} |\n"
                
            with open(SUMMARY_MD, 'w', encoding='utf-8') as f:
                f.write(summary_content)
                
        except Exception as e:
            pass
            
        # Gửi thông điệp kết thúc tiến trình
        yield "data: " + json.dumps({'type': 'complete', 'total': total_videos}) + "\n\n"
        
    return Response(event_generator(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005, debug=False)
