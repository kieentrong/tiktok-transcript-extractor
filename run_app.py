import os
import sys
import time
import socket
import webbrowser
import threading
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, 'venv', 'bin', 'python')

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def open_browser():
    # Đợi 1.5 giây để Flask server khởi động ổn định trước khi mở cửa sổ ứng dụng
    time.sleep(1.5)
    url = "http://127.0.0.1:5005"
    
    # Danh sách các đường dẫn cài đặt Chrome phổ biến trên macOS
    chrome_paths = [
        "/Applications/Google Chrome.app",
        "/Users/kientrong/Applications/Google Chrome.app"
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_found = True
            break
            
    if chrome_found:
        print("\n🚀 Đang khởi chạy ứng dụng dưới dạng cửa sổ độc lập (Chrome App Mode)...")
        # Sử dụng lệnh open của macOS để chạy Chrome ở chế độ cửa sổ ứng dụng độc lập (--app)
        subprocess.run([
            "open", "-a", "Google Chrome", 
            "--args", f"--app={url}", 
            "--new-window"
        ])
    else:
        # Fallback về trình duyệt mặc định nếu không tìm thấy Chrome trên macOS
        print(f"\n🚀 Đang tự động mở trình duyệt tại địa chỉ: {url}...")
        webbrowser.open(url)

def main():
    print("==================================================================")
    print("🌐 KHỞI CHẠY PHẦN MỀM TỰ ĐỘNG CÀO TRANSCRIPT TIKTOK v2.0")
    print("==================================================================")
    
    # 1. Kiểm tra môi trường ảo venv
    if not os.path.exists(VENV_PYTHON):
        print(f"❌ Lỗi: Không tìm thấy môi trường ảo tại {VENV_PYTHON}")
        print("Vui lòng đảm bảo bạn đã tạo venv và cài đặt đầy đủ thư viện.")
        sys.exit(1)
        
    # 2. Kiểm tra xung đột cổng 5005
    port = 5005
    if is_port_in_use(port):
        print(f"⚠️ Cảnh báo: Cổng {port} hiện đang bận (có thể do một server cũ đang chạy).")
        print("Đang cố gắng khởi chạy, nếu lỗi vui lòng tắt ứng dụng đang chiếm cổng và thử lại.")
        
    # 3. Khởi chạy tiến trình mở trình duyệt trong một luồng riêng
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 4. Khởi chạy Flask Server sử dụng Python của venv
    try:
        app_path = os.path.join(BASE_DIR, 'app.py')
        print(f"📡 Đang khởi động Web Server cục bộ...")
        
        # Chạy app.py bằng venv python
        subprocess.run([VENV_PYTHON, app_path])
    except KeyboardInterrupt:
        print("\n👋 Đã tắt Web Server cục bộ theo yêu cầu. Hẹn gặp lại bạn lần sau!")
    except Exception as e:
        print(f"\n❌ Lỗi khởi chạy server: {e}")

if __name__ == '__main__':
    main()
