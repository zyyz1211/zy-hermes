# -*- coding: utf-8 -*-
"""扫描指定路径下含 U+FFFD 替换符的乱码文件名（UTF-8 beta 模式期间固化的损坏名字）。

用法:
    python scan_mojibake_files.py [路径1] [路径2] ...
    不带参数时默认扫描: 桌面、开始菜单(用户+公共)、快速启动栏。
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_ROOTS = [
    os.path.join(os.path.expanduser('~'), 'Desktop'),
    os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu'),
    os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Microsoft', 'Internet Explorer', 'Quick Launch'),
    r'C:\ProgramData\Microsoft\Windows\Start Menu',
]

def scan(root):
    found = []
    if not os.path.isdir(root):
        return found
    for cur, dirs, files in os.walk(root):
        for n in dirs + files:
            if '\ufffd' in n:
                found.append(os.path.join(cur, n))
    return found

def main():
    roots = sys.argv[1:] or DEFAULT_ROOTS
    total = 0
    for r in roots:
        hits = scan(r)
        for h in hits:
            print(h)
        total += len(hits)
    print(f'扫描完成: {len(roots)} 个路径, 共发现 {total} 个乱码文件名', file=sys.stderr)
    return 1 if total else 0

if __name__ == '__main__':
    sys.exit(main())
