# Backup & Context

## 2026-05-28 - Tiếp quản ban đầu

### Yêu cầu người dùng
- Luôn trả lời bằng tiếng Việt.
- Luôn lưu lại thông tin sửa đổi vào file `Backup&context.md`.
- Đọc dự án và tóm tắt dự án đang làm gì để người dùng bổ sung thông tin.

### Tổng quan dự án
- Tên sản phẩm: TikTok Transcript Extractor - NEX Picture Desktop Studio.
- Mục tiêu: ứng dụng macOS/desktop để quét một kênh TikTok, lấy danh sách video, tải phụ đề tiếng Việt gốc nếu có, hoặc dùng Whisper local để chuyển giọng nói thành transcript.
- Kết quả đầu ra: file `.txt` sạch trong `transcripts/`, danh sách video trong `videos.json`, báo cáo tổng hợp trong `summary.md`.

### Kiến trúc hiện tại
- `app.py`: Flask server chạy local ở `127.0.0.1:5005`, cung cấp giao diện web, API quét kênh, API dừng, mở thư mục kết quả và stream tiến trình bằng SSE.
- `templates/index.html`: giao diện single-page app, gọi API Flask qua `fetch` và `EventSource`, hiển thị log, progress bar, thống kê phụ đề gốc/Whisper/đã có sẵn/lỗi.
- `download_and_parse.py`: logic dùng `yt-dlp`, dọn WebVTT, tải audio, chạy `openai-whisper`, lưu transcript và sinh báo cáo. Đây cũng là module được `app.py` import.
- `get_all_videos.py`: script cũ/quy trình CLI để quét danh sách video của kênh hard-code.
- `run_app.py`: launcher kiểu web/Chrome app mode, chạy Flask bằng Python trong `venv`.
- `src-tauri/src/main.rs`: Rust/Tauri wrapper, tự tìm project root, tạo `venv` nếu thiếu, cài Python dependencies, chạy Flask ngầm, chờ port 5005, mở webview Tauri, kill Flask khi thoát.
- `src-tauri/tauri.conf.json`: cấu hình Tauri v1, app window 980x800, bundle `.app` và `.dmg`.

### Trạng thái repo/dữ liệu
- Nhánh Git hiện tại: `main`, tracking `origin/main`.
- File Git quản lý chính: Python backend, HTML template, Tauri/Rust config/source, README, lockfiles, assets/icon.
- `.gitignore` đang loại trừ `venv/`, `node_modules/`, `src-tauri/target/`, `transcripts/`, `temp_audio/`, `videos.json`, `summary.md`, `.dmg`, `.app`.
- Dữ liệu local hiện có: `videos.json` gồm 108 video; thư mục `transcripts/` hiện có 211 file `.txt`; `summary.md` ghi một lần chạy GUI với 108 video, 15 video đã xử lý thành công, 0 lỗi.

### Điểm kỹ thuật cần chú ý
- `download_and_parse.py` đang hard-code `BASE_DIR = '/Users/kientrong/Desktop/Antigravity/Kien'`; nếu đổi máy/thư mục sẽ dễ lỗi. `app.py` thì đã tính `BASE_DIR` động.
- Version chưa đồng bộ: `README.md`, `package.json`, `tauri.conf.json` ghi `3.1.5`, nhưng `src-tauri/Cargo.toml` ghi package version `3.0.0`.
- `get_all_videos.py` còn hard-code kênh `https://www.tiktok.com/@khoang.lang.cuocsong`, trong khi UI mặc định là `@kieentrong`.
- Tauri wrapper tự `pip install` nhiều gói nặng (`openai-whisper`, torch dependency qua Whisper); lần chạy đầu có thể lâu và phụ thuộc mạng/Python/CPU.
- Frontend gọi API bằng endpoint tuyệt đối `http://127.0.0.1:5005`, phù hợp với Tauri production webview theo README.

### Thay đổi đã thực hiện trong lượt này
- Tạo file `Backup&context.md` để lưu bối cảnh tiếp quản ban đầu.
- Chưa sửa logic ứng dụng, chưa chạy build/test, chưa khởi động server.

## 2026-05-28 - Bổ sung định hướng và sửa nền tảng

### Thông tin người dùng bổ sung
- App cần dùng linh hoạt cho mọi kênh TikTok, không chỉ một kênh cố định.
- Người dùng muốn xem xét khả năng phát triển thành Chrome extension để dễ phát hành.
- Không cần giữ dữ liệu local hiện tại như một yêu cầu sản phẩm.
- Đồng ý sửa các điểm kỹ thuật lệch: hard-code đường dẫn/kênh và version không đồng bộ.

### Thay đổi đã thực hiện
- `download_and_parse.py`: đổi `BASE_DIR` từ đường dẫn hard-code `/Users/kientrong/Desktop/Antigravity/Kien` sang đường dẫn động theo vị trí file.
- `get_all_videos.py`: bỏ kênh hard-code, thêm tham số dòng lệnh nhận URL hoặc username dạng `@username`, và cho phép chỉ định file output bằng `-o/--output`.
- `src-tauri/Cargo.toml`: đồng bộ version package Rust từ `3.0.0` lên `3.1.5`.

### Ghi chú định hướng Chrome extension
- Có thể phát triển thành Chrome extension, nhưng không nên bê nguyên kiến trúc hiện tại sang extension vì extension không thể chạy trực tiếp Python/Whisper local/yt-dlp như desktop app.
- Hướng khả thi: extension chỉ làm UI + lấy URL/kênh từ tab TikTok, còn xử lý cào transcript chạy ở backend local hoặc cloud API.
- Nếu muốn dễ phát hành nhất: chuyển phần xử lý nặng sang server/API, extension chỉ gửi job và hiển thị tiến trình/kết quả.

## 2026-05-28 - Đánh giá backend free cho Chrome extension

### Kết luận
- Có thể làm backend free cho MVP/demo, nhưng khó free bền vững nếu chạy Whisper local trên cloud vì transcribe audio cần CPU/RAM/thời gian xử lý lớn.
- Phương án free thực tế nhất: giữ xử lý nặng ở máy người dùng bằng local companion app/Tauri, còn Chrome extension chỉ điều khiển và lấy URL.
- Phương án cloud free khả thi cho demo: Render Free hoặc Hugging Face Spaces CPU, nhưng có giới hạn ngủ máy/quota/tốc độ và không phù hợp nếu nhiều người dùng chạy cùng lúc.

### Gợi ý kiến trúc
- MVP miễn phí ổn định nhất: Chrome extension + local backend `127.0.0.1:5005` dùng code Flask hiện tại.
- MVP dễ demo online: Chrome extension + backend Render/Hugging Face Spaces, chỉ xử lý phụ đề gốc trước; Whisper nên để tùy chọn hoặc xử lý local.
- Sản phẩm phát hành rộng: extension + cloud backend trả phí nhỏ, có hàng đợi job, giới hạn quota người dùng, lưu kết quả tạm thời.

## 2026-05-28 - Sửa lỗi app bị hỏng/không chạy trên máy khác

### Chẩn đoán
- Bundle `.app` hiện có chỉ chứa binary Tauri và `icon.icns`, không chứa `app.py`, `download_and_parse.py` hoặc `templates/`.
- Khi đem sang máy khác, Rust launcher không thể tìm backend Python để chạy Flask.
- App đang ký ad-hoc, chưa notarize Developer ID; nếu tải qua internet, macOS Gatekeeper vẫn có thể báo app bị hỏng/không mở được do quarantine.

### Thay đổi đã thực hiện
- `src-tauri/tauri.conf.json`: thêm Python backend files và `templates/` vào bundle resources.
- `src-tauri/src/main.rs`: khi chạy bản đóng gói, tìm backend trong `Contents/Resources`, copy sang `~/Library/Application Support/TikTok Transcript Extractor`, rồi tạo `venv`/chạy Flask ở thư mục runtime đó.
- Cách này tránh ghi vào bên trong `.app`, giảm nguy cơ phá bundle/code signing khi app nằm trong `/Applications`.
- Sau khi build thử, Tauri đặt resource từ đường dẫn `../...` vào `Contents/Resources/_up_/`; launcher đã được cập nhật để nhận diện cả thư mục này.

### Việc còn cần làm khi phát hành
- Build lại `.app`/`.dmg`.
- Ký app bằng Developer ID và notarize nếu muốn người dùng mở bình thường không cần lệnh phụ.
- Nếu chưa có Developer ID, người dùng có thể vẫn cần xóa quarantine hoặc mở bằng chuột phải > Open.
- README đã được cập nhật để phân biệt Apple Silicon/Intel, thêm lệnh `xattr -cr` cho bản test chưa notarize, và ghi chú yêu cầu notarization cho bản phát hành chính thức.
- Đã chạy `pnpm tauri build`; artifact mới nằm tại `src-tauri/target/release/bundle/macos/TikTok Transcript Extractor.app` và `src-tauri/target/release/bundle/dmg/TikTok Transcript Extractor_3.1.5_aarch64.dmg`.
- Đã chạy ad-hoc codesign lại trên `.app` trong `src-tauri/target/release/bundle/macos/` và verify hợp lệ trên disk. Đây vẫn chưa phải Developer ID notarization.
- Đã tạo thêm DMG test từ `.app` đã ad-hoc sign: `src-tauri/target/release/bundle/dmg/TikTok Transcript Extractor_3.1.5_aarch64_test-signed.dmg`.

## 2026-05-28 - Chuẩn bị release v3.1.6

### Thay đổi đã thực hiện
- Bump version từ `3.1.5` lên `3.1.6` trong `README.md`, `package.json`, `src-tauri/Cargo.toml`, `src-tauri/Cargo.lock` và `src-tauri/tauri.conf.json`.
- Thêm dòng changelog `v3.1.6` vào README cho lỗi app bị báo hỏng/không chạy trên máy khác.

### Ghi chú phát hành
- Máy hiện chỉ có Rust target `aarch64-apple-darwin`, nên bản release trước mắt là Apple Silicon.
- Nếu cần hỗ trợ Mac Intel, cần cài target `x86_64-apple-darwin` và build thêm artifact riêng hoặc universal binary.
- Khi build v3.1.6, bước DMG của Tauri bị kẹt do volume tạm `/Volumes/TikTok Transcript Extractor` còn mount. Đã force detach `/dev/disk6`, ký ad-hoc lại `.app`, rồi tạo DMG mới bằng `hdiutil create`.
- Artifact release v3.1.6: `src-tauri/target/release/bundle/dmg/TikTok Transcript Extractor_3.1.6_aarch64.dmg`.
