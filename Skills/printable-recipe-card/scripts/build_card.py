#!/usr/bin/env python3
"""Build a 2-page landscape Letter recipe card PDF from a spec JSON.

Usage: python build_card.py <spec.json> <output.pdf>

Spec format: references/spec-format.md. Text accepts <b>, <i>, and <g>green callout</g>.
The script auto-shrinks text to fit. Anything that still overflows is printed as
"WARNING: ..." so the spec can be trimmed and the card rebuilt.
"""
import datetime, json, math, os, sys
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from PIL import Image

GF = "/usr/share/fonts/truetype/google-fonts/"
DJ = "/usr/share/fonts/truetype/dejavu/"


def reg(name, path, fallback):
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(name, path))
        return name
    return fallback


BODY = reg("Body", DJ + "DejaVuSansCondensed.ttf", "Helvetica")
BODYB = reg("BodyB", DJ + "DejaVuSansCondensed-Bold.ttf", "Helvetica-Bold")
BODYI = reg("BodyI", DJ + "DejaVuSansCondensed-Oblique.ttf", "Helvetica-Oblique")
if BODY == "Body":
    registerFontFamily("Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyB")
HB = reg("PopB", GF + "Poppins-Bold.ttf", BODYB)
HM = reg("PopM", GF + "Poppins-Medium.ttf", BODYB)
HR = reg("PopR", GF + "Poppins-Regular.ttf", BODY)

GREEN = HexColor("#067A46"); LIME = HexColor("#91C11E"); DARK = HexColor("#242424")
GREY = HexColor("#6B6B6B"); TINT = HexColor("#F1F7E6"); RULE = HexColor("#DADADA")
TAG_COLORS = [HexColor("#E3F0C8"), HexColor("#D9E6F7"), HexColor("#F7E3D9"), HexColor("#EFE3F7")]
W, H = landscape(letter)
M = 22
WARN = []


def mk(text):
    return str(text or "").replace("<g>", '<font color="#067A46"><b>').replace("</g>", "</b></font>")


def cover_crop(path, w, h, focus=None):
    """Crop the image to the w:h aspect ratio, centered on focus=(fx, fy).

    fx, fy are fractions of the full image (0,0 = top-left, 1,1 = bottom-right). The crop
    window is centered on that point and clamped to the image edges. Default is the center.
    """
    im = Image.open(path).convert("RGB")
    iw, ih = im.size
    fx, fy = (focus if focus else (0.5, 0.5))
    fx = min(max(float(fx), 0.0), 1.0)
    fy = min(max(float(fy), 0.0), 1.0)
    tr = w / h
    if iw / ih > tr:
        nw = int(ih * tr)
        x = int(round(fx * iw - nw / 2)); x = min(max(x, 0), iw - nw)
        im = im.crop((x, 0, x + nw, ih))
    else:
        nh = int(iw / tr)
        y = int(round(fy * ih - nh / 2)); y = min(max(y, 0), ih - nh)
        im = im.crop((0, y, iw, y + nh))
    return ImageReader(im)


def P(text, size, lead, font=BODY, color=DARK, align=0, indent=0, bullet=None):
    st = ParagraphStyle("p", fontName=font, fontSize=size, leading=lead, textColor=color, alignment=align,
                        leftIndent=indent, bulletIndent=0, bulletFontName=BODY, bulletFontSize=size)
    return Paragraph(mk(text), st, bulletText=bullet)


def fit_bullets(items, w, max_h, size=7.9, min_size=6.6, gap=3):
    """Return (paragraphs, size) where the bullet list fits max_h, shrinking the font as needed."""
    s = size
    while True:
        ps = [P(t, s, s * 1.25, indent=8, bullet="•") for t in items]
        h = sum(p.wrap(w, 5000)[1] for p in ps) + gap * max(len(ps) - 1, 0)
        if h <= max_h or s <= min_size:
            return ps, s, h
        s -= 0.2


def info_groups(spec):
    groups = []
    g1 = []
    if spec.get("hello"):
        g1 += [("sub", spec["hello"]["title"]), ("para", spec["hello"]["text"])]
    if spec.get("tip") or spec.get("prep_ahead"):
        g1 += [("head", "Before you start")]
        if spec.get("tip"):
            g1 += [("sub", spec["tip"]["title"]), ("para", spec["tip"]["text"])]
        if spec.get("prep_ahead"):
            g1 += [("sub", "Prep ahead"), ("bullets", spec["prep_ahead"])]
    if g1: groups.append((1.55 if spec.get("prep_ahead") else 1.25, g1))
    g2 = []
    if spec.get("tools"): g2 += [("head", "Cooking tools"), ("para", spec["tools"])]
    if spec.get("pantry"): g2 += [("head", "Pantry ingredients"), ("para", spec["pantry"])]
    if spec.get("allergens"): g2 += [("head", "Allergens"), ("para", spec["allergens"])]
    if g2: groups.append((1.1, g2))
    if spec.get("nutrition"):
        groups.append((0.95, [("head", "Nutrition  (per serving)"), ("table", spec["nutrition"])]))
    if spec.get("notes"):
        groups.append((1.25, [("head", "Notes"), ("bullets", spec["notes"])]))
    return groups


def info_bar_height(c, spec, w, size=7.8):
    """Height the info bar needs at the default font size (clamped to a sensible range)."""
    groups = info_groups(spec)
    if not groups:
        return 0
    pad = 10
    tw = sum(g[0] for g in groups)
    inner = w - pad * 2 - 18 * (len(groups) - 1)
    need = max(layout_items(c, it, 0, 0, inner * wt / tw, size, draw=False) for wt, it in groups)
    return max(90, min(190, need + 2 * pad + 2))


def draw_info_bar(c, spec, x, y, w, h):
    """Horizontal info band at the bottom of page 1. Sections are optional; columns size to content."""
    groups = info_groups(spec)
    if not groups:
        return
    c.setFillColor(TINT); c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
    pad = 10
    tw = sum(g[0] for g in groups)
    inner = w - pad * 2 - 18 * (len(groups) - 1)
    cx = x + pad
    for gi, (weight, items) in enumerate(groups):
        cw = inner * weight / tw
        size = 7.8
        while True:
            used = layout_items(c, items, cx, y + h - pad, cw, size, draw=False)
            if used <= h - 2 * pad or size <= 6.2:
                break
            size -= 0.2
        if used > h - 2 * pad:
            WARN.append(f"info bar column {gi+1} overflows; shorten its text or raise bar_height")
        layout_items(c, items, cx, y + h - pad, cw, size, draw=True)
        if gi < len(groups) - 1:
            c.setStrokeColor(HexColor("#C9DDB0")); c.setLineWidth(0.8)
            c.line(cx + cw + 9, y + pad, cx + cw + 9, y + h - pad)
        cx += cw + 18


def layout_items(c, items, x, top, w, size, draw):
    y = top
    first = True
    prev = None
    for kind, val in items:
        if kind == "head":
            hs = size + 3.4
            y -= (0 if first else 5) + hs
            if draw:
                c.setFillColor(GREEN); c.setFont(HM, hs); c.drawString(x, y + 1.5, val)
            y -= 2
        elif kind == "sub":
            ss = size + 1.2
            y -= ss + (1 if prev == "head" or first else 4)
            if draw:
                c.setFillColor(DARK); c.setFont(HM, ss); c.drawString(x, y + 1, val)
            y -= 1.5
        elif kind == "para":
            p = P(val, size, size * 1.25); _, ph = p.wrap(w, 2000)
            if draw: p.drawOn(c, x, y - ph)
            y -= ph
        elif kind == "bullets":
            for t in val:
                p = P(t, size, size * 1.25, indent=8, bullet="•"); _, ph = p.wrap(w, 2000)
                if draw: p.drawOn(c, x, y - ph)
                y -= ph + 2
        elif kind == "table":
            ABBR = {"Carbohydrates": "Carbs", "Carbohydrate": "Carbs", "Saturated Fat": "Sat. Fat",
                    "Dietary Fiber": "Fiber", "Cholesterol": "Cholest.", "Unsaturated Fat": "Unsat. Fat",
                    "Trans Fat": "Trans Fat", "Potassium": "Potass."}
            rows = [(ABBR.get(a, a), b) for a, b in (tuple(r) for r in val)]
            half = math.ceil(len(rows) / 2)
            colw = w / 2
            rh = size * 1.45
            for i, (a, b) in enumerate(rows):
                col, r = (0, i) if i < half else (1, i - half)
                yy = y - (r + 1) * rh
                if draw:
                    c.setFillColor(DARK); c.setFont(BODY, size); c.drawString(x + col * colw, yy + 2, a)
                    c.setFont(BODYB, size); c.drawRightString(x + col * colw + colw - 8, yy + 2, b)
                    c.setStrokeColor(HexColor("#C9DDB0")); c.setLineWidth(0.4)
                    c.line(x + col * colw, yy, x + col * colw + colw - 8, yy)
            y -= half * rh
        first = False
        prev = kind
    return top - y


def main():
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    imgdir = spec.get("img_dir", os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "img"))

    def ip(f):
        if not f:
            return None
        p = os.path.join(imgdir, f)
        return p if os.path.exists(p) else None

    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle(f"{spec['title']} - Recipe Card")
    c.setAuthor(spec.get("source", ""))

    # ================= PAGE 1 =================
    ts = 26
    while c.stringWidth(spec["title"], HB, ts) > W - 2 * M and ts > 15:
        ts -= 1
    c.setFillColor(DARK); c.setFont(HB, ts); c.drawString(M, H - 50, spec["title"])
    ss = 14
    while c.stringWidth(spec.get("subtitle", ""), HM, ss) > W - 2 * M and ss > 9:
        ss -= 0.5
    c.setFont(HM, ss); c.drawString(M, H - 70, spec.get("subtitle", ""))
    bits = [spec.get("time"), spec.get("servings"),
            f"Calories: {spec['calories']}" if spec.get("calories") else None,
            f"Protein: {spec['protein']}" if spec.get("protein") else None]
    c.setFont(HR, 11.5); c.drawString(M, H - 88, "  •  ".join(b for b in bits if b))
    stats_w = c.stringWidth("  •  ".join(b for b in bits if b), HR, 11.5)
    tx = W - M
    for k, label in enumerate(reversed(spec.get("tags", [])[:4])):
        c.setFont(HM, 9.5); tw = c.stringWidth(label, HM, 9.5) + 22
        if tx - tw < M + stats_w + 12:
            WARN.append(f"tag '{label}' dropped (no room)"); break
        tx -= tw
        c.setFillColor(TAG_COLORS[k % len(TAG_COLORS)]); c.roundRect(tx, H - 93, tw, 18, 9, fill=1, stroke=0)
        c.setFillColor(DARK); c.drawCentredString(tx + tw / 2, H - 87.5, label); tx -= 8

    hero = ip(spec.get("hero"))

    # ---------- bottom info bar (intro / tips / tools / nutrition / notes) ----------
    bar_bot = 20
    bar_h = spec.get("bar_height") or info_bar_height(c, spec, W - 2 * M)
    bar_top = bar_bot + bar_h
    if bar_h:
        draw_info_bar(c, spec, M, bar_bot, W - 2 * M, bar_h)
    else:
        bar_top = bar_bot - 12

    body_top, body_bot = H - 100, bar_top + 12
    if hero:
        hw = 440
        c.drawImage(cover_crop(hero, hw, body_top - body_bot, spec.get("hero_focus")), 0, body_bot, hw, body_top - body_bot)
        px = hw + 18
    else:
        px = M
    pw = W - px - M

    ings = spec["ingredients"]
    grid = all(i.get("icon") and ip(i.get("icon")) for i in ings if "section" not in i) and hero
    header = spec.get("ingredient_header", "2 Person  |  4 Person" if grid else (spec.get("servings") or ""))
    hy = body_top - 14
    c.setFillColor(GREEN); c.setFont(HM, 13); c.drawString(px, hy, "Ingredients")
    if header:
        c.setFont(HB, 8.5)
        c.drawString(px + c.stringWidth("Ingredients", HM, 13) + 8, hy + 0.5, header)
    top = hy - 12

    if grid:
        n_ing = len(ings)
        cols = 4 if n_ing > 9 else 3
        nrows = math.ceil(n_ing / cols)
        rh = min(100, (top - body_bot) / max(nrows, 1)); s_ = max(22, min(40, rh - 50)); cw = pw / cols
        if rh < 64:
            WARN.append("ingredient grid is cramped; consider list mode (drop icons)")
        for i, ing in enumerate(ings):
            col, row = i % cols, i // cols
            cx = px + col * cw + cw / 2; cy = top - row * rh
            c.drawImage(ip(ing["icon"]), cx - s_ / 2, cy - s_, s_, s_, mask="auto", preserveAspectRatio=True, anchor="c")
            c.setFillColor(GREEN); c.setFont(HB, 7.8); c.drawCentredString(cx, cy - s_ - 11, ing.get("amount", ""))
            p = P(ing["name"], 7.4, 8.6, align=1); _, h = p.wrap(cw - 4, 100)
            p.drawOn(c, cx - (cw - 4) / 2, cy - s_ - 14 - h)
            if ing.get("allergen"):
                c.setFillColor(LIME); c.setFont(BODYB, 6.5); c.drawCentredString(cx, cy - s_ - 22 - h, ing["allergen"])
    else:
        n_items = len(ings)
        if hero:
            ncols = 1 if n_items <= 14 else 2
            size = 10.0
        else:
            ncols = 2 if n_items <= 16 else 3
            size = 12.0
        gap = 14 if hero else 28
        colw = (pw - gap * (ncols - 1)) / ncols
        avail = top - body_bot
        while True:
            lead = size * 1.28
            amt_w = min(colw * 0.34, 62 * size / 9)
            blocks = []
            for ing in ings:
                if "section" in ing:
                    p = P(f"<b>{ing['section']}</b>", size, lead, font=HM, color=GREEN)
                    blocks.append(("sec", p, p.wrap(colw, 500)[1] + 4))
                else:
                    a = P(f'<font color="#067A46"><b>{ing.get("amount", "")}</b></font>', size, lead)
                    n = P(ing["name"], size, lead)
                    ha = a.wrap(amt_w - 4, 500)[1]; hn = n.wrap(colw - amt_w, 500)[1]
                    blocks.append(("ing", (a, n), max(ha, hn) + size * 0.4))
            total = sum(b[2] for b in blocks)
            target = min(avail, max(total / ncols, max(b[2] for b in blocks)))
            colsplit, cur, h_used = [[]], 0, 0
            for k, b in enumerate(blocks):
                limit = target if cur < ncols - 1 else avail
                orphan = b[0] == "sec" and k + 1 < len(blocks) and h_used + b[2] + blocks[k + 1][2] > limit
                if (h_used + b[2] > limit or orphan) and colsplit[cur]:
                    cur += 1; colsplit.append([]); h_used = 0
                colsplit[cur].append(b); h_used += b[2]
            fits = len(colsplit) <= ncols and all(sum(x[2] for x in col) <= avail for col in colsplit)
            if fits or size <= 6.8:
                break
            size -= 0.2
        if len(colsplit) > ncols:
            WARN.append("ingredient list overflows page 1; shorten names or move notes to 'notes'")
        for ci, colb in enumerate(colsplit[:ncols]):
            x = px + ci * (colw + gap); y = top
            for kind, obj, h in colb:
                if kind == "sec":
                    obj.drawOn(c, x, y - h + 2)
                else:
                    a, n = obj
                    a.drawOn(c, x, y - a.wrap(amt_w - 4, 500)[1])
                    n.drawOn(c, x + amt_w, y - n.wrap(colw - amt_w, 500)[1])
                    c.setStrokeColor(RULE); c.setLineWidth(0.4); c.line(x, y - h + 1.2, x + colw, y - h + 1.2)
                y -= h
    c.showPage()

    # ================= PAGE 2: steps, full width =================
    steps = spec["steps"]
    n = len(steps)
    has_img = any(ip(s.get("image")) for s in steps)
    if has_img:
        scols = 3 if n <= 6 else 4
        srows = max(1, math.ceil(n / scols))
    else:
        scols = 2 if n <= 4 else (3 if n <= 9 else 4)
        srows = max(1, math.ceil(n / scols))
    gx = M; gw = W - 2 * M; gap = 16
    colw = (gw - (scols - 1) * gap) / scols
    area_top, area_bot = H - 24, 38
    row_h = (area_top - area_bot) / srows
    img_h = min(colw * 0.58, row_h * 0.52) if has_img else 0
    # One font size for every step. With photos, shrink the photos (down to ~35% of the row)
    # before shrinking the text, so the text stays readable at the stove.
    base = (10.2 if scols == 3 else 9.0) if has_img else (11.5 if scols <= 3 else 10.2)

    def size_for(title_h):
        return min(fit_bullets(stp["bullets"], colw, row_h - title_h - 10, size=base)[1] for stp in steps)

    if has_img:
        min_img = row_h * 0.35
        while True:
            step_size = size_for(img_h + 22)
            if step_size >= base - 0.01 or img_h <= min_img:
                break
            img_h = max(min_img, img_h - 4)
        if step_size < base - 0.01:
            step_size = size_for(img_h + 22)
    else:
        step_size = size_for(34)
    for i, stp in enumerate(steps):
        col, row = i % scols, i // scols
        sx = gx + col * (colw + gap); t = area_top - row * row_h
        if has_img:
            im = ip(stp.get("image"))
            if im:
                c.drawImage(cover_crop(im, colw, img_h, stp.get("focus")), sx, t - img_h, colw, img_h)
            else:
                c.setFillColor(TINT); c.rect(sx, t - img_h, colw, img_h, fill=1, stroke=0)
            c.setFillColor(white); c.rect(sx, t - 24, 24, 24, fill=1, stroke=0)
            c.setFillColor(GREEN); c.setFont(HB, 13); c.drawCentredString(sx + 12, t - 18, str(i + 1))
            c.setFillColor(GREEN); c.setFont(HM, 12 if scols == 3 else 11)
            c.drawString(sx, t - img_h - 16, stp["title"])
            btop = t - img_h - 22
        else:
            c.setFillColor(GREEN); c.circle(sx + 11, t - 11, 11, fill=1, stroke=0)
            c.setFillColor(white); c.setFont(HB, 12); c.drawCentredString(sx + 11, t - 15.5, str(i + 1))
            c.setFillColor(GREEN); c.setFont(HM, 12.5)
            c.drawString(sx + 28, t - 16, stp["title"])
            c.setStrokeColor(GREEN); c.setLineWidth(0.8); c.line(sx, t - 27, sx + colw, t - 27)
            btop = t - 34
        max_h = btop - (t - row_h) - 10
        ps, size, h = fit_bullets(stp["bullets"], colw, max_h, size=step_size, min_size=step_size)
        if h > max_h:
            WARN.append(f"step {i+1} '{stp['title']}' overflows by {h - max_h:.0f}pt; trim its wording")
        yy = btop
        for p in ps:
            _, hh = p.wrap(colw, 5000); p.drawOn(c, sx, yy - hh); yy -= hh + 3

    c.setFillColor(GREY); c.setFont(BODY, 6.3)
    foot = spec.get("source", "")
    saved = spec.get("saved", datetime.date.today().strftime("%b %-d, %Y"))
    c.drawString(M, 22, (f"Source: {foot}  •  " if foot else "") + f"Saved {saved}")
    c.save()
    for w in WARN:
        print("WARNING:", w)
    print("wrote", out)


if __name__ == "__main__":
    main()
