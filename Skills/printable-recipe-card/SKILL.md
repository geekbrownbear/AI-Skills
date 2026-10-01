---
name: "printable-recipe-card"
description: Turn any online recipe (a HelloFresh link, a food blog, AllRecipes, NYT Cooking, Serious Eats, Minimalist Baker, a pasted recipe, or a screenshot or PDF of one) into a clean 2-page printable recipe card PDF. Page 1 has the photo, the ingredients, and an info bar. Page 2 is all steps. It doubles as an offline archive copy. Along the way it fixes broken recipe data such as missing prep steps, "1 unit" amounts, meat stock in veggie recipes, and inconsistent names. Use this whenever the user shares a recipe link or recipe text and wants a card, printable, PDF, offline copy, or "make this into a card like the others", or says a site's print or PDF button is broken. Also use it for follow-ups like "do this one too" or "and this one".
---

# Printable Recipe Card

The user prints these cards to cook from instead of reading a phone. They also keep the PDFs
as an offline archive in case a recipe site disappears. So each card needs to be:
- **Complete**: every ingredient, quantity, temperature, and time from the original.
- **Correct**: obvious data errors are fixed.
- **Easy to read at the stove.**

The look is based on HelloFresh's printed cards: a big photo, a green ingredient panel, and
steps with titles and bullets, with ingredient names in bold.

## Standing preferences

- **Page 1** has:
  - a header: title, subtitle, a stats line (time, servings, calories, protein), and up to 3 tags
  - the hero photo on the left, with ingredients to its right
  - a full-width info bar along the bottom: the intro blurb (no "Hello" heading) and Before you start, Cooking tools, Pantry
    ingredients and Allergens, a 2-column Nutrition table, and Notes

  There is **no** "Not included in your delivery" block, **no** "Some of the produce…" note, and
  **no** logo.
- **Page 2** is only the steps, full width. There is **no** "Cook for YOUR Crowd" section. The
  whole back page goes to the method, so long recipes fit:
  - photo steps: up to 8 (3 or 4 columns by 2 rows)
  - text-only steps: up to about 12 (2–4 columns)
- Use real quantities, never "1 unit". Whole-item counts (1 lime, 2 buns) are fine.
- If a recipe is labeled vegetarian or tofu but contains meat-based stock, swap in veggie stock
  everywhere. Don't change the protein in recipes that are genuinely meat recipes.
- Fix obvious errors without asking, then list every fix in the reply.

## Workflow

### 1. Get the recipe

Run `python scripts/fetch_recipe.py <url> /home/claude/work` (use a fresh work directory for
each recipe).
- **HelloFresh**: you get ingredient icons, a photo for every step, and 2|4 serving amounts.
- **Most other recipe sites**: the script reads the schema.org Recipe data, which gives the hero
  photo, ingredient lines, steps, yield, times, and nutrition. Some sites also include step photos.
- **Exit code 2 (blocked or no structured data)**: see Fallback below.

### Fallback

Many sites (AllRecipes, Budget Bytes, Serious Eats, Cookie and Kate, and others) block the
container's curl. When that happens:
1. Call `web_fetch` on the user's URL. It usually works where curl doesn't, and it returns the
   page text, often including image URLs.
2. Try to download the main photo URL from that result with `curl -L -o img/hero.jpg <url>`.
   Image CDNs are usually not blocked. Check the file with `file`.
3. If there's still no photo, build without one. The ingredients then take the full width of
   page 1.
4. If the user pasted text or uploaded a screenshot or PDF, work straight from that.
5. Note any "Recipe Notes" or FAQ tips on the page (storage, substitutions, make-ahead). They
   go in the card's Notes section because they're valuable in an archive copy.

### 2. Look at the photos and set focal points

Make a contact sheet of the downloaded images and view it. Check three things:
- **The hero is the finished dish.** If not, use the final plated step photo.
- **The photos match the recipe.** On HelloFresh they often show a different protein; see
  the fixes reference.
- **Step photos are usable.** Tiny images or images with text overlays are better left out.

Then **choose a focal point for every image you use.** The card crops each photo to a
landscape box, and by default it keeps the dead center. Blog photos are often tall phone shots
(for example 1200x2133), so a center crop can land on the background, a cookbook, or empty
counter instead of the food. To fix that:
1. Make a second contact sheet with horizontal gridlines labeled 0.1 to 0.9 down the side of each
   image (PIL `ImageDraw` works) and view it.
2. For each image, read off where the food or the action in that step sits, and write it as
   `[fx, fy]` (fractions of the full image; 0,0 is top-left). Set `hero_focus` for the hero and
   `focus` on each step. Tall images mostly need `fy`; wide images mostly need `fx`.
3. Aim the crop at what the step is about (the mixer beaters in "Cream Together", the candy in
   "Add Candy"), not just at the largest blob of food.
4. After building, check the crops in step 6 and adjust any focal point that cut off the subject.

### 3. Audit and fix

Read `references/fixes-and-quantities.md` and go through its checklist. It has a general
section for any recipe and a HelloFresh section for the errors those recipes usually have.

### 4. Write the spec

Save it as `/home/claude/work/spec.json` following `references/spec-format.md`. Key points:

- **Steps**: group the method into logical stages. Aim for 4–9 steps without photos, or 6 with
  photos. Blog recipes often have 10–15 tiny steps; don't pad them out or merge them
  aggressively. Name the stages ("Bake Tofu", "Make Sauce", "Fry & Serve") and
  rewrite each in your own concise words. Keep every quantity, temperature, time, and doneness
  cue. Bold the ingredient names, times, and temperatures that someone glancing at the card
  needs. Put 4-serving variants and "(you'll use the rest later)" notes in `<g>`. Put the steps
  in real cooking order: start the longest-running task first, and flag parallel work with
  `<g>While X cooks:</g>`.
- **Time**: recalculate the real start-to-plate time with the overlapping work taken into
  account (checklist item 11). Don't copy the site's figure.
- **Ingredients**: HelloFresh cards use the icon grid with `"2 | 4"` amounts. Everything else
  uses list mode:
  - Split each ingredient into `amount` (quantity and unit, like "2-3 TBSP" or "4 cloves") and
    `name` (with the prep, like "garlic, minced").
  - Keep the recipe's own ingredient groups (Sauce, Topping) as `{"section": ...}` rows.
  - List every ingredient, including salt and oil. There is no "shipped" concept for
    non-HelloFresh recipes, so leave out `pantry` or use it only for "to taste" extras.
  - Keep the original yield. Don't rescale unless the user asks.
- **Hello / Before you start**: write one short, useful sentence for each in your own words:
  what makes the dish good, and one prep tip. Don't copy the site's intro prose.
- **Prep ahead** (`prep_ahead`, 2–3 bullets): always include it. List what can be done earlier
  in the day, or days before, so dinner goes faster. Each bullet should say when to do it and
  how to store it. Good candidates:
  - pressing tofu at lunch in a tofu press (the user's own habit; it's perfectly pressed by
    dinner)
  - cooking grains ahead (day-old rice is better for fried rice)
  - mixing sauces, dressings, and marinades
  - quick-pickling
  - chopping sturdy veg (carrots, onions, peppers)
  - making dough
  - toasting nuts

  Skip anything that suffers from sitting, such as cut avocado or apple, dressed greens, or
  anything meant to be crispy. These bullets appear under "Before you start" in the page 1 info
  bar.
- **Nutrition**: include it if the source gives it. If the source doesn't list nutrition, leave
  it out and don't make numbers up.
- **Allergens**: work them out from the ingredients (soy, wheat or gluten, milk, eggs, peanuts,
  tree nuts, sesame, fish, shellfish).
- **Source**: set `source` to the URL without `https://`. The footer adds "Saved <date>" for
  the archive.
- **Tags**: 1–3 short tags, like Veggie, Vegan, Quick, Gluten-Free, or Spicy.

### 5. Build

Run:
`python scripts/build_card.py /home/claude/work/spec.json "/mnt/user-data/outputs/<Recipe-Name>-Recipe-Card.pdf"`

The script sizes the info bar to its content and uses one text size for all steps. When steps
have photos, it shrinks the photos before the text, so the text stays readable. It shrinks text
only as a last resort. It prints `WARNING:` lines for anything that
still overflows, such as a step, an info-bar column, the ingredient list, or a dropped tag. Fix every
warning. Trim the wording or merge steps. If the info bar is too tall, shorten the Hello, tip,
or Notes text. Then rebuild.

### 6. Check visually

Render both pages with `pdftoppm -r 70 -png` and view them. Look for:
- Text colliding with other text.
- A cramped step that would be hard to read while cooking.
- A photo that is cropped badly (the subject cut off or the crop landing on background). Fix it by
  changing `hero_focus` or the step's `focus`, not by swapping the photo.

Fix and rebuild before delivering.

### 7. Deliver

Call `present_files` with the PDF. Keep the reply short: a bulleted list of the fixes you made,
which quantities are estimates, and anything that's missing (for example, no photo because the
site blocked it, or no nutrition listed).

For several recipes at once, run steps 1–6 for each one in its own work directory, then present
all the PDFs together.
