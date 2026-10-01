# Recipe fixes checklist and real quantities

## A. Any recipe

1. **Ingredients used in a step but not listed** (or listed but never used). Add the missing
   one to the ingredient list, or work the unused one into the right step.
2. **Split amounts.** When one ingredient is used in two places (for example, "3 TBSP tamari,
   plus more for the veggies"), make the steps say exactly how much goes where
   ("1 TBSP tamari" in the veggie step).
3. **Missing oven temperature, pan size, or heat level.** Pull it from elsewhere in the recipe,
   such as the notes or the intro. If it's missing everywhere, use a sensible standard value
   and mention it in the reply.
4. **Vague or no times.** Keep the source's time ranges and doneness cues ("until golden, 26–30
   minutes"). A cue on its own is fine when the source gives no time.
5. **Footnote asterisks** ("tofu*", "rice*"). Find the note the asterisk points to and put its
   content inline or in Notes. Then remove the asterisk.
6. **Duplicate parentheses or scraped junk** like "((minced))", "Pin this recipe", ad text, or
   "see photo". Clean it up.
7. **Awkward units.** Convert to kitchen units: 0.66 TBSP becomes 2 tsp, 0.375 cup becomes
   ⅓ cup + 2 tsp. Grams-only baking recipes can keep grams, with cups in the name if the
   source gives both.
8. **Inconsistent names.** "Scallions" in the ingredients but "green onion" in the steps.
   Pick one name and use it everywhere.
9. **Mislabeled "vegetarian" or "vegan" recipes** that contain chicken, beef, or fish stock,
   fish sauce, Worcestershire (anchovy), gelatin, or butter or honey (in a vegan recipe).
   Swap in a veggie-friendly equivalent and list the swap in the reply.
10. **Storage, make-ahead, substitution, and serving tips** hidden in the intro, notes, or FAQ.
    Put them in Notes, since they're valuable in the archive copy.
11. **Total time: recalculate it, don't trust the site's number.** Sites often just add up
    prep and cook time, or add every step's time together. Walk through the method as a real
    cook would, running things in parallel: the oven preheats while you prep, rice boils while
    tofu bakes, and sauce gets whisked during both. Estimate the actual elapsed time from start
    to plate and show it as "About N Minutes", rounded to 5. Tell the user when it differs a
    lot from the site's figure.
12. **Write the steps in real cooking order, with the overlap spelled out.** Start the
    longest-running item first (water to boil, oven to preheat, dough to rest). Mark parallel
    work with a green lead-in, like `<g>While tofu and rice cook:</g>`. The "Before you start"
    tip should name the first thing to get going.
13. **Unusual techniques that are intentional.** Examples: pasta-method rice (lots of water,
    drained), a no-knead dough with a tiny amount of yeast, a very high or low oven temperature.
    These look like errors but aren't. Don't "correct" them. Add a short `<g>` note in the step
    ("pasta-style; it gets drained") and a one-line explanation of why it works in Notes. Treat
    something as an error only when it clearly can't work, such as missing liquid, a
    contradiction, or an impossible quantity.

## B. HelloFresh specifics (common on meat-to-tofu conversions)

1. **Chicken or beef stock concentrate in a veggie or tofu recipe.** Change it to Veggie Stock
   Concentrate in both the ingredient grid and the steps.
2. **Missing tofu prep.** A step says "Add tofu" (often with an orphan `*`) but never drains or
   cuts it. Add: "Open and drain tofu; press out excess water with paper towels."
   Then add the right cut:
   - Photos show ground meat → "Crumble into small pieces."
   - Photos show chunks or strips → ¾-inch cubes or planks.
3. **Stock concentrate added to a dry, oiled pan.** It scorches and won't coat anything. Move
   it to after browning, with 2 TBSP of water (¼ cup for 4), and cook until absorbed or saucy.
4. **Photos show a different protein.** Keep the photos (they're the only ones available), but
   tell the user.
5. **Pantry items** (oil, salt, pepper, sugar, butter) aren't shipped. They go in the
   `pantry` string, not the ingredient grid.
6. **Tools.** Add paper towels if tofu gets pressed. Add a microwave-safe bowl if something is
   microwaved.
7. **"Veggie" tag.** Use it only once the recipe is actually vegetarian after the fixes.

## C. Real quantities for "1 unit" items

| Listed as | Card amount (2 \| 4) | Basis |
|---|---|---|
| Tofu | 14 oz \| 28 oz, "Extra-Firm Tofu" | Older HelloFresh US recipes list 14 oz blocks |
| Corn (canned) | 1 cup \| 2 cups, "Corn Kernels (drained)" | Estimate: one small drained can |
| Stock concentrate | 2 tsp \| 4 tsp | Estimate: one packet |
| Black beans / chickpeas | 1 can (15 oz) \| 2 cans | Standard can size |
| Baby lettuce / romaine heart | 1 head \| 2 heads | Whole count |
| Limes, lemons, shallots, tomatoes, scallions, buns | Keep the count | Already a real quantity |
| Spice blends with decimals | Use the amount the step actually measures | Step text wins |

When a quantity is an estimate, say so in the reply, not on the card. If the user tells you
the real sizes in their box, use those.
