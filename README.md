## Difficult Word Extractor + Definitions

Extract rare/difficult vocabulary from a novel and optionally fetch dictionary definitions in bulk.

### What this does
- Ingest AntConc word-list exports (or multiple exports) and merge them.
- Filter out common English words using NGSL (New General Service List).
- Preserve hyphenated words (e.g., half-reproachful).
- Apply simple lemmatization (e.g., thought→think, seen→see) to improve filtering.
- Output a clean, single-column CSV of difficult words.
- Optionally fetch definitions for those words via a free dictionary API.

### Files in this project
- `word.py`: merges AntConc exports and generates `difficult_words.csv`.
- `define_words.py`: fetches definitions and generates `difficult_words_with_defs.csv`.
- `NGSL_1.2_stats.csv`: NGSL list used to remove common words.
- `Word_results_*.txt`: your AntConc exports (one or many) with columns like `Headword` and `Freq`.
-  I also included the book's pdf slaughter house five

---

## Prerequisites
- Python 3.10+ installed (Linux/macOS/Windows).
- Your novel analyzed in AntConc, exported as text tables with headers including `Headword` and `Freq`.
- Place all files in the same directory (e.g., your Desktop).

No extra Python packages are required (uses the standard library only).

---

## Quick Start
1) Put AntConc exports next to the scripts
- Save your word lists from AntConc as `Word_results_1.txt`, `Word_results_2.txt`, etc. (tab- or space-separated is fine).
- Make sure the first line includes headers (e.g., `Type\tPOS\tHeadword\tRank\tFreq...`).

2) Generate difficult words
```bash
python3 /home/shocker/Desktop/word.py
```
Output:
- `difficult_words.csv` with a header `Word` and one word per line (no frequencies).

3) (Optional) Fetch definitions for those words
```bash
python3 /home/shocker/Desktop/define_words.py --limit 50
# Remove --limit to fetch all
```
Output:
- `difficult_words_with_defs.csv` with columns: `Word, Phonetic, POS, Definition, Example`.

---

## Details and Options
### `word.py`
Behavior:
- Merges all files matching `Word_results_*.txt` (and `Word_results.txt` if present).
- Picks the `Headword` and `Freq` columns; tolerates tabs/spaces.
- Normalizes words (lowercase, keeps hyphens, strips possessives).
- Filters NGSL words using `NGSL_1.2_stats.csv` (first column of lemmas).
- Applies a small lemmatizer (e.g., thought→think, men→man) to catch inflected forms.
- Applies a frequency ceiling to drop very frequent tokens/names.

To re-run:
```bash
python3 /home/shocker/Desktop/word.py
```

Tips:
- If you want fewer words, raise filtering (e.g., increase strictness or lower frequency ceiling inside `word.py`).
- To exclude specific proper nouns, add them to the `stoplist` inside `word.py`.

### `define_words.py`
Behavior:
- Reads `difficult_words.csv` (single column `Word`).
- Calls `https://api.dictionaryapi.dev/api/v2/entries/en/<word>` with retries and a delay to be polite.
- Appends results to `difficult_words_with_defs.csv`, so you can safely re-run and resume.

Common flags:
```bash
python3 /home/shocker/Desktop/define_words.py \
  --input /home/shocker/Desktop/difficult_words.csv \
  --output /home/shocker/Desktop/difficult_words_with_defs.csv \
  --limit 200 \
  --delay 0.4 \
  --retries 3
```

Notes:
- The free API sometimes returns sparse data; the script still records the row so future runs won’t duplicate work.
- You can open/edit the CSV in any spreadsheet app and then import to Anki if you want flashcards.

---

## Getting the AntConc export (reminder)
1) Open AntConc → Word tab.
2) Load your `.txt` novel/file(s).
3) Click Start to build the list.
4) Export the table (include headers) as a text file, name like `Word_results_1.txt`.
5) Repeat if you have multiple sources; place them next to the scripts.

---

## Troubleshooting
- Nothing shows up / only names appear
  - Ensure you exported the full list from AntConc (not just top 100).
  - Re-run `word.py` after adding more `Word_results_*.txt` files.
  - Check that `NGSL_1.2_stats.csv` is present in the same folder.

- Definitions feel slow or frozen
  - Use `--limit 50` to test quickly.
  - Increase `--delay` to avoid transient API throttling; re-run to resume.

- I need different filtering
  - Open `word.py` and adjust `FREQ_MAX`, update `stoplist`, or add more mappings in the lemmatizer.

---

## Example session

### Upload a pdf file of your book => File => Open File 
### Select Word and click on start
<img width="1352" height="804" alt="image" src="https://github.com/user-attachments/assets/e352f15d-9de5-4367-956c-1447e400f143" />


![photo_2025-10-03_01-52-31](https://github.com/user-attachments/assets/324267d3-8576-401e-a63b-5ddd28f6fee7)


<img width="1426" height="810" alt="Screenshot from 2025-10-03 01-51-44" src="https://github.com/user-attachments/assets/8fb29ff1-6630-42f8-a16a-d163c41c6de0" />


https://github.com/user-attachments/assets/1ee70ccd-1c6f-497a-983c-35aa6d52b002


```bash
# 1) Generate difficult words from multiple exports
python3 /home/shocker/Desktop/word.py

# 2) Fetch first 100 definitions (test)
python3 /home/shocker/Desktop/define_words.py --limit 100

# 3) Fetch the rest later (resume-safe)
python3 /home/shocker/Desktop/define_words.py
```

---
