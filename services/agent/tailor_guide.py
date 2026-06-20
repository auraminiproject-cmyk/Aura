from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


async def generate_tailoring_guide(
    *,
    garment_type: str,
    fabric: str,
    measurements: dict,
    occasion: str | None = None,
) -> bytes:
    """Generate PDF tailoring guide with yardage and construction steps."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 50

    def line(text: str, size: int = 11):
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(50, y, text[:90])
        y -= 18

    line("Fashion AI — Tailoring Guide", 16)
    line(f"Garment: {garment_type}")
    line(f"Fabric: {fabric}")
    if occasion:
        line(f"Occasion: {occasion}")
    line("Measurements (cm):")
    for k, v in measurements.items():
        line(f"  {k}: {v}")

    chest = measurements.get("chest_cm", 88)
    waist = measurements.get("waist_cm", 72)
    yardage = round((chest + waist) / 100 * 2.5, 1)
    line(f"Estimated yardage: {yardage} meters")

    line("Construction steps:")
    steps = [
        "1. Prewash fabric; press with recommended heat.",
        "2. Draft pattern using body measurements (+2cm ease).",
        "3. Cut main panels; mark grain line and notches.",
        "4. Sew darts and side seams; finish raw edges.",
        "5. Attach lining; hem to length; final press.",
    ]
    for step in steps:
        line(step)

    c.showPage()
    c.save()
    return buf.getvalue()
