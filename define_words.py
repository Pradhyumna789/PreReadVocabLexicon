import csv
import json
import os
import time
import argparse
from typing import Optional

import urllib.request
import urllib.error


API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"


def http_get(url: str, timeout: float = 10.0) -> Optional[bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "word-fetcher/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        # 404 means word not found; treat as None
        if e.code == 404:
            return None
        raise
    except urllib.error.URLError:
        return None


def parse_response(data: bytes) -> list[dict]:
    try:
        obj = json.loads(data.decode("utf-8"))
    except Exception:
        return []
    if not isinstance(obj, list):
        return []
    return obj


def extract_first_sense(entry_list: list[dict]) -> tuple[str, str, str, str]:
    # Returns (phonetic, pos, definition, example)
    phonetic = ""
    pos = ""
    definition = ""
    example = ""

    if not entry_list:
        return phonetic, pos, definition, example

    entry = entry_list[0] or {}
    phonetic = entry.get("phonetic") or ""

    meanings = entry.get("meanings") or []
    if meanings:
        m0 = meanings[0] or {}
        pos = m0.get("partOfSpeech") or ""
        defs = m0.get("definitions") or []
        if defs:
            d0 = defs[0] or {}
            definition = (d0.get("definition") or "").strip()
            example = (d0.get("example") or "").strip()

    return phonetic, pos, definition, example


def load_words(path: str) -> list[str]:
    words: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        # Accept either single-column [Word] or [Word, ...]
        for row in reader:
            if not row:
                continue
            word = (row[0] or "").strip()
            if word:
                words.append(word)
    return words


def load_done(path: str) -> set[str]:
    done: set[str] = set()
    if not os.path.exists(path):
        return done
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if row:
                done.add(row[0].strip().lower())
    return done


def append_result(path: str, word: str, phonetic: str, pos: str, definition: str, example: str) -> None:
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["Word", "Phonetic", "POS", "Definition", "Example"])
        writer.writerow([word, phonetic, pos, definition, example])


def fetch_definitions(
    input_csv: str,
    output_csv: str,
    limit: Optional[int] = None,
    delay_sec: float = 0.3,
    max_retries: int = 3,
) -> None:
    words = load_words(input_csv)
    done = load_done(output_csv)

    fetched = 0
    for word in words:
        key = word.lower()
        if key in done:
            continue
        if limit is not None and fetched >= limit:
            break

        attempt = 0
        resp: Optional[bytes] = None
        while attempt < max_retries and resp is None:
            attempt += 1
            resp = http_get(API_URL.format(urllib.parse.quote(word)))
            if resp is None:
                time.sleep(delay_sec * attempt)

        phonetic = pos = definition = example = ""
        if resp:
            entries = parse_response(resp)
            phonetic, pos, definition, example = extract_first_sense(entries)

        append_result(output_csv, word, phonetic, pos, definition, example)
        fetched += 1
        time.sleep(delay_sec)

    print(f"Wrote {fetched} definitions to {output_csv}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch definitions for words CSV using dictionaryapi.dev")
    parser.add_argument("--input", default="difficult_words.csv", help="Input CSV (default: difficult_words.csv)")
    parser.add_argument("--output", default="difficult_words_with_defs.csv", help="Output CSV")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of words to fetch (for testing)")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between requests in seconds")
    parser.add_argument("--retries", type=int, default=3, help="Max retries per word")
    args = parser.parse_args()

    fetch_definitions(
        input_csv=args.input,
        output_csv=args.output,
        limit=args.limit,
        delay_sec=args.delay,
        max_retries=args.retries,
    )


if __name__ == "__main__":
    main()


