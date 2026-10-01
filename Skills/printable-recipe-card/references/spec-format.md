# Card spec format (input to build_card.py)

Text fields accept inline markup: `<b>bold</b>`, `<i>italic</i>`, and `<g>green callout</g>`.
Leave a field out to omit its section. Every info-bar section is optional.

**Layout.** Page 1 has the header, then the hero photo (left) and the ingredients (right), then an
info bar across the bottom. Page 2 has the steps, full width.

| Field | Notes |
|---|---|
| `title`, `subtitle` | Name, then a "with …" line naming the key components (write one if the source has none). Both auto-shrink. |
| `time`, `servings`, `calories`, `protein` | e.g. `"45 Minutes"`, `"Serves 4"`, `"321"`, `"13 grams"`. Omit any you don't have. |
| `tags` | Up to 3 short pills |
| `img_dir` | Folder containing images. Leave it out: it defaults to `img/` next to spec.json. A relative value is resolved from the current directory, not the spec's, so use an absolute path if you set it. |
| `hero` | Hero image filename. Omit it to give the ingredients the full page width. |
| `hero_focus` | `[fx, fy]`: the point in the hero photo to keep centered when it is cropped. Fractions of the full image, 0,0 = top-left, 1,1 = bottom-right; default `[0.5, 0.5]`. A tall photo cropped to a wide box mostly needs `fy` (e.g. `[0.5, 0.56]`). |
| `ingredient_header` | Optional. Defaults to "2 Person \| 4 Person" in grid mode, and to `servings` in list mode. |
| `ingredients` | See the two modes below |
| `hello` | `{title, text}`: one sentence on what makes the dish good. Info bar, column 1. |
| `tip` | `{title, text}`: one prep tip for "Before you start". Info bar, column 1. |
| `prep_ahead` | List of 2–3 short bullets, each saying what to do, when, and how to store it (e.g. "Press the <b>tofu</b> at lunch and refrigerate."). Appears under "Before you start" with a "Prep ahead" subheading. |
| `tools` | Comma-separated string. Info bar, column 2 (with pantry and allergens). |
| `pantry` | HelloFresh only. Comma-separated string. |
| `nutrition` | List of `[name, value]`, shown as a 2-column table in the info bar. Long labels are abbreviated automatically (Carbs, Sat. Fat, Fiber). Omit it if the source has none. |
| `allergens` | String |
| `notes` | List of short strings: storage, make-ahead, substitutions, garnish ideas. Info bar, last column. Keep to 2–4 notes. |
| `bar_height` | Optional override in points. It's auto-sized from the content (90–175) by default. |
| `steps` | List of `{title, bullets[], image?, focus?}`, with 1–3 bullets each. `focus` is `[fx, fy]` like `hero_focus`, for that step's photo. |
| `source` | URL without `https://`. The footer adds "Saved <today>" (or set `saved`, e.g. `"Sep 30, 2026"`, if the container clock is off). |

## Ingredient modes

**Grid mode** is used automatically when every ingredient has an `icon` and there is a hero
photo (HelloFresh):
```json
{"icon": "ing_tofu.png", "amount": "14 oz | 28 oz", "name": "Extra-Firm Tofu", "allergen": "Contains: Soy"}
```

**List mode** is used for everything else. Section rows are optional group headers:
```json
{"section": "Sauce"},
{"amount": "3 TBSP", "name": "tamari or soy sauce"},
{"amount": "4 cloves", "name": "garlic, minced"}
```
Keep `amount` short (quantity and unit only) and put the prep in `name`. The list flows into
2 columns beside the photo, or 3 columns with no photo, and the text shrinks to fit.

## Step layouts (page 2, full width)

- **Any step has an image**: 3 columns by 2 rows (up to 6 steps), or 4 by 2 (7–8 steps). All
  steps share one text size. The photos shrink to about 35% of the row before the text shrinks.
- **No step images**: numbered text boxes. Up to 4 steps uses 2 columns, 5–9 uses 3 columns,
  and 10–12 uses 4 columns. All steps share one text size, which starts large (11.5pt) for
  reading at the stove.
- For more than about 12 text steps, merge related ones.

## Example step

```json
{"title": "Sear Tofu", "image": "step4.jpg", "focus": [0.5, 0.6], "bullets": [
  "Add baked <b>tofu</b> to sauce; marinate <b>5 minutes</b>.",
  "Heat a large skillet over medium. Cook tofu until deep golden, <b>3-4 minutes</b> <g>(lower heat if browning too fast)</g>."
]}
```
