# AI-Skills

A collection of skills I have built for AI platforms and am sharing publicly. Each skill is a self-contained folder of instructions (and any supporting files) that teaches an AI assistant how to do one kind of task well. Use them as-is, adapt them to your own workflow, or use them as a starting point for your own skills.

## Repository Layout

All skills live in the [`Skills`](Skills) directory. Each skill has its own folder with a `SKILL.md` file at its root.

```
AI-Skills/
├── Skills/
│   ├── printable-recipe-card/
│   │   └── SKILL.md
│   └── <more skills as they are added>/
├── LICENSE
└── README.md
```

## Available Skills

| Skill | Description |
| --- | --- |
| [printable-recipe-card](Skills/printable-recipe-card) | Turns an online recipe (link, pasted text, screenshot, or PDF) into a clean two-page printable recipe card PDF. |

More skills will be added over time.

## Downloading a Skill

Pick whichever method fits your setup.

### Option 1: Download the whole repository as a ZIP

1. Open the repository on GitHub.
2. Click the green **Code** button, then **Download ZIP**.
3. Unzip the file. The skills are in the `Skills` folder.

### Option 2: Clone the repository

```bash
git clone https://github.com/geekbrownbear/AI-Skills.git
cd AI-Skills/Skills
```

Pull future updates with `git pull`.

### Option 3: Download a single skill

Use a sparse checkout to fetch only the skill you want:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/geekbrownbear/AI-Skills.git
cd AI-Skills
git sparse-checkout set Skills/printable-recipe-card
```

Replace `printable-recipe-card` with the name of the skill folder you want.

## Installing a Skill

### Claude (claude.ai and the Claude app)

1. Zip the skill folder so the folder itself is the top level of the ZIP and `SKILL.md` sits inside it (for example `printable-recipe-card.zip` containing `printable-recipe-card/SKILL.md`).
2. In Claude, go to **Settings** and open the **Capabilities** section.
3. Find the **Skills** area and upload the ZIP file.
4. Make sure the skill is toggled on.

Menu names can change between releases. If the layout differs, check the [Claude Help Center](https://support.claude.com) for current instructions on uploading custom skills.

### Claude Code

Copy the skill folder into one of these locations:

- Personal (available in every project): `~/.claude/skills/<skill-name>/`
- Project-specific: `<your-project>/.claude/skills/<skill-name>/`

Example:

```bash
cp -r Skills/printable-recipe-card ~/.claude/skills/
```

### Other platforms

Each skill is plain Markdown plus supporting files. For platforms that do not support skills directly, the contents of `SKILL.md` can be used as a system prompt or custom instructions.

## Contributing

Suggestions, bug reports, and improvements are welcome. Open an issue or submit a pull request.

## License

Released under the [Apache-2.0 License](LICENSE).
