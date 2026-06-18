"""Build a downloadable PDF trip plan from an itinerary dict (ReportLab).

Page 1 is a designed cover (full-bleed cropped hero banner + centered title +
footer) drawn directly on the canvas; the plan starts on page 2. Uses a bundled
Unicode font (DejaVu Sans) so ₹/€/£/¥ render. Images are fetched server-side.
"""
from __future__ import annotations

import html
import os
from io import BytesIO
from typing import Any, Dict, List, Optional

import requests
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, Image as RLImage, KeepTogether,
                                PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

_UA = {"User-Agent": "VoyageMind/1.0 (travel assistant)"}
_BLUE = colors.HexColor("#2563eb")
_LIGHT = colors.HexColor("#eef2ff")
_ZEBRA = colors.HexColor("#f8fafc")
_GREY = colors.HexColor("#e5e7eb")
_DARK = colors.HexColor("#374151")
_MUTED = colors.HexColor("#6b7280")

_FONT, _FONT_B = "Helvetica", "Helvetica-Bold"
try:
    _fd = os.path.join(os.path.dirname(__file__), "fonts")
    pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(_fd, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(_fd, "DejaVuSans-Bold.ttf")))
    _FONT, _FONT_B = "DejaVu", "DejaVu-Bold"
except Exception:
    pass


def _esc(s: Any) -> str:
    return html.escape(str(s if s is not None else ""), quote=False)


def _cover_banner(url: str, ratio: float) -> Optional[ImageReader]:
    """Fetch + centre-crop the hero to `ratio` (w/h) for a full-bleed banner."""
    if not url:
        return None
    try:
        from PIL import Image as PILImage

        r = requests.get(url, headers=_UA, timeout=12)
        if r.status_code != 200:
            return None
        im = PILImage.open(BytesIO(r.content)).convert("RGB")
        iw, ih = im.size
        cur = iw / ih
        if cur > ratio:  # too wide → crop sides
            nw = int(ih * ratio)
            x = (iw - nw) // 2
            im = im.crop((x, 0, x + nw, ih))
        else:            # too tall → crop top/bottom
            nh = int(iw / ratio)
            y = (ih - nh) // 2
            im = im.crop((0, y, iw, y + nh))
        buf = BytesIO()
        im.save(buf, "JPEG", quality=85)
        buf.seek(0)
        return ImageReader(buf)
    except Exception:
        return None


def _fetch_image(url: str, max_w: float, max_h: Optional[float] = None) -> Optional[RLImage]:
    if not url:
        return None
    try:
        from PIL import Image as PILImage

        r = requests.get(url, headers=_UA, timeout=12)
        if r.status_code != 200:
            return None
        im = PILImage.open(BytesIO(r.content)).convert("RGB")
        iw, ih = im.size
        buf = BytesIO()
        im.save(buf, "JPEG", quality=80)
        buf.seek(0)
        w, h = max_w, max_w * ih / iw
        if max_h and h > max_h:
            h, w = max_h, max_h * iw / ih
        return RLImage(buf, width=w, height=h)
    except Exception:
        return None


def _map_image(center, places: List[Dict[str, Any]], max_w: float) -> Optional[RLImage]:
    try:
        from staticmap import CircleMarker, Line, StaticMap

        m = StaticMap(640, 360, url_template="https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        coords = [(p["lon"], p["lat"]) for p in places
                  if p.get("lat") is not None and p.get("lon") is not None]
        if len(coords) >= 2:
            m.add_line(Line(coords, "#2563eb", 3))
        for c in coords:
            m.add_marker(CircleMarker(c, "#2563eb", 14))
            m.add_marker(CircleMarker(c, "white", 7))
        if not coords and center and center[0] is not None:
            m.add_marker(CircleMarker((center[1], center[0]), "#2563eb", 14))
        img = m.render()
        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return RLImage(buf, width=max_w, height=max_w * 360 / 640)
    except Exception:
        return None


def _table(data, col_widths, header=True, total_row=False) -> Table:
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    style = [
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, _GREY),
    ]
    first = 1 if header else 0
    style.append(("ROWBACKGROUNDS", (0, first), (-1, -1), [colors.white, _ZEBRA]))
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), _BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_B),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ]
    if total_row:
        style += [
            ("FONTNAME", (0, -1), (-1, -1), _FONT_B),
            ("BACKGROUND", (0, -1), (-1, -1), _LIGHT),
        ]
    t.setStyle(TableStyle(style))
    return t


def build_pdf(it: Dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, title="VoyageMind Trip Plan",
    )
    base = getSampleStyleSheet()
    H2 = ParagraphStyle("H2", parent=base["Heading2"], fontName=_FONT_B, fontSize=15,
                        textColor=_BLUE, spaceBefore=2, spaceAfter=4)
    body = ParagraphStyle("body", parent=base["Normal"], fontName=_FONT, fontSize=10, leading=16)
    small = ParagraphStyle("small", parent=base["Normal"], fontName=_FONT, fontSize=8,
                           textColor=colors.grey, leading=12)

    cur = it.get("currency") or {}
    sym = cur.get("symbol", "$")

    def money(v) -> str:
        try:
            return f"{sym}{round(float(v)):,}"
        except Exception:
            return f"{sym}0"

    prefs = it.get("preferences") or {}
    dest = (it.get("destination") or {}).get("name", "Your Trip")
    dest_title = dest.split(",")[0].strip() or "Your Trip"
    cw = doc.width

    # ── cover assets ──
    W, H = A4
    band_h = H * 0.46
    banner = _cover_banner((it.get("destination") or {}).get("image"), W / band_h)
    bits = []
    if prefs.get("nights"):
        bits.append(f"{prefs['nights']} nights")
    if prefs.get("travelers"):
        bits.append(f"{prefs['travelers']} traveller(s)")
    if prefs.get("style"):
        bits.append(f"{prefs['style']} style")
    if prefs.get("start_date"):
        bits.append(f"from {prefs['start_date']}")
    subtitle = "  ·  ".join(bits)
    flag = (it.get("logistics") or {}).get("flag", "")

    def draw_cover(c, _doc):
        # full-bleed banner
        if banner is not None:
            c.drawImage(banner, 0, H - band_h, width=W, height=band_h, mask="auto")
        else:
            c.setFillColor(_BLUE)
            c.rect(0, H - band_h, W, band_h, fill=1, stroke=0)
        # accent strip
        c.setFillColor(_BLUE)
        c.rect(0, H - band_h - 6, W, 6, fill=1, stroke=0)
        # title block
        ty = H - band_h - 78
        c.setFillColor(_BLUE)
        c.setFont(_FONT_B, 34)
        c.drawCentredString(W / 2, ty, f"Trip to {dest_title}")
        if flag:
            c.setFont(_FONT, 22)
            c.setFillColor(_DARK)
            c.drawCentredString(W / 2, ty - 34, flag)
        if subtitle:
            c.setFont(_FONT, 13)
            c.setFillColor(_DARK)
            c.drawCentredString(W / 2, ty - (62 if flag else 30), subtitle)
        c.setFont(_FONT, 11)
        c.setFillColor(_MUTED)
        c.drawCentredString(W / 2, ty - (92 if flag else 60),
                            "Your personalised, AI-planned itinerary")
        # divider
        c.setStrokeColor(_GREY)
        c.setLineWidth(1)
        c.line(W / 2 - 55, ty - (112 if flag else 80), W / 2 + 55, ty - (112 if flag else 80))
        # footer pinned to the bottom
        c.setStrokeColor(_GREY)
        c.setLineWidth(0.5)
        c.line(2 * cm, 2.1 * cm, W - 2 * cm, 2.1 * cm)
        c.setFont(_FONT_B, 10)
        c.setFillColor(_BLUE)
        c.drawCentredString(W / 2, 1.55 * cm, "VoyageMind")
        c.setFont(_FONT, 8)
        c.setFillColor(colors.grey)
        c.drawCentredString(W / 2, 1.15 * cm, "Multi-agent travel assistant · fares & rates are estimates")

    def draw_footer(c, _doc):
        c.setStrokeColor(_GREY)
        c.setLineWidth(0.5)
        c.line(2 * cm, 1.3 * cm, W - 2 * cm, 1.3 * cm)
        c.setFont(_FONT, 8)
        c.setFillColor(colors.grey)
        c.drawString(2 * cm, 0.95 * cm, "VoyageMind")
        c.drawRightString(W - 2 * cm, 0.95 * cm, f"Page {_doc.page - 1}")

    # ── story (starts on page 2) ──
    story: List[Any] = [PageBreak()]

    def section(heading: str, *flowables) -> None:
        block = [
            Paragraph(heading, H2),
            HRFlowable(width="100%", thickness=1, color=_GREY, spaceBefore=2, spaceAfter=8),
            *[f for f in flowables if f is not None],
        ]
        story.append(KeepTogether(block))
        story.append(Spacer(1, 0.7 * cm))

    b = it.get("budget") or {}
    weather = it.get("weather") or {}

    overview_flow: List[Any] = []
    if it.get("summary"):
        overview_flow.append(Paragraph(_esc(it["summary"]), body))
        overview_flow.append(Spacer(1, 0.4 * cm))
    rows = []
    if prefs.get("style"):
        rows.append(["Style", _esc(str(prefs["style"]).title())])
    if prefs.get("nights"):
        rows.append(["Duration", f"{prefs['nights']} nights"])
    if prefs.get("travelers"):
        rows.append(["Travellers", str(prefs["travelers"])])
    if b.get("total") is not None:
        rows.append(["Estimated cost",
                     money(b["total"]) + (f"   /   {money(b['target'])} budget" if b.get("target") else "")])
    if weather.get("avg_high_c") is not None:
        rows.append(["Avg high", f"{round(weather['avg_high_c'])}°C"])
    if rows:
        overview_flow.append(_table(rows, [cw * 0.32, cw * 0.68], header=False))
    if overview_flow:
        section("Overview", *overview_flow)

    geo = (it.get("destination") or {}).get("geo") or {}
    center = (geo.get("lat"), geo.get("lon")) if geo.get("lat") is not None else None
    places = (it.get("activities") or {}).get("pois") or []
    if center:
        mimg = _map_image(center, places, cw)
        if mimg:
            section("Map", mimg)

    if weather.get("available"):
        section("Weather", Paragraph(_esc(weather.get("summary", "")), body))

    plan = (it.get("activities") or {}).get("plan") or []
    if plan:
        data = [["Day", "Morning", "Afternoon", "Evening"]]
        for d in plan:
            data.append([
                str(d.get("day", "")),
                Paragraph(_esc(d.get("morning", "")), body),
                Paragraph(_esc(d.get("afternoon", "")), body),
                Paragraph(_esc(d.get("evening", "")), body),
            ])
        three = (cw - 1.2 * cm) / 3
        section("Day-by-day itinerary", _table(data, [1.2 * cm, three, three, three]))

    if places:
        lines = []
        for i, p in enumerate(places[:6], 1):
            line = f"<b>{i}. {_esc(p.get('name', ''))}</b>"
            if p.get("tag"):
                line += f" — {_esc(p['tag'])}"
            if p.get("category"):
                line += f"  ({_esc(p['category'])})"
            lines.append(Paragraph(line, body))
            lines.append(Spacer(1, 0.15 * cm))
        section("Top attractions", *lines)

    hotels = it.get("hotels") or {}
    if hotels.get("available") and hotels.get("options"):
        data = [["Hotel", "Per night", "Total"]]
        for h in hotels["options"][:5]:
            data.append([Paragraph(_esc(h.get("name", "")), body),
                         money(h.get("nightly_rate")), money(h.get("total_price"))])
        section("Hotels", _table(data, [cw * 0.5, cw * 0.25, cw * 0.25]),
                Paragraph("Rates are estimates.", small))

    flights = it.get("flights") or {}
    if flights.get("available") and flights.get("options"):
        data = [["Airline", "Price (est.)"]]
        for f in flights["options"][:3]:
            data.append([Paragraph(_esc(f.get("airline", "")), body), money(f.get("total_price"))])
        section(f"Flights · {_esc(flights.get('route', ''))}", _table(data, [cw * 0.65, cw * 0.35]))

    if b.get("breakdown"):
        data = [["Item", "Cost"]]
        for k, v in b["breakdown"].items():
            data.append([_esc(k.replace("_", " ").title()), money(v)])
        data.append(["Total", money(b.get("total"))])
        section("Budget (estimated)", _table(data, [cw * 0.6, cw * 0.4], total_row=True))

    logi = it.get("logistics") or {}
    if logi.get("available"):
        section("Local info", Paragraph(_esc(logi.get("summary", "")), body))

    doc.build(story, onFirstPage=draw_cover, onLaterPages=draw_footer)
    return buf.getvalue()
