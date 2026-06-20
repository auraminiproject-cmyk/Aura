"""Image validation, resize, EXIF strip — blueprint Phase 5."""

import io

from PIL import Image


def compress_image(data: bytes, max_px: int = 800, quality: int = 85) -> bytes:
    img = Image.open(io.BytesIO(data))
    img.load()
    img_without_exif = Image.new(img.mode, img.size)
    img_without_exif.putdata(list(img.getdata()))
    img_without_exif.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    fmt = "JPEG" if img.format != "PNG" else "PNG"
    save_kw = {"quality": quality, "optimize": True} if fmt == "JPEG" else {}
    img_without_exif.save(buf, format=fmt, **save_kw)
    return buf.getvalue()


def blur_score(data: bytes) -> float:
    import numpy as np

    img = Image.open(io.BytesIO(data)).convert("L")
    arr = np.array(img, dtype=float)
    return float(arr.var())


def brightness_score(data: bytes) -> float:
    img = Image.open(io.BytesIO(data)).convert("L")
    return sum(img.getdata()) / (img.size[0] * img.size[1])
