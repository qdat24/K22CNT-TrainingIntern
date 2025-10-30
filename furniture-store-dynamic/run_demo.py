#!/usr/bin/env python3
"""
Script chạy demo nhanh cho website nội thất
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_flask():
    """Kiểm tra Flask đã cài đặt chưa"""
    try:
        import flask
        print("✓ Flask đã được cài đặt")
        return True
    except ImportError:
        print("✗ Flask chưa được cài đặt")
        return False

def install_flask():
    """Cài đặt Flask"""
    print("\n📦 Đang cài đặt Flask...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask==3.0.0", "Werkzeug==3.0.1"])
        print("✓ Cài đặt Flask thành công!")
        return True
    except:
        print("✗ Không thể cài đặt Flask")
        return False

def run_server():
    """Chạy Flask server"""
    print("\n🚀 Đang khởi động server...")
    print("📍 Website sẽ chạy tại: http://localhost:5000")
    print("⌨️  Nhấn Ctrl+C để dừng server\n")
    
    # Đợi 2 giây rồi mở trình duyệt
    time.sleep(2)
    print("🌐 Đang mở trình duyệt...")
    webbrowser.open('http://localhost:5000')
    
    # Chạy Flask app
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

def main():
    print("=" * 50)
    print("🪑 WEBSITE THƯƠNG MẠI ĐIỆN TỬ NỘI THẤT")
    print("=" * 50)
    print()
    
    # Kiểm tra Flask
    if not check_flask():
        response = input("Bạn có muốn cài đặt Flask không? (y/n): ")
        if response.lower() == 'y':
            if not install_flask():
                print("\n⚠️  Vui lòng cài đặt Flask thủ công: pip install Flask")
                return
        else:
            print("\n⚠️  Cần cài Flask để chạy website")
            print("Chạy lệnh: pip install Flask")
            return
    
    # Chạy server
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n\n👋 Đã dừng server. Tạm biệt!")
    except Exception as e:
        print(f"\n⚠️  Lỗi: {e}")

if __name__ == "__main__":
    main()
