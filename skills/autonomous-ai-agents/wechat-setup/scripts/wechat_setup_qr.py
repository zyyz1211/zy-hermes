# coding:utf-8
"""
Hermes WeChat (Weixin) QR Code Setup Helper

Automates the interactive `hermes gateway setup` wizard for WeChat:
1. Pipes input to select WeChat and start QR login
2. Captures the QR URL from stdout in real time
3. Generates a QR code image on the desktop for the user to scan
4. Auto-refreshes the image if the QR code expires
5. Keeps the process alive until the user scans successfully

Usage:
    python scripts/wechat_setup_qr.py

The QR code image is saved to ~/Desktop/wechat_qrcode.png.
"""
import subprocess
import re
import os
import sys
import time


def main():
    proc = subprocess.Popen(
        ['hermes', 'gateway', 'setup'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Select Weixin (option 3) and confirm QR login
    proc.stdin.write("3\n")
    proc.stdin.flush()
    time.sleep(1)
    proc.stdin.write("y\n")
    proc.stdin.flush()

    qr_url = None
    desktop = os.path.expanduser('~/Desktop/wechat_qrcode.png')

    print("等待二维码URL...")
    while True:
        line = proc.stdout.readline()
        if not line:
            break

        print(line, end='', flush=True)

        # Capture initial QR URL
        if not qr_url:
            m = re.search(r'(https://liteapp\.weixin\.qq\.com/q/[^\s\)]+)', line)
            if m:
                qr_url = m.group(1).strip()
                _generate_qr(qr_url, desktop)
                print(f"\n{'='*60}")
                print(f"✅ 二维码已保存到桌面: {desktop}")
                print(f"✅ 请用手机微信扫描二维码!")
                print(f"{'='*60}\n")

        # Update QR code on expiry refresh
        if qr_url and '正在刷新' in line:
            m = re.search(r'(https://liteapp\.weixin\.qq\.com/q/[^\s\)]+)', line)
            if m:
                new_url = m.group(1).strip()
                if new_url != qr_url:
                    qr_url = new_url
                    _generate_qr(qr_url, desktop)
                    print(f"\n🔄 二维码已刷新，请重新扫描!\n")

        # Setup complete
        if '连接成功' in line or 'account_id' in line:
            print(f"\n🎉 微信配置成功！账号信息已保存！")
            break

    proc.wait()
    print(f"\n进程退出码: {proc.returncode}")


def _generate_qr(url: str, save_path: str):
    """Generate a QR code image from URL and save it."""
    try:
        import qrcode
        img = qrcode.make(url)
        img.save(save_path)
    except ImportError:
        print(f"⚠ qrcode 模块未安装，请手动打开链接:\n{url}")
        print("安装: pip install qrcode[pil]")


if __name__ == '__main__':
    main()
