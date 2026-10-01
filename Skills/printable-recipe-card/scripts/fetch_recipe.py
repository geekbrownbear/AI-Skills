#!/usr/bin/env python3
"""Fetch a recipe page, extract structured recipe data, and download photos.

Usage: python fetch_recipe.py <recipe_url> <work_dir>

Supported sources, tried in order:
  1. HelloFresh pages (the page's __NEXT_DATA__ JSON). This path gets per-ingredient icons, a
     photo for each step, and 2 and 4 serving amounts.
  2. Any site with schema.org Recipe JSON-LD, which covers most recipe blogs and big recipe
     sites. This path gets the hero photo, ingredient lines, steps (plus step photos when the
     site provides them), the yield, times, and nutrition.
If the site blocks the container (403 or a Cloudflare page) or has no structured data, the
script exits with code 2. Fall back to web_fetch as described in SKILL.md.

Writes <work_dir>/recipe.json (normalized) and images into <work_dir>/img/.
"""
import html, json, os, re, sys, subprocess

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
HDRS = ["-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H", "Accept-Language: en-US,en;q=0.9"]
HF_MEDIA = "https://media.hellofresh.com"


def curl(url, out=None):
    cmd = ["curl", "-sL", "--compressed", "--max-time", "40", "-A", UA] + HDRS + [url]
    if out:
        cmd += ["-o", out]
    cmd += ["-w", "%{http_code}"]
    r = subprocess.run(cmd, capture_output=True)
    if out:
        return None, r.stdout.decode()
    body, code = r.stdout[:-3], r.stdout[-3:].decode()
    return body, code


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60]


def clean(s):
    s = re.sub(r"<br\s*/?>", "\n", str(s or ""))
    s = re.sub(r"</(p|li)>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", html.unescape(s))).strip()
    return re.sub(r"\(\((.*?)\)\)", r"(\1)", s)


def is_image(path):
    """True if the download is a real image; deletes error pages saved under an image name."""
    try:
        with open(path, "rb") as f:
            head = f.read(12)
        ok = (head.startswith(b"\x89PNG") or head.startswith(b"\xff\xd8")
              or (head[:4] == b"RIFF" and head[8:12] == b"WEBP"))
    except Exception:
        ok = False
    if not ok and os.path.exists(path):
        os.remove(path)
    return ok


def download(url, path):
    if not url:
        return None
    curl(url, path)
    if not is_image(path):
        return None
    # give the file a real .jpg/.png extension and convert webp/gif to formats reportlab reads
    try:
        from PIL import Image
        im = Image.open(path)
        fmt = im.format
        base = os.path.splitext(path)[0]
        if fmt == "PNG" or (fmt != "JPEG" and im.mode in ("RGBA", "P", "LA")):
            new = base + ".png"
            if fmt != "PNG" or new != path:
                im.save(new, "PNG")
        else:
            new = base + ".jpg"
            if fmt != "JPEG":
                im.convert("RGB").save(new, "JPEG", quality=90)
            elif new != path:
                os.replace(path, new)
        if new != path and os.path.exists(path):
            os.remove(path)
        path = new
    except Exception:
        pass
    return os.path.basename(path)


def iso_minutes(s):
    if not s:
        return None
    m = re.match(r"P(?:T)?(?:(\d+)H)?(?:(\d+)M)?", str(s).replace("DT", "T"))
    if not m:
        return None
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0) or None


# ------------------------------------------------------------------ HelloFresh
def find_hf(o, rid):
    if isinstance(o, dict):
        if "steps" in o and "ingredients" in o and "yields" in o and (not rid or o.get("id") == rid):
            return o
        for v in o.values():
            r = find_hf(v, rid)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = find_hf(v, rid)
            if r:
                return r
    return None


def from_hellofresh(page, url, img):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    if not m:
        return None
    data = json.loads(m.group(1))
    rid = url.rstrip("/").split("?")[0].split("-")[-1]
    r = find_hf(data, rid) or find_hf(data, None)
    if not r:
        return None
    by_id = {i["id"]: i for i in r["ingredients"]}
    yields = {y["yields"]: {i["id"]: (i.get("amount"), i.get("unit")) for i in y["ingredients"]}
              for y in r["yields"]}
    y2, y4 = yields.get(2, {}), yields.get(4, {})
    ings = []
    for iid, (amt, unit) in y2.items():
        ing = by_id.get(iid, {})
        name = ing.get("name", "?")
        icon = None
        if ing.get("imagePath"):
            icon = download(f"{HF_MEDIA}/w_200,q_auto,f_png,c_limit/hellofresh_s3{ing['imagePath']}",
                            os.path.join(img, f"ing_{slug(name)}.png"))
        ings.append({"text": f"{amt} {unit} {name}", "name": name, "amount2": amt,
                     "amount4": y4.get(iid, (None, None))[0], "unit": unit,
                     "allergens": [a.get("name") for a in ing.get("allergens", [])],
                     "shipped": bool(ing.get("imagePath")), "icon": icon})
    steps = []
    for s in r["steps"]:
        ims = s.get("images") or []
        im = None
        if ims and ims[0].get("path"):
            im = download(f"{HF_MEDIA}/w_750,q_auto,f_jpg,c_limit,fl_lossy/hellofresh_s3{ims[0]['path']}",
                          os.path.join(img, f"step{s['index']}.jpg"))
        steps.append({"index": s["index"], "text": clean(s.get("instructions")), "image": im})
    hero = None
    if r.get("imagePath"):
        p = r["imagePath"] if r["imagePath"].startswith("/image/") else "/image" + r["imagePath"]
        hero = download(f"{HF_MEDIA}/w_1600,q_auto,f_jpg,c_limit,fl_lossy/hellofresh_s3{p}",
                        os.path.join(img, "hero.jpg"))
    times = [iso_minutes(r.get("totalTime")), iso_minutes(r.get("prepTime"))]
    return {
        "source_type": "hellofresh", "url": url, "name": r.get("name"), "headline": r.get("headline"),
        "description": r.get("description"), "yield": "2 | 4 servings",
        "time_minutes": max([t for t in times if t] or [None]),
        "tags": [t.get("name") for t in r.get("tags", [])],
        "utensils": [u.get("name") for u in r.get("utensils", [])],
        "nutrition": [[n["name"], n["amount"], n["unit"]] for n in r.get("nutrition", [])],
        "ingredients": ings, "steps": steps, "hero": hero, "notes": [],
    }


# ------------------------------------------------------------------ schema.org JSON-LD
def iter_nodes(o):
    if isinstance(o, list):
        for v in o:
            yield from iter_nodes(v)
    elif isinstance(o, dict):
        yield o
        if "@graph" in o:
            yield from iter_nodes(o["@graph"])


def is_recipe(n):
    t = n.get("@type")
    return t == "Recipe" or (isinstance(t, list) and "Recipe" in t)


def img_url(v):
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return v.get("url") or v.get("contentUrl")
    if isinstance(v, list) and v:
        # prefer the largest listed image
        best = None
        for x in v:
            u = img_url(x)
            w = x.get("width", 0) if isinstance(x, dict) else 0
            try:
                w = int(w)
            except Exception:
                w = 0
            if u and (best is None or w > best[1]):
                best = (u, w)
        return best[0] if best else None
    return None


def flatten_steps(ins, section=None):
    out = []
    if isinstance(ins, str):
        for line in [l.strip() for l in clean(ins).split("\n") if l.strip()]:
            out.append({"section": section, "text": line, "image_url": None})
    elif isinstance(ins, list):
        for x in ins:
            out += flatten_steps(x, section)
    elif isinstance(ins, dict):
        t = ins.get("@type")
        if t == "HowToSection" or "itemListElement" in ins:
            out += flatten_steps(ins.get("itemListElement", []), ins.get("name") or section)
        else:
            txt = clean(ins.get("text") or ins.get("name") or "")
            if txt:
                out.append({"section": section, "text": txt, "image_url": img_url(ins.get("image"))})
    return out


def from_jsonld(page, url, img):
    recipe = None
    for block in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', page, re.S | re.I):
        try:
            data = json.loads(block.strip())
        except Exception:
            try:
                data = json.loads(re.sub(r"[\x00-\x1f]", " ", block.strip()))
            except Exception:
                continue
        for n in iter_nodes(data):
            if is_recipe(n):
                recipe = n
                break
        if recipe:
            break
    if not recipe:
        return None
    r = recipe
    hero = download(img_url(r.get("image")), os.path.join(img, "hero.img"))
    steps = []
    for i, s in enumerate(flatten_steps(r.get("recipeInstructions")), 1):
        im = download(s["image_url"], os.path.join(img, f"step{i}.img")) if s["image_url"] else None
        steps.append({"index": i, "section": s["section"], "text": s["text"], "image": im})
    nut = r.get("nutrition") or {}
    nutrition = [[k.replace("Content", "").replace("calories", "Calories"), clean(v), ""]
                 for k, v in nut.items() if not k.startswith("@") and v]
    y = r.get("recipeYield")
    if isinstance(y, list):
        y = next((str(v) for v in y if not str(v).isdigit()), str(y[0]) if y else None)
    kw = r.get("keywords")
    tags = [k.strip() for k in (kw.split(",") if isinstance(kw, str) else (kw or []))][:10]
    for f in ("recipeCategory", "recipeCuisine"):
        v = r.get(f)
        tags += v if isinstance(v, list) else ([v] if v else [])
    times = [iso_minutes(r.get("totalTime")),
             (iso_minutes(r.get("prepTime")) or 0) + (iso_minutes(r.get("cookTime")) or 0) or None]
    author = r.get("author")
    if isinstance(author, list):
        author = author[0] if author else None
    if isinstance(author, dict):
        author = author.get("name")
    return {
        "source_type": "jsonld", "url": url, "name": clean(r.get("name")), "headline": None,
        "description": clean(r.get("description")), "author": author, "yield": clean(y),
        "time_minutes": max([t for t in times if t] or [None]),
        "tags": tags, "utensils": [clean(t.get("name") if isinstance(t, dict) else t) for t in (r.get("tool") or [])],
        "nutrition": nutrition,
        "ingredients": [{"text": clean(t), "icon": None} for t in (r.get("recipeIngredient") or [])],
        "steps": steps, "hero": hero, "notes": [],
    }


def main():
    url, work = sys.argv[1], sys.argv[2]
    img = os.path.join(work, "img")
    os.makedirs(img, exist_ok=True)
    body, code = curl(url)
    page = body.decode("utf-8", "ignore")
    if code != "200" or "cf-browser-verification" in page or "Just a moment..." in page[:3000]:
        print(f"BLOCKED: HTTP {code}. The site refuses the container's requests. "
              f"Use web_fetch on the URL instead (see SKILL.md, 'Fallback').")
        sys.exit(2)
    out = None
    if "hellofresh." in url:
        out = from_hellofresh(page, url, img)
    if not out:
        out = from_jsonld(page, url, img)
    if not out:
        print("NO STRUCTURED DATA: no HelloFresh data or schema.org Recipe found. Use web_fetch instead.")
        sys.exit(2)

    with open(os.path.join(work, "recipe.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"[{out['source_type']}] {out['name']}" + (f" | {out['headline']}" if out.get("headline") else ""))
    print(f"Yield: {out.get('yield')} | Time: {out.get('time_minutes')} min | Author: {out.get('author', '-')}")
    print("Tags:", ", ".join(map(str, out["tags"])))
    if out["utensils"]:
        print("Utensils:", ", ".join(out["utensils"]))
    print("\nINGREDIENTS:")
    for i in out["ingredients"]:
        if out["source_type"] == "hellofresh":
            flag = "" if i["shipped"] else "  [pantry]"
            print(f"  {i['name']}: {i['amount2']} | {i['amount4']} {i['unit']}  {i['allergens'] or ''}{flag}  icon={i['icon']}")
        else:
            print("  " + i["text"])
    print("\nNUTRITION:", "; ".join(f"{a} {b}{c}" for a, b, c in out["nutrition"]) or "none listed")
    print("\nSTEPS:")
    for s in out["steps"]:
        sec = f" [{s['section']}]" if s.get("section") else ""
        print(f"--- {s['index']}{sec} (image={s['image']})\n{s['text']}")
    print(f"\nHero: {out['hero']}. Images in {img}/. Make a contact sheet and look at it before building.")


if __name__ == "__main__":
    main()
