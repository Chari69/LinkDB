# LinkDB
![Version](https://img.shields.io/badge/version-1.0.0-blueviolet) ![Ludereth](https://img.shields.io/badge/@ludereth-darkgreen) ![@chari69](https://img.shields.io/badge/@chari69-orange)

> Builds of versions 1.X.X are for testing and development purposes. The program may be unstable.

> This program was 80% vibe-coded, errors expected. It will be polished over time.

![LinkDB](/resources/screenshot.png)

LinkDB is a terminal-based program to save links (Bookmarks) and categorize in tags.

# to-do
- Folder Support
- Better search/filters
- Improvements in the main UI.
- Better documentation
- More hotkeys support

# build/run
1. Clone the repository.

2. Install Dependencies:
```bash
pip install -r requirements.txt
```

3. Run LinkDB:
```bash
textual run main.py
```

---

If you want to compile as standalone binary:
```bash
pip install nuitka
python -m nuitka --onefile main.py
```

# reset db
To reset your link database use:

```bash
python -c "from db import reset_db; reset_db()"
```