import yt_dlp
import json

url = 'https://www.tiktok.com/@khoang.lang.cuocsong'

ydl_opts = {
    'extract_flat': True,
    'nocheckcertificate': True,
}

print("Đang quét toàn bộ danh sách video của kênh...")
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    try:
        info = ydl.extract_info(url, download=False)
        entries = info.get('entries', [])
        print(f"Quét thành công! Tìm thấy tổng cộng {len(entries)} video.")
        
        # Lưu danh sách video vào file json để phân tích
        video_list = []
        for entry in entries:
            video_list.append({
                'id': entry.get('id'),
                'title': entry.get('title'),
                'url': entry.get('url'),
                'duration': entry.get('duration'),
                'description': entry.get('description'),
                'timestamp': entry.get('timestamp')
            })
            
        with open('videos.json', 'w', encoding='utf-8') as f:
            json.dump(video_list, f, indent=2, ensure_ascii=False)
        print("Đã lưu danh sách video vào videos.json")
    except Exception as e:
        print(f"Lỗi: {e}")
