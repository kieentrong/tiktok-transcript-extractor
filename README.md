# TikTok Transcript Extractor - NEX Picture Desktop Studio (v3.1.1)

Ứng dụng **Native Desktop App chuyên nghiệp** dành cho macOS giúp tự động quét, cào và trích xuất sạch sẽ toàn bộ transcript từ bất kỳ kênh TikTok nào. 
---

## Tính năng chính (Core Features)

*   **Quét Kênh Siêu Tốc**: Chỉ cần dán URL hoặc Username của kênh TikTok, phần mềm tự động quét và thống kê chính xác tổng số lượng video hiện có trên kênh chỉ trong 1-2 giây.
*   **Trích Xuất Phụ Đề Gốc Tiếng Việt**: Tự động tải xuống phụ đề tiếng Việt gốc được uploader đính kèm trên TikTok một cách nhanh chóng và chính xác.
*   ** Whisper AI Local (Dự Phòng Thiếu Phụ Đề)**: Đối với các video không có phụ đề gốc, phần mềm tích hợp sẵn mô hình **OpenAI Whisper AI (chạy trực tiếp trên CPU cục bộ)** tự động nghe và chuyển đổi giọng nói trong video thành văn bản tiếng Việt chất lượng cao.
*   **Dọn Dẹp và Làm Sạch Văn Bản**: Phân tích cú pháp các tệp phụ đề thô (`.vtt`), loại bỏ hoàn toàn các thẻ HTML định dạng, mốc thời gian thừa và các dòng lặp lại liên tiếp để xuất ra tệp văn bản sạch sẽ (`.txt`).
*   **Định Dạng Tên Tệp Chuẩn Hóa**: Tự động lưu trữ các tệp transcript vào thư mục kết quả dưới dạng đặt tên chuyên nghiệp: `[Tiêu Đề Video] - [ID Video].txt`.
*   **Live Logs SSE Thời Gian Thực**: Cung cấp giao diện console log cập nhật từng giây và thanh tiến trình gradient mượt mà hiển thị chi tiết trạng thái xử lý từng video (Đã có sẵn, dùng Whisper, dùng phụ đề gốc, hoặc bị lỗi).
*   **Tự Động Tắt Sạch Flask Server**: Khi bạn đóng cửa sổ ứng dụng Tauri, Rust Backend sẽ tự động kill sạch Flask Python server chạy ngầm dưới nền, giải phóng 100% tài nguyên RAM và CPU cho macOS.

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng
Mac Os Native
### 📂 1. Dành cho Người dùng Cuối (End-User)
Ứng dụng native đã được biên dịch và đóng gói sẵn sàng tại thư mục gốc:
*   📦 **TikTok Transcript Extractor.app**: Bản chạy native trực tiếp. Bạn có thể kéo tệp này vào thư mục `/Applications` để sử dụng lâu dài.
*   💾 **TikTok Transcript Extractor_3.0.0_aarch64.dmg**: File cài đặt đĩa đệm chuẩn macOS.

#### 💡 Cách Vận Hành Trên Một Máy Mac Mới Hoàn Toàn:
1.  **Nhấp đúp chuột** vào tệp **`TikTok Transcript Extractor.app`** để khởi chạy.
2.  **Hệ thống tự động setup ngầm (Self-installing)**: 
    *   Ứng dụng sẽ tự động kiểm tra và tạo môi trường ảo Python `venv` trong thư mục gốc.
    *   Tự động chạy `pip install` để cài đặt ngầm tất cả thư viện AI cần thiết (`Flask`, `yt-dlp`, `openai-whisper`...) hoàn toàn ẩn dưới nền mà không cần mở Terminal.
3.  **Lưu ý duy nhất**: Máy Mac cần cài đặt sẵn lệnh `python3`. Nếu máy mới chưa từng cài bao giờ, hệ thống macOS sẽ hiển thị hộp thoại hỏi *"Bạn có muốn cài đặt Command Line Tools không?"* -> chỉ cần bấm **"Install"** đồng ý, hệ thống sẽ tự tải trong 30 giây và app hoạt động trơn tru vĩnh viễn!

---

### 💻 2. Dành cho Nhà phát triển (Developer)

Yêu cầu môi trường: **Node.js, pnpm, Rust/Cargo, Python 3**.

#### Khởi chạy chế độ Development:
```bash
# 1. Cài đặt các thư viện Node.js và CLI
pnpm install

# 2. Khởi chạy ứng dụng trong môi trường dev
pnpm tauri dev
```

#### Biên dịch và Đóng gói Release (.app và .dmg):
```bash
# Đóng gói sản phẩm chính thức
pnpm tauri build
```
Các tệp đóng gói hoàn tất sẽ xuất hiện tại thư mục `src-tauri/target/release/bundle/`.

---

## 🛠️ Kiến Trúc Công Nghệ

*   **Tauri Desktop Framework (v1.5)**: Cung cấp Webview native Apple Webkit siêu nhẹ làm giao diện người dùng và lõi Rust backend điều phối hệ thống.
*   **Python 3 (Venv)**: Xử lý logic cào dữ liệu TikTok (`yt-dlp`), chuyển đổi giọng nói cục bộ (`openai-whisper`) và cầu nối API (`Flask` chạy trên cổng rảnh **`5005`** tránh xung đột AirPlay macOS).

---

*Copyright by Kien NEX Picture • Phiên bản v2.0*
