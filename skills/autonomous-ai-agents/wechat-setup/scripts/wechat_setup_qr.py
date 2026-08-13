# -*- coding: utf-8 -*-
"""Helper to display WeChat login QR code for iLink bot setup."""

import qrcode

def show_qr(data: str) -> None:
    qr = qrcode.QRCode(border=2)
    qr.add_data(data)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

if __name__ == "__main__":
    import sys
    data = sys.argv[1] if len(sys.argv) > 1 else ""
    show_qr(data)
