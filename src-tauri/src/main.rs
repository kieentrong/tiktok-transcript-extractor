#![cfg_attr(
  all(not(debug_assertions), target_os = "windows"),
  windows_subsystem = "windows"
)]

use std::path::{Path, PathBuf};
use std::process::{Command, Stdio, Child};
use std::sync::Mutex;
use std::net::TcpStream;
use std::time::Duration;
use std::thread;
use std::env;

// Biến tĩnh lưu child process của Flask server để tự động kill khi thoát app
static FLASK_CHILD: Mutex<Option<Child>> = Mutex::new(None);

/// Duyệt tìm thư mục gốc của dự án chứa file app.py và venv
fn find_project_root() -> Option<PathBuf> {
    // 1. Thử tìm tương đối từ file thực thi hiện tại (hữu dụng khi chạy app đóng gói .app)
    if let Ok(exe_path) = env::current_exe() {
        let mut dir = exe_path.parent();
        while let Some(path) = dir {
            if path.join("app.py").exists() {
                return Some(path.to_path_buf());
            }
            dir = path.parent();
        }
    }
    // 2. Thử tìm từ thư mục làm việc hiện tại
    if let Ok(cwd) = env::current_dir() {
        let mut dir = Some(cwd.as_path());
        while let Some(path) = dir {
            if path.join("app.py").exists() {
                return Some(path.to_path_buf());
            }
            dir = path.parent();
        }
    }
    None
}

/// Kiểm tra xem cổng TCP có đang mở (phục vụ kết nối) hay không
fn is_port_ready(port: u16) -> bool {
    let addr = format!("127.0.0.1:{}", port);
    TcpStream::connect(&addr).is_ok()
}

/// Chờ cho đến khi cổng TCP sẵn sàng (tối đa 15 giây)
fn wait_for_port(port: u16, max_attempts: usize) -> bool {
    for _ in 0..max_attempts {
        if is_port_ready(port) {
            return true;
        }
        thread::sleep(Duration::from_millis(150));
    }
    false
}

/// Tự động thiết lập môi trường ảo venv và cài đặt thư viện cần thiết nếu chưa có
fn setup_environment(project_root: &Path) -> Result<(), String> {
    let venv_dir = project_root.join("venv");
    if !venv_dir.exists() {
        println!("👉 Không tìm thấy môi trường ảo venv. Bắt đầu tự động thiết lập...");
        
        // 1. Tạo venv bằng python3
        let status = Command::new("python3")
            .args(&["-m", "venv", "venv"])
            .current_dir(project_root)
            .status()
            .map_err(|e| format!("Không thể chạy python3 để tạo venv. Lỗi: {}", e))?;
            
        if !status.success() {
            return Err("Tạo môi trường ảo venv thất bại. Vui lòng đảm bảo python3 được cài đặt.".to_string());
        }
        
        println!("👉 Đang cài đặt các thư viện cần thiết qua pip (Flask, yt-dlp, whisper...)...");
        // 2. Cài đặt các thư viện bằng pip của venv
        let pip_path = venv_dir.join("bin").join("pip");
        let status = Command::new(pip_path)
            .args(&[
                "install", 
                "flask", 
                "yt-dlp", 
                "openai-whisper", 
                "static-ffmpeg", 
                "soundfile"
            ])
            .current_dir(project_root)
            .status()
            .map_err(|e| format!("Lỗi khi chạy pip install. Chi tiết: {}", e))?;
            
        if !status.success() {
            return Err("Cài đặt các gói thư viện Python thất bại.".to_string());
        }
        println!("🚀 Thiết lập môi trường ảo venv thành công!");
    }
    Ok(())
}

fn main() {
    let project_root = find_project_root().expect("❌ Lỗi nghiêm trọng: Không thể tìm thấy thư mục gốc chứa file app.py!");
    println!("📂 Đã phát hiện thư mục gốc dự án: {:?}", project_root);

    // 1. Tự động thiết lập môi trường nếu chưa có
    if let Err(e) = setup_environment(&project_root) {
        eprintln!("⚠️ Cảnh báo thiết lập môi trường ảo: {}", e);
    }

    // 2. Khởi chạy ngầm Flask server
    let python_path = project_root.join("venv").join("bin").join("python");
    let app_path = project_root.join("app.py");

    println!("📡 Đang khởi động Flask Server cục bộ từ venv...");
    let child = Command::new(python_path)
        .arg(app_path)
        .current_dir(&project_root)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn();

    match child {
        Ok(child_proc) => {
            // Lưu giữ tiến trình Flask trong biến tĩnh
            if let Ok(mut lock) = FLASK_CHILD.lock() {
                *lock = Some(child_proc);
            }
            println!("📡 Tiến trình Flask Server đã được khởi chạy ngầm.");
        }
        Err(e) => {
            eprintln!("❌ Lỗi khi khởi chạy Flask server: {}", e);
        }
    }

    // 3. Đợi Flask Server khởi động và sẵn sàng nhận kết nối trên cổng 5005 (TCP ready)
    println!("⏳ Đang kiểm tra trạng thái cổng 5005...");
    if wait_for_port(5005, 100) {
        println!("✅ Flask Server đã sẵn sàng nhận kết nối tại http://127.0.0.1:5005");
    } else {
        eprintln!("⚠️ Cảnh báo: Đã quá thời gian chờ nhưng Flask Server chưa phản hồi.");
    }

    // 4. Khởi động giao diện ứng dụng Tauri native
    let app = tauri::Builder::default()
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    // 5. Đăng ký bộ lắng nghe sự kiện thoát của Tauri để tắt sạch Flask Server chạy ngầm
    app.run(|_app_handle, event| match event {
        tauri::RunEvent::Exit => {
            println!("👋 Ứng dụng Tauri đang đóng. Đang dọn dẹp và tắt Flask Server...");
            if let Ok(mut lock) = FLASK_CHILD.lock() {
                if let Some(ref mut child_proc) = *lock {
                    match child_proc.kill() {
                        Ok(_) => println!("✅ Đã tắt Flask Server chạy ngầm thành công. Giải phóng tài nguyên!"),
                        Err(e) => eprintln!("❌ Không thể tắt Flask Server: {}", e),
                    }
                }
            }
        }
        _ => {}
    });
}
