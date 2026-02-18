from pathlib import Path
from datetime import datetime

import qrcode

from core.utils import QR_DIR


def generate_qr(data: str) -> Path:
    filename = f"qr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
    path = QR_DIR / filename
    image = qrcode.make(data)
    image.save(path)
    return path
