import os
import sys
import json
import re
import time
import random
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# Thêm static-ffmpeg để tự động xử lý ffmpeg binary cho Whisper trên macOS
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
    print("Đã tích hợp static-ffmpeg thành công!")
except ImportError:
    print("Chưa cài đặt static-ffmpeg. Sẽ cố gắng cài đặt bổ sung nếu cần dùng Whisper.")

import yt_dlp

# Đường dẫn thư mục
BASE_DIR = '/Users/kientrong/Desktop/Antigravity/Kien'
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, 'transcripts')
TEMP_DIR = os.path.join(BASE_DIR, 'temp_audio')
VIDEOS_JSON = os.path.join(BASE_DIR, 'videos.json')
SUMMARY_MD = os.path.join(BASE_DIR, 'summary.md')

# Đảm bảo các thư mục tồn tại
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Khởi tạo mô hình Whisper (lazy loading)
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Đang tải mô hình Whisper base (tiếng Việt)...")
        import whisper
        # Sử dụng model 'base' cho độ chính xác tốt mà vẫn nhẹ và nhanh
        whisper_model = whisper.load_model('base')
        print("Đã tải mô hình Whisper base thành công!")
    return whisper_model

def sanitize_filename(title):
    """Làm sạch tiêu đề để làm tên file macOS hợp lệ"""
    # Thay thế các ký tự không hợp lệ bằng khoảng trắng
    clean = re.sub(r'[\\/*?:"<>|]', ' ', title)
    # Loại bỏ khoảng trắng thừa
    clean = ' '.join(clean.split())
    # Giới hạn độ dài tên file tối đa 100 ký tự để an toàn
    if len(clean) > 100:
        clean = clean[:100].strip()
    # Nếu rỗng thì trả về mặc định
    return clean if clean else "video_transcript"

def clean_vtt(vtt_content):
    """Phân tích cú pháp file .vtt và trả về văn bản sạch"""
    lines = vtt_content.strip().split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line == 'WEBVTT':
            continue
        if '-->' in line:
            continue
        if line.startswith('NOTE'):
            continue
        
        # Loại bỏ các thẻ định dạng HTML trong WebVTT nếu có (ví dụ <c>...</c>)
        line = re.sub(r'<[^>]+>', '', line)
        
        # Tránh lặp lại các dòng giống hệt nhau liên tiếp (thường xảy ra ở phụ đề tự động)
        if cleaned_lines and cleaned_lines[-1] == line:
            continue
            
        cleaned_lines.append(line)
        
    return '\n'.join(cleaned_lines)

def transcribe_audio_with_whisper(audio_path):
    """Sử dụng Whisper local để transcribe audio"""
    try:
        model = get_whisper_model()
        print(f"Đang phân tích âm thanh {os.path.basename(audio_path)} bằng Whisper...")
        # Nhận diện giọng nói với ngôn ngữ tiếng Việt
        result = model.transcribe(audio_path, language='vi', verbose=False)
        
        # Định dạng văn bản kết quả cho dễ đọc
        segments = result.get('segments', [])
        text_lines = []
        for seg in segments:
            text = seg.get('text', '').strip()
            if text:
                text_lines.append(text)
                
        return '\n'.join(text_lines)
    except Exception as e:
        print(f"Lỗi khi chạy Whisper: {e}")
        traceback.print_exc()
        raise e

def process_single_video(video, index, total):
    video_id = video.get('id')
    title = video.get('title', f"Video {video_id}")
    url = video.get('url')
    
    safe_title = sanitize_filename(title)
    output_filename = f"{safe_title} - {video_id}.txt"
    output_path = os.path.join(TRANSCRIPTS_DIR, output_filename)
    
    print(f"[{index}/{total}] Bắt đầu xử lý: {title} (ID: {video_id})")
    
    # 1. Kiểm tra nếu file kết quả đã tồn tại (hỗ trợ checkpoint)
    if os.path.exists(output_path):
        print(f"   -> Đã xử lý từ trước. Bỏ qua.")
        return {'id': video_id, 'title': title, 'status': 'skipped', 'method': 'exists'}
        
    # Thêm delay ngẫu nhiên từ 1-3 giây để tránh bị rate limit từ TikTok
    time.sleep(random.uniform(1.0, 3.0))
    
    # 2. Thử tải phụ đề tiếng Việt gốc từ TikTok
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
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_sub) as ydl:
            ydl.download([url])
            
        # Tìm file .vtt vừa tải về
        vtt_file = None
        for ext in ['vtt', 'vie-VN.vtt', 'vi.vtt', 'vie.vtt']:
            possible_path = os.path.join(TEMP_DIR, f"{video_id}.{ext}")
            if os.path.exists(possible_path):
                vtt_file = possible_path
                break
                
        if vtt_file:
            print("   -> Tải phụ đề tiếng Việt thành công!")
            with open(vtt_file, 'r', encoding='utf-8') as f:
                vtt_content = f.read()
                
            clean_text = clean_vtt(vtt_content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(clean_text)
                
            # Dọn dẹp file tạm
            try:
                os.remove(vtt_file)
            except:
                pass
                
            print("   -> Đã lưu transcript thành công từ phụ đề gốc.")
            return {'id': video_id, 'title': title, 'status': 'success', 'method': 'native_sub'}
            
    except Exception as e:
        print(f"   -> Không tải được phụ đề trực tiếp. Lỗi: {e}")
        
    # 3. Phương án B: Tải audio và sử dụng Whisper để nhận diện giọng nói
    print("   -> Đang tiến hành tải âm thanh để chạy Whisper...")
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
            info_dict = ydl.extract_info(url, download=True)
            # Lấy tên file thực tế được tải về
            filename = ydl.prepare_filename(info_dict)
            if os.path.exists(filename):
                audio_file = filename
            else:
                # Tìm thủ công nếu không khớp
                for file in os.listdir(TEMP_DIR):
                    if file.startswith(video_id) and not file.endswith('.vtt'):
                        audio_file = os.path.join(TEMP_DIR, file)
                        break
                        
        if audio_file and os.path.exists(audio_file):
            print(f"   -> Đã tải xong file âm thanh: {os.path.basename(audio_file)}")
            # Chạy Whisper để lấy transcript
            clean_text = transcribe_audio_with_whisper(audio_file)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(clean_text)
                
            # Dọn dẹp file âm thanh tạm thời
            try:
                os.remove(audio_file)
            except:
                pass
                
            print("   -> Đã dịch và lưu transcript thành công bằng Whisper.")
            return {'id': video_id, 'title': title, 'status': 'success', 'method': 'whisper'}
        else:
            raise Exception("Không tìm thấy file âm thanh tải về.")
            
    except Exception as e:
        print(f"   ❌ Lỗi nghiêm trọng khi xử lý video {video_id}: {e}")
        return {'id': video_id, 'title': title, 'status': 'failed', 'error': str(e)}

def main():
    start_time = time.time()
    
    if not os.path.exists(VIDEOS_JSON):
        print(f"Lỗi: Không tìm thấy file {VIDEOS_JSON}. Vui lòng chạy get_all_videos.py trước.")
        sys.exit(1)
        
    with open(VIDEOS_JSON, 'r', encoding='utf-8') as f:
        videos = json.load(f)
        
    total_videos = len(videos)
    print(f"Bắt đầu xử lý tổng cộng {total_videos} video...")
    
    results = []
    
    # Để an toàn cho TikTok rate limits và hiệu năng máy khi chạy Whisper local,
    # chúng tôi sẽ chạy TUẦN TỰ (Sequential) thay vì chạy song song luồng lớn.
    # Whisper chạy rất nặng CPU/RAM, chạy tuần tự sẽ giúp máy ổn định và không bị block IP.
    for i, video in enumerate(videos, 1):
        try:
            res = process_single_video(video, i, total_videos)
            results.append(res)
        except Exception as e:
            results.append({
                'id': video.get('id'),
                'title': video.get('title'),
                'status': 'failed',
                'error': str(e)
            })
            
    # Thống kê kết quả
    total_processed = len(results)
    success_sub = sum(1 for r in results if r.get('status') == 'success' and r.get('method') == 'native_sub')
    success_whisper = sum(1 for r in results if r.get('status') == 'success' and r.get('method') == 'whisper')
    skipped = sum(1 for r in results if r.get('status') == 'skipped')
    failed = sum(1 for r in results if r.get('status') == 'failed')
    
    elapsed_time = time.time() - start_time
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)
    time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    # Tạo báo cáo tổng hợp bằng tiếng Việt
    summary_content = f"""# Báo Cáo Kết Quả Cào Transcript Kênh TikTok @khoang.lang.cuocsong

Tài liệu báo cáo tiến độ và kết quả phân tích transcript kênh TikTok `@khoang.lang.cuocsong`.

---

## 📖 Lịch sử Thay đổi (Changelog)

| Phiên bản | Ngày | Tác giả | Nội dung thay đổi |
| :--- | :--- | :--- | :--- |
| **v1.0.0** | 25/05/2026 | Antigravity | Hoàn thành cào và xử lý transcript cho toàn bộ kênh. |

---

## 📊 Thống kê Chung
- **Tổng số video trong kênh**: {total_videos}
- **Tổng số đã xử lý thành công**: {success_sub + success_whisper + skipped}
  - *Tải phụ đề gốc từ TikTok*: {success_sub} video
  - *Dịch âm thanh bằng Whisper local*: {success_whisper} video
  - *Đã tồn tại trước đó (Bỏ qua)*: {skipped} video
- **Thất bại**: {failed} video
- **Tổng thời gian thực hiện**: {time_str}

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
        
    print(f"\n===== HOÀN THÀNH QUÁ TRÌNH =====\n")
    print(f"Tổng số video: {total_videos}")
    print(f"Thành công từ phụ đề gốc: {success_sub}")
    print(f"Thành công từ Whisper: {success_whisper}")
    print(f"Bỏ qua (đã có): {skipped}")
    print(f"Thất bại: {failed}")
    print(f"Báo cáo tổng hợp đã được lưu tại {SUMMARY_MD}")

if __name__ == '__main__':
    main()
