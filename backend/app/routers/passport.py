"""
Passport presentation endpoints:
- GET /passport/{id} (JSON)
- GET /p/{id} (HTML web view)
- GET /passport/{id}/card.png (Share Card image 1080x1350)
"""

import io
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from PIL import Image, ImageDraw, ImageFont

from app.schemas import PassportResponse, VerdictEnum
from app.storage import get_passport
from app.routers.analyze import load_fixture
from app.strings import get_strings

router = APIRouter(tags=["Passport"])


def resolve_passport(passport_id: str) -> PassportResponse:
    passport = get_passport(passport_id)
    if passport:
        return passport

    # Fallback lookup for demo fixture IDs
    if "original" in passport_id:
        return load_fixture("original", new_id=passport_id)
    elif "modified" in passport_id:
        return load_fixture("modified", new_id=passport_id)
    elif "ai_confirmed" in passport_id:
        return load_fixture("ai_confirmed", new_id=passport_id)
    elif "likely_ai" in passport_id:
        return load_fixture("likely_ai", new_id=passport_id)
    elif "inconclusive" in passport_id:
        return load_fixture("inconclusive", new_id=passport_id)

    raise HTTPException(status_code=404, detail=f"Passport with ID '{passport_id}' not found")


@router.get("/passport/{id}", response_model=PassportResponse)
async def get_passport_json(id: str):
    """Returns the frozen-contract Passport JSON for a given ID."""
    return resolve_passport(id)


@router.get("/p/{id}", response_class=HTMLResponse)
async def get_passport_page(id: str, lang: Optional[str] = Query("en", pattern="^(en|hi)$")):
    """
    GET /p/{id}:
    Human-readable, mobile-friendly Passport page in English or Hindi.
    Used by iOS Shortcut, Telegram Bot links, and direct sharing.
    """
    passport = resolve_passport(id)
    strings = get_strings()
    
    is_hi = (lang == "hi")
    
    # Verdict style mappings (strict ladder colours: amber, orange, red ONLY for ai_confirmed, grey-blue, green)
    verdict_colors = {
        VerdictEnum.original: ("#107c41", "#dff6dd", "VERIFIED ORIGINAL"),
        VerdictEnum.modified: ("#b7791f", "#fef3c7", "MODIFIED / ALTERED"),
        VerdictEnum.out_of_context: ("#b7791f", "#fef3c7", "OUT OF CONTEXT"),
        VerdictEnum.ai_confirmed: ("#c53030", "#fed7d7", "AI-GENERATED (CONFIRMED)"),
        VerdictEnum.likely_ai: ("#dd6b20", "#feebc8", "LIKELY AI"),
        VerdictEnum.likely_real_looking: ("#2b6cb0", "#ebf8ff", "NO AI SIGNS FOUND"),
        VerdictEnum.inconclusive: ("#4a5568", "#edf2f7", "INCONCLUSIVE")
    }
    
    theme_color, bg_tint, default_label = verdict_colors.get(
        passport.verdict, ("#4a5568", "#edf2f7", "INCONCLUSIVE")
    )
    
    headline_text = strings.get("verdicts", {}).get(passport.verdict.value, {}).get("headline", {}).get(lang, default_label)
    detail_text = strings.get("verdicts", {}).get(passport.verdict.value, {}).get("detail", {}).get(lang, "")
    scope_note_text = passport.scope_note.hi if is_hi else passport.scope_note.en
    
    reasons_html = "".join([
        f"<li style='margin-bottom: 8px;'><strong>{r.key}:</strong> {r.hi if is_hi else r.en}</li>"
        for r in passport.reasons
    ]) or "<li>No specific risk flags recorded.</li>"

    origin_html = ""
    if passport.origin:
        claim = passport.origin.claim_hi if is_hi else passport.origin.claim_en
        origin_html = f"""
        <div class="card">
            <h3>👁️ Eye 1: Indexed Origin</h3>
            <p><strong>Source:</strong> {passport.origin.source}</p>
            <p><strong>First Seen:</strong> {passport.origin.date}</p>
            <p><strong>Claim:</strong> {claim}</p>
            <p><a href="{passport.origin.factcheck_url}" target="_blank" rel="noopener">View Archive Source / Fact-Check &rarr;</a></p>
        </div>
        """

    diff_html = ""
    if passport.diff:
        regions_count = len(passport.diff.changed_regions)
        diff_html = f"""
        <div class="card">
            <h3>👁️ Eye 2: Change & Alignment Diff</h3>
            <p>Detected <strong>{regions_count}</strong> altered region(s) compared to the baseline archive.</p>
            <div style="display:flex; gap: 10px; margin-top: 10px; flex-wrap: wrap;">
                <div>
                    <span style="font-size:12px; color:#666;">Diff Heatmap Overlay:</span><br/>
                    <img src="{passport.diff.heatmap_url}" alt="Heatmap" style="max-width:240px; border-radius:6px; border:1px solid #ccc;"/>
                </div>
                <div>
                    <span style="font-size:12px; color:#666;">Aligned Original:</span><br/>
                    <img src="{passport.diff.aligned_url}" alt="Aligned" style="max-width:240px; border-radius:6px; border:1px solid #ccc;"/>
                </div>
            </div>
        </div>
        """

    c2pa_html = ""
    if passport.c2pa.status != "none":
        c2pa_html = f"""
        <div class="card">
            <h3>🛡️ Content Credentials (C2PA)</h3>
            <p><strong>Status:</strong> {passport.c2pa.status.upper()}</p>
            <p><strong>Issuer:</strong> {passport.c2pa.issuer or 'N/A'}</p>
            <p><strong>AI-Generated Flag:</strong> {'YES' if passport.c2pa.ai_generated else 'NO'}</p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trinetra Provenance Passport - {passport.id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 16px;
            background: #f7fafc;
            color: #2d3748;
        }}
        .container {{
            max-width: 680px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }}
        .header {{
            padding: 16px 20px;
            background: #1a202c;
            color: #ffffff;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ margin: 0; font-size: 18px; letter-spacing: 0.5px; }}
        .header .meta {{ font-size: 12px; color: #a0aec0; }}
        .lang-switch a {{
            color: #edf2f7;
            text-decoration: none;
            font-size: 13px;
            margin-left: 8px;
            padding: 4px 8px;
            background: #2d3748;
            border-radius: 4px;
        }}
        .verdict-banner {{
            padding: 24px 20px;
            background-color: {bg_tint};
            border-left: 6px solid {theme_color};
        }}
        .verdict-title {{
            font-size: 22px;
            font-weight: 800;
            color: {theme_color};
            margin: 0 0 8px 0;
        }}
        .verdict-detail {{
            font-size: 15px;
            line-height: 1.5;
            margin: 0;
            color: #4a5568;
        }}
        .eyes-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            padding: 16px 20px;
            background: #edf2f7;
            border-bottom: 1px solid #e2e8f0;
        }}
        .eye-box {{
            background: white;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #cbd5e0;
        }}
        .eye-box .eye-title {{ font-size: 11px; text-transform: uppercase; color: #718096; font-weight: 600; }}
        .eye-box .eye-val {{ font-size: 14px; font-weight: 700; margin-top: 4px; }}
        .content {{ padding: 20px; }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 16px;
        }}
        .card h3 {{ margin-top: 0; font-size: 15px; color: #2d3748; }}
        .scope-note {{
            background: #fffaf0;
            border-left: 4px solid #dd6b20;
            padding: 12px;
            font-size: 13px;
            color: #7b341e;
            margin-top: 16px;
            border-radius: 4px;
        }}
        .actions {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .btn {{
            flex: 1;
            min-width: 140px;
            text-align: center;
            padding: 10px 14px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
        }}
        .btn-card {{ background: #3182ce; color: white; }}
        .btn-external {{ background: #edf2f7; color: #2d3748; border: 1px solid #cbd5e0; }}
        .footer {{
            padding: 14px 20px;
            font-size: 12px;
            text-align: center;
            color: #718096;
            border-top: 1px solid #e2e8f0;
            background: #f7fafc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>TRINETRA : PROVENANCE PASSPORT</h1>
                <div class="meta">ID: {passport.id} &bull; Team Kinetix</div>
            </div>
            <div class="lang-switch">
                <a href="/p/{passport.id}?lang=en">EN</a>
                <a href="/p/{passport.id}?lang=hi">हिन्दी</a>
            </div>
        </div>

        <div class="verdict-banner">
            <div class="verdict-title">{headline_text}</div>
            <p class="verdict-detail">{detail_text}</p>
        </div>

        <div class="eyes-grid">
            <div class="eye-box">
                <div class="eye-title">Eye 1: Origin</div>
                <div class="eye-val">{passport.eyes.origin.value.upper()}</div>
            </div>
            <div class="eye-box">
                <div class="eye-title">Eye 2: Change</div>
                <div class="eye-val">{passport.eyes.change.value.upper()}</div>
            </div>
            <div class="eye-box">
                <div class="eye-title">Eye 3: Synthesis</div>
                <div class="eye-val">{passport.eyes.synthesis.value.upper()}</div>
            </div>
        </div>

        <div class="content">
            <div class="card">
                <h3>🔍 Key Signals & Reasons</h3>
                <ul style="padding-left: 20px; margin: 0;">
                    {reasons_html}
                </ul>
            </div>

            {origin_html}
            {diff_html}
            {c2pa_html}

            <div class="scope-note">
                <strong>Scope Note:</strong> {scope_note_text}
            </div>

            <div class="actions">
                <a href="/passport/{passport.id}/card.png?lang={lang}" target="_blank" class="btn btn-card">Download Share Card</a>
                <a href="{passport.external_search.lens}" target="_blank" rel="noopener" class="btn btn-external">Search Google Lens</a>
                <a href="{passport.external_search.tineye}" target="_blank" rel="noopener" class="btn btn-external">Search TinEye</a>
            </div>
        </div>

        <div class="footer">
            Code for Innovex '26 &bull; Theme: Navyug - A New Era &bull; Trinetra Digital Trust
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/passport/{id}/card.png")
async def get_share_card(id: str, lang: Optional[str] = Query("en", pattern="^(en|hi)$")):
    """
    GET /passport/{id}/card.png?lang=en|hi:
    Generates a high-resolution 1080x1350 PNG share card using Pillow.
    Features verdict colour + icon + text + three eyes + scope note + Trinetra footer.
    """
    passport = resolve_passport(id)
    strings = get_strings()
    is_hi = (lang == "hi")

    # Share card canvas: 1080 x 1350 px
    width, height = 1080, 1350
    card = Image.new("RGB", (width, height), color=(18, 22, 30))
    draw = ImageDraw.Draw(card)

    # Colors
    c_banner = (30, 36, 48)
    verdict_colors = {
        VerdictEnum.original: (16, 124, 65),     # green
        VerdictEnum.modified: (183, 121, 31),   # amber
        VerdictEnum.out_of_context: (183, 121, 31), # amber
        VerdictEnum.ai_confirmed: (197, 48, 48), # red (ONLY for ai_confirmed)
        VerdictEnum.likely_ai: (221, 107, 32),   # orange
        VerdictEnum.likely_real_looking: (43, 108, 176), # grey-blue
        VerdictEnum.inconclusive: (74, 85, 104)  # grey-blue
    }
    v_color = verdict_colors.get(passport.verdict, (74, 85, 104))

    # Header section
    draw.rectangle([(0, 0), (width, 160)], fill=(12, 15, 22))
    draw.rectangle([(0, 155), (width, 160)], fill=(0, 200, 220)) # Accent cyan line

    # Draw header text
    draw.text((60, 45), "TRINETRA", fill=(255, 255, 255))
    draw.text((60, 85), "PROVENANCE PASSPORT | DIGITAL TRUST", fill=(0, 200, 220))
    draw.text((60, 115), f"ID: {passport.id} • Team Kinetix", fill=(160, 174, 192))

    # Verdict Box (y: 200 - 450)
    draw.rectangle([(60, 200), (width - 60, 450)], fill=c_banner, outline=v_color, width=4)
    draw.rectangle([(60, 200), (width - 60, 270)], fill=v_color)
    
    headline = strings.get("verdicts", {}).get(passport.verdict.value, {}).get("headline", {}).get(lang, passport.verdict.value.upper())
    detail = strings.get("verdicts", {}).get(passport.verdict.value, {}).get("detail", {}).get(lang, "")
    
    draw.text((90, 220), headline, fill=(255, 255, 255))
    draw.text((90, 300), f"CONFIDENCE: {passport.confidence_band.value.upper()}", fill=(200, 210, 225))
    
    # Detail wrapped
    draw.text((90, 345), detail[:100] + ("..." if len(detail) > 100 else ""), fill=(180, 190, 205))

    # Three Eyes Grid (y: 490 - 660)
    box_w = (width - 120 - 40) // 3
    y_eyes = 490
    eyes_data = [
        ("EYE 1: ORIGIN", passport.eyes.origin.value.upper()),
        ("EYE 2: CHANGE", passport.eyes.change.value.upper()),
        ("EYE 3: SYNTHESIS", passport.eyes.synthesis.value.upper()),
    ]
    for i, (title, val) in enumerate(eyes_data):
        x0 = 60 + i * (box_w + 20)
        x1 = x0 + box_w
        draw.rectangle([(x0, y_eyes), (x1, y_eyes + 160)], fill=c_banner, outline=(50, 60, 80), width=2)
        draw.text((x0 + 20, y_eyes + 30), title, fill=(130, 150, 175))
        draw.text((x0 + 20, y_eyes + 85), val, fill=(255, 255, 255))

    # Reasons Section (y: 700 - 980)
    draw.rectangle([(60, 700), (width - 60, 980)], fill=c_banner, outline=(50, 60, 80), width=2)
    draw.text((90, 725), "VERIFIED EVIDENCE & SIGNALS", fill=(0, 200, 220))
    y_reason = 775
    for r in passport.reasons[:3]:
        r_text = f"• [{r.key}] {r.hi if is_hi else r.en}"
        draw.text((90, y_reason), r_text[:85] + ("..." if len(r_text) > 85 else ""), fill=(220, 225, 235))
        y_reason += 45

    # Scope Note Box (y: 1020 - 1180)
    draw.rectangle([(60, 1020), (width - 60, 1180)], fill=(35, 28, 20), outline=(183, 121, 31), width=2)
    draw.text((90, 1045), "SCOPE NOTE & SEARCH JURISDICTION", fill=(237, 137, 54))
    scope_text = passport.scope_note.hi if is_hi else passport.scope_note.en
    draw.text((90, 1090), scope_text[:110] + ("..." if len(scope_text) > 110 else ""), fill=(225, 215, 200))

    # Footer (y: 1240 - 1350)
    draw.rectangle([(0, 1250), (width, 1350)], fill=(12, 15, 22))
    draw.text((60, 1275), "Code for Innovex '26 • Theme: Navyug - A New Era", fill=(130, 145, 165))
    draw.text((60, 1305), "Trinetra: Digital Trust & Provenance Passport", fill=(100, 115, 135))

    # Output as PNG bytes
    buf = io.BytesIO()
    card.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")
