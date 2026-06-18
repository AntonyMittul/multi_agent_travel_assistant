"""Build a downloadable PDF trip plan from an itinerary dict (ReportLab).

Images are fetched server-side (no browser CORS issues) and the map is rendered
from OSM tiles via staticmap. Every image/map step degrades gracefully — if a
fetch fails, that piece is simply omitted and the PDF still builds.
"""
from __future__ import annotations

import html
from io import BytesIO
from typing import Any, Dict, List, Optional

import requests
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image as RLImage, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

_UA = {"User-Agent": "VoyageMind/1.0 (travel assistant)"}
_BLUE = colors.HexColor("#2563eb")
_LIGHT = colors.HexColor("#eef2ff")
_GREY = colors.HexColor("#e5e7eb")


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

        m = StaticMap(640, 380, url_template="https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
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
        return RLImage(buf, width=max_w, height=max_w * 380 / 640)
    except Exception:
        return None


def _table(data, col_widths, header=True, total_row=False) -> Table:
    t = Table(data, colWidths=col_widths)
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, _GREY),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), _BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    if total_row:
        style += [
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), _LIGHT),
        ]
    t.setStyle(TableStyle(style))
    return t


def build_pdf(it: Dict[str, Any]) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm, title="VoyageMind Trip Plan",
    )
    base = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=base["Title"], fontSize=26, textColor=_BLUE, spaceAfter=4)
    H2 = ParagraphStyle("H2", parent=base["Heading2"], fontSize=14, textColor=_BLUE,
                        spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=15)
    small = ParagraphStyle("small", parent=base["Normal"], fontSize=8, textColor=colors.grey)
    centre = ParagraphStyle("centre", parent=body, alignment=TA_CENTER, fontSize=11)

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

    # ── cover ──
    hero = (it.get("destination") or {}).get("image")
    himg = _fetch_image(hero, cw, max_h=10 * cm)
    story.append(Spacer(1, 0.8 * cm))
    if himg:
        story.append(himg)
        story.append(Spacer(1, 0.6 * cm))
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
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Generated by VoyageMind — multi-agent travel assistant", small))
    story.append(PageBreak())

    # ── overview ──
    if it.get("summary"):
        story.append(Paragraph("Overview", H2))
        story.append(Paragraph(_esc(it["summary"]), body))

    b = it.get("budget") or {}
    weather = it.get("weather") or {}
    rows = []
    if prefs.get("style"):
        rows.append(["Style", _esc(str(prefs["style"]).title())])
    if prefs.get("nights"):
        rows.append(["Duration", f"{prefs['nights']} nights"])
    if prefs.get("travelers"):
        rows.append(["Travellers", str(prefs["travelers"])])
    if b.get("total") is not None:
        tot = money(b["total"]) + (f"  /  {money(b['target'])} budget" if b.get("target") else "")
        rows.append(["Estimated cost", tot])
    if weather.get("avg_high_c") is not None:
        rows.append(["Avg high", f"{round(weather['avg_high_c'])}°C"])
    if rows:
        story.append(Spacer(1, 0.3 * cm))
        story.append(_table(rows, [cw * 0.32, cw * 0.68], header=False))

    # ── map ──
    geo = (it.get("destination") or {}).get("geo") or {}
    center = (geo.get("lat"), geo.get("lon")) if geo.get("lat") is not None else None
    places = (it.get("activities") or {}).get("pois") or []
    if center:
        mimg = _map_image(center, places, cw)
        if mimg:
            story.append(Paragraph("Map", H2))
            story.append(mimg)

    # ── weather ──
    if weather.get("available"):
        story.append(Paragraph("Weather", H2))
        story.append(Paragraph(_esc(weather.get("summary", "")), body))

    # ── itinerary ──
    plan = (it.get("activities") or {}).get("plan") or []
    if plan:
        story.append(Paragraph("Day-by-day itinerary", H2))
        data = [["Day", "Morning", "Afternoon", "Evening"]]
        for d in plan:
            data.append([
                str(d.get("day", "")),
                Paragraph(_esc(d.get("morning", "")), body),
                Paragraph(_esc(d.get("afternoon", "")), body),
                Paragraph(_esc(d.get("evening", "")), body),
            ])
        three = (cw - 1 * cm) / 3
        story.append(_table(data, [1 * cm, three, three, three]))

    # ── attractions ──
    if places:
        story.append(Paragraph("Top attractions", H2))
        for i, p in enumerate(places[:6], 1):
            line = f"<b>{i}. {_esc(p.get('name', ''))}</b>"
            if p.get("tag"):
                line += f" — {_esc(p['tag'])}"
            if p.get("category"):
                line += f" ({_esc(p['category'])})"
            story.append(Paragraph(line, body))

    # ── hotels ──
    hotels = it.get("hotels") or {}
    if hotels.get("available") and hotels.get("options"):
        story.append(Paragraph("Hotels", H2))
        data = [["Hotel", "Per night", "Total"]]
        for h in hotels["options"][:5]:
            data.append([Paragraph(_esc(h.get("name", "")), body),
                         money(h.get("nightly_rate")), money(h.get("total_price"))])
        story.append(_table(data, [cw * 0.5, cw * 0.25, cw * 0.25]))
        story.append(Paragraph("Rates are estimates.", small))

    # ── flights ──
    flights = it.get("flights") or {}
    if flights.get("available") and flights.get("options"):
        story.append(Paragraph(f"Flights · {_esc(flights.get('route', ''))}", H2))
        data = [["Airline", "Price (est.)"]]
        for f in flights["options"][:3]:
            data.append([Paragraph(_esc(f.get("airline", "")), body), money(f.get("total_price"))])
        story.append(_table(data, [cw * 0.65, cw * 0.35]))

    # ── budget ──
    if b.get("breakdown"):
        story.append(Paragraph("Budget (estimated)", H2))
        data = [["Item", "Cost"]]
        for k, v in b["breakdown"].items():
            data.append([_esc(k.replace("_", " ").title()), money(v)])
        data.append(["Total", money(b.get("total"))])
        story.append(_table(data, [cw * 0.6, cw * 0.4], total_row=True))

    # ── local info ──
    logi = it.get("logistics") or {}
    if logi.get("available"):
        story.append(Paragraph("Local info", H2))
        story.append(Paragraph(_esc(logi.get("summary", "")), body))

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Flight fares and hotel rates are estimates. Generated by VoyageMind.", small))

    doc.build(story)
    return buf.getvalue()
