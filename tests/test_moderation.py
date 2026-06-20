from services.api.core.moderation import moderate_image_bytes, moderate_text


def test_text_ok():
    ok, _ = moderate_text("red lehenga for wedding")
    assert ok


def test_text_blocked():
    ok, reason = moderate_text("explicit nude photos")
    assert not ok
    assert reason


def test_image_valid_png_header():
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200
    ok, _ = moderate_image_bytes(png)
    assert ok
