"""Build a downloadable PDF trip plan from an itinerary dict (ReportLab).

Uses a bundled Unicode font (DejaVu Sans) so currency symbols like ₹/€/£/¥
render correctly. Images are fetched server-side (no browser CORS) and the map
is rendered from OSM tiles; every image/map step degrades gracefully.
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

# Register the bundled Unicode font (falls back to Helvetica if missing).
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
    H1 = ParagraphStyle("H1", parent=base["Title"], fontName=_FONT_B, fontSize=30,
                        textColor=_BLUE, spaceAfter=6)
    H2 = ParagraphStyle("H2", parent=base["Heading2"], fontName=_FONT_B, fontSize=15,
                        textColor=_BLUE, spaceBefore=2, spaceAfter=4)
    body = ParagraphStyle("body", parent=base["Normal"], fontName=_FONT, fontSize=10, leading=16)
    small = ParagraphStyle("small", parent=base["Normal"], fontName=_FONT, fontSize=8,
                           textColor=colors.grey, leading=12)
    centre = ParagraphStyle("centre", parent=body, alignment=TA_CENTER, fontSize=12, leading=18)

    cur = it.get("currency") or {}
    sym = cur.get("symbol", "$")

    def money(v) -> str:
        try:
            return f"{sym}{round(float(v)):,}"
        except Exception:
            return f"{sym}0"

    prefs = it.get("preferences") or {}
    dest = (it.get("destination") or {}).get("name", "Your Trip")
    cw = doc.width
    story: List[Any] = []

    def section(heading: str, *flowables) -> None:
        """Add a section that stays together on one page."""
        block = [
            Paragraph(heading, H2),
            HRFlowable(width="100%", thickness=1, color=_GREY, spaceBefore=2, spaceAfter=8),
            *[f for f in flowables if f is not None],
        ]
        story.append(KeepTogether(block))
        story.append(Spacer(1, 0.7 * cm))

    # ── cover ──
    hero = (it.get("destination") or {}).get("image")
    himg = _fetch_image(hero, cw, max_h=11 * cm)
    story.append(Spacer(1, 1 * cm))
    if himg:
        story.append(himg)
        story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(f"Trip to {_esc(dest)}", H1))
    bits = []
    if prefs.get("nights"):
        bits.append(f"{prefs['nights']} nights")
    if prefs.get("travelers"):
        bits.append(f"{prefs['travelers']} traveller(s)")
    if prefs.get("style"):
        bits.append(f"{prefs['style']} style")
    if prefs.get("start_date"):
        bits.append(f"from {prefs['start_date']}")
    if bits:
        story.append(Paragraph(_esc(" · ".join(bits)), centre))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Generated by VoyageMind — multi-agent travel assistant", small))
    story.append(PageBreak())

    b = it.get("budget") or {}
    weather = it.get("weather") or {}

    # ── overview (summary + stats) ──
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

    # ── map ──
    geo = (it.get("destination") or {}).get("geo") or {}
    center = (geo.get("lat"), geo.get("lon")) if geo.get("lat") is not None else None
    places = (it.get("activities") or {}).get("pois") or []
    if center:
        mimg = _map_image(center, places, cw)
        if mimg:
            section("Map", mimg)

    # ── weather ──
    if weather.get("available"):
        section("Weather", Paragraph(_esc(weather.get("summary", "")), body))

    # ── itinerary ──
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

    # ── attractions ──
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

    # ── hotels ──
    hotels = it.get("hotels") or {}
    if hotels.get("available") and hotels.get("options"):
        data = [["Hotel", "Per night", "Total"]]
        for h in hotels["options"][:5]:
            data.append([Paragraph(_esc(h.get("name", "")), body),
                         money(h.get("nightly_rate")), money(h.get("total_price"))])
        section("Hotels", _table(data, [cw * 0.5, cw * 0.25, cw * 0.25]),
                Paragraph("Rates are estimates.", small))

    # ── flights ──
    flights = it.get("flights") or {}
    if flights.get("available") and flights.get("options"):
        data = [["Airline", "Price (est.)"]]
        for f in flights["options"][:3]:
            data.append([Paragraph(_esc(f.get("airline", "")), body), money(f.get("total_price"))])
        section(f"Flights · {_esc(flights.get('route', ''))}", _table(data, [cw * 0.65, cw * 0.35]))

    # ── budget ──
    if b.get("breakdown"):
        data = [["Item", "Cost"]]
        for k, v in b["breakdown"].items():
            data.append([_esc(k.replace("_", " ").title()), money(v)])
        data.append(["Total", money(b.get("total"))])
        section("Budget (estimated)", _table(data, [cw * 0.6, cw * 0.4], total_row=True))

    # ── local info ──
    logi = it.get("logistics") or {}
    if logi.get("available"):
        section("Local info", Paragraph(_esc(logi.get("summary", "")), body))

    story.append(Paragraph("Flight fares and hotel rates are estimates. Generated by VoyageMind.", small))

    doc.build(story)
    return buf.getvalue()
