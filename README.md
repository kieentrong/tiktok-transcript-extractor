# TikTok Transcript Extractor - NEX Picture Desktop Studio (v3.1.1)

Ứng dụng **Native Desktop App chuyên nghiệp** dành cho macOS giúp quét và trích xuất toàn bộ transcript (phụ đề hoặc dịch giọng nói thành văn bản bằng Whisper AI local) từ bất kỳ kênh TikTok nào. Dự án được phát triển và tối ưu hóa toàn diện theo triết lý thiết kế **NEX Picture Design Logic (White/Ice Theme)**.

---

## 🏗️ Kiến Trúc Hệ Thống (Tauri + Rust + Python)

Ứng dụng kết hợp sức mạnh vượt trội của 3 nền tảng công nghệ hiện đại:

```text
       ┌─────────────────────────────────────────────────────────┐
       │             TAURI NATIVE DESKTOP APP (.app)             │
       │                                                         │
       │   ┌─────────────────────────┐ ┌─────────────────────┐   │
       │   │    Tauri HTML5/CSS3     │ │  Tauri Rust Core    │   │
       │   │   Glassmorphism UI      │ │   (App Launcher)    │   │
       │   └────────────┬────────────┘ └──────────┬──────────┘   │
       │                │ HTTP API Requests       │              │
       │                ▼                         │ Khởi chạy    │
       │   ┌─────────────────────────┐            │ và Quản lý   │
       │   │   Local Flask Server    │◄───────────┘ ngầm         │
       │   │    (Python 5005)        │                           │
       │   └─────────────────────────┘                           │
       └─────────────────────────────────────────────────────────┘
```

1. **Tauri Frontend (HTML5/CSS3/JS Webkit)**:
   - Giao diện **White/Ice Surface** siêu sang trọng, nền sáng xám băng tuyết nhạt `#f4f7fa`, các card trắng nổi mịn màng với vầng sáng tỏa tròn xanh dương mờ dịu mắt ở góc (`rgba(0, 97, 255, 0.06)`).
   - Thiết kế **Flexbox tự co giãn thông minh**, khóa hoàn toàn thanh cuộn body dọc. Cửa sổ native `980x720` tự động khít tuyệt đối với giao diện, bảng logs tự co giãn theo chiều cao cửa sổ.
   - Chân trang (Footer) gọn gàng, tinh tế với nền sáng xanh băng nhạt, điểm xuyết vạch chia xanh thương hiệu của **NEX Picture**.
   - Trực tiếp kết nối Live Logs qua cơ chế Server-Sent Events (SSE) thời gian thực.
2. **Tauri Backend (Rust Core)**:
   - Tự động dò tìm thư mục dự án gốc (Recursive Parent Search), chạy ổn định dù di chuyển file `.app` đi bất cứ đâu.
   - **Tự khởi tạo (Self-installing)**: Tự động chạy lệnh tạo môi trường ảo Python `venv` và cài đặt thư viện (`pip install`) ngầm nếu chạy trên máy Mac hoàn toàn mới.
   - Khởi chạy ngầm Flask Server ẩn dưới nền, không hiển thị Terminal.
   - Thực hiện kiểm tra TCP port `5005` liên tục cho tới khi server sẵn sàng mới hiển thị cửa sổ giao diện để tránh lỗi trắng trang.
   - **Tự động dọn dẹp (Self-cleanup)**: Khi đóng cửa sổ app, Rust tự động kill sạch tiến trình Flask chạy ngầm để giải phóng 100% RAM/CPU.
3. **Flask Server (Python AI Engine)**:
   - Cổng chạy mặc định **`5005`** (tránh xung đột với cổng 5000 AirPlay mặc định của macOS).
   - Tích hợp `yt-dlp` quét và tải phụ đề gốc tiếng Việt siêu tốc.
   - Tích hợp mô hình **OpenAI Whisper AI (Local CPU)** tự động chuyển đổi giọng nói thành văn bản tiếng Việt chất lượng cao đối với các video không có phụ đề gốc.

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Dành cho Người dùng Cuối (End-User)
Ứng dụng đã được đóng gói chính thức tại thư mục gốc dự án:
- 📦 **TikTok Transcript Extractor.app**: Nhấp đúp chuột là chạy ngay.
- 💾 **TikTok Transcript Extractor_3.0.0_aarch64.dmg**: File đĩa cài đặt chuẩn macOS.

> [!NOTE]
> **Khi chạy trên máy Mac mới hoàn toàn ("Trắng tinh")**:
> 1. Chỉ cần nhấp đúp chạy ứng dụng `.app`.
> 2. Hệ thống sẽ tự động cài đặt môi trường ảo và thư viện ngầm trong vài chục giây. 
> 3. Nếu máy chưa từng cài Command Line Tools, macOS sẽ hiện thông báo hỏi cài đặt -> bạn chỉ cần bấm **"Install"** đồng ý, hệ thống sẽ xử lý tự động 100%.

### 2. Dành cho Nhà phát triển (Developer)
Yêu cầu hệ thống: **Node.js, pnpm, Rust/Cargo, Python 3**.

```bash
# 1. Cài đặt các thư viện Node.js
pnpm install

# 2. Chạy ứng dụng ở chế độ thử nghiệm (Development Mode)
pnpm tauri dev

# 3. Biên dịch và đóng gói ứng dụng native release (.app & .dmg)
pnpm tauri build
```

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
/
├── venv/                       # Môi trường ảo Python (Backend xử lý dữ liệu & AI)
├── transcripts/                # [Output] Thư mục chứa các tệp transcript sạch (.txt)
├── templates/                  
│   └── index.html              # Giao diện chính B2B NEX Picture (HTML/CSS/JS)
├── src-tauri/                  # Thư mục mã nguồn Tauri Rust Desktop App
│   ├── Cargo.toml              # Cấu hình dependencies Rust
│   ├── tauri.conf.json         # Cấu hình cửa sổ Tauri & Bundler đóng gói
│   └── src/
│       └── main.rs             # Mã nguồn Rust quản lý tiến trình Flask chạy ngầm
├── app.py                      # Flask API Server điều phối logic cào và AI
├── run_app.py                  # Script Python khởi chạy (dành cho chế độ chạy web)
├── download_and_parse.py       # Core module tải phụ đề và transcribe Whisper
├── package.json                # Cấu hình Node.js/pnpm
└── README.md                   # Tài liệu hướng dẫn dự án chính thức
```

---

## 📖 Nhật Ký Phiên Bản (Changelog)

- **v1.0.0**: Khởi tạo quét kênh và tải phụ đề WebVTT bằng `yt-dlp`.
- **v1.1.0**: Hoàn thành cào transcript 168 video dạng `[Tên Video] - [Video ID].txt` và Whisper local dịch audio.
- **v2.0.0**: Đóng gói thành Local Web App với giao diện Glassmorphism Dark Mode và kết nối SSE.
- **v2.1.0**: Cập nhật Copyright chân trang thành **Copyright by Kien NEX Picture • Phiên bản v2.0** và đóng gói thành `.app` macOS chuẩn.
- **v2.2.0**: Tích hợp Chrome App Mode và AppleScript đóng Terminal tự động.
- **v2.3.0**: Sửa lỗi tắt Flask bằng cơ chế `disown`, tích hợp tự động setup venv (Self-installing).
- **v2.3.1**: Chuyển cổng chạy mặc định sang **`5005`** giải quyết triệt để lỗi xung đột AirPlay macOS.
- **v3.0.0**: **[Nâng cấp Công nghệ Đột phá]** Chuyển đổi sang **Tauri Desktop Framework**. Rust backend quản lý ngầm Flask Python và tự động dọn dẹp khi tắt app, loại bỏ hoàn toàn Terminal và Chrome tab.
- **v3.1.0**: Áp dụng triệt để **NEX Picture Design Logic (White/Ice Theme)** màu sáng sang trọng. Áp dụng layout Flexbox tự co giãn khóa thanh cuộn body ngoài.
- **v3.1.1**: **[Đồng bộ hóa 100% Giao diện Sáng]** Chuyển đổi Console log và Footer sang tông màu sáng Ice/White đồng điệu mượt mà.

---

*Copyright by Kien NEX Picture • Phiên bản v2.0*
