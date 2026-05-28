import argparse
import json
import os

import yt_dlp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT = os.path.join(BASE_DIR, 'videos.json')


def normalize_tiktok_url(value):
    value = value.strip()
    if value.startswith('@'):
        return f'https://www.tiktok.com/{value}'
    return value


parser = argparse.ArgumentParser(description='Quét danh sách video từ một kênh TikTok.')
parser.add_argument('url', help='URL kênh TikTok hoặc username dạng @username')
parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT, help='File JSON đầu ra, mặc định là videos.json trong thư mục dự án')
args = parser.parse_args()

url = normalize_tiktok_url(args.url)

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
            
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(video_list, f, indent=2, ensure_ascii=False)
        print(f"Đã lưu danh sách video vào {args.output}")
    except Exception as e:
        print(f"Lỗi: {e}")
