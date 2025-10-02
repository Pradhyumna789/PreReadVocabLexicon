import csv
import re
import glob
import os


def normalize_word(raw: str) -> str:
    """Lowercase, keep letters and internal hyphens, strip possessive, and tidy."""
    lowered = raw.lower()
    # strip trailing possessive 's or ’s
    lowered = re.sub(r"(’s|'s)$", "", lowered)
    # keep a-z and hyphen only
    cleaned = re.sub(r"[^a-z-]", " ", lowered)
    # collapse multiple hyphens/spaces around hyphens
    cleaned = re.sub(r"\s*-+\s*", "-", cleaned)
    cleaned = cleaned.strip("-").strip()
    return cleaned


def parse_word_results(path: str) -> list[tuple[str, float]]:
    words_and_freqs: list[tuple[str, float]] = []
    with open(path, "r", encoding="utf-8") as file_handle:
        header_line = file_handle.readline()
        if not header_line:
            return words_and_freqs

        # Detect delimiter: prefer tab if present, else split on whitespace
        if "\t" in header_line:
            header_parts = [h.strip() for h in header_line.strip().split("\t")]
            splitter = "\t"
        else:
            header_parts = header_line.strip().split()
            splitter = None  # means use .split() later

        # Identify column indices. Use 'Headword' if present, else fallback to 'Type'.
        try:
            freq_idx = header_parts.index("Freq")
        except ValueError:
            # If header missing or mislabeled, attempt to infer: assume last numeric column is Freq
            freq_idx = -1

        headword_idx = header_parts.index("Headword") if "Headword" in header_parts else None
        type_idx = header_parts.index("Type") if "Type" in header_parts else 0

        for line in file_handle:
            line = line.strip()
            if not line:
                continue

            if splitter:
                parts = [p.strip() for p in line.split(splitter)]
            else:
                parts = line.split()

            if not parts:
                continue

            # Best-effort determine frequency
            freq_value: float | None = None
            if freq_idx != -1 and len(parts) > freq_idx:
                try:
                    freq_value = float(parts[freq_idx])
                except ValueError:
                    freq_value = None
            if freq_value is None:
                # Try: find last numeric token in the row
                for token in reversed(parts):
                    try:
                        freq_value = float(token)
                        break
                    except ValueError:
                        continue

            if freq_value is None:
                continue

            # Choose the word column: prefer Headword if present and non-empty, else Type
            word_raw = None
            if headword_idx is not None and len(parts) > headword_idx and parts[headword_idx]:
                word_raw = parts[headword_idx]
            elif type_idx is not None and len(parts) > type_idx:
                word_raw = parts[type_idx]

            if not word_raw:
                continue

            word = normalize_word(word_raw)
            if not word:
                continue

            words_and_freqs.append((word, freq_value))

    return words_and_freqs


def load_ngsl_set(path: str) -> set[str]:
    ngsl: set[str] = set()
    with open(path, "r", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader, None)
        for row in reader:
            if not row:
                continue
            lemma = row[0].strip().lower()
            if lemma:
                ngsl.add(lemma)
    return ngsl


def lemmatize_simple(word: str, ngsl: set[str]) -> str:
    """Very small lemmatizer to map common inflections to lemmas for NGSL matching."""
    if not word:
        return word

    # Irregulars and pronouns mapping
    irregular_map = {
        "was": "be",
        "were": "be",
        "been": "be",
        "am": "be",
        "is": "be",
        "are": "be",
        "has": "have",
        "had": "have",
        "did": "do",
        "done": "do",
        "does": "do",
        "said": "say",
        "made": "make",
        "went": "go",
        "gone": "go",
        "goes": "go",
        "got": "get",
        "gotten": "get",
        "came": "come",
        "come": "come",
        "told": "tell",
        "saw": "see",
        "seen": "see",
        "thought": "think",
        "thinking": "think",
        "knew": "know",
        "known": "know",
        "took": "take",
        "taken": "take",
        "gave": "give",
        "given": "give",
        "found": "find",
        "left": "leave",
        "felt": "feel",
        "kept": "keep",
        "held": "hold",
        "bought": "buy",
        "brought": "bring",
        "became": "become",
        "began": "begin",
        "begun": "begin",
        "ran": "run",
        "wrote": "write",
        "written": "write",
        "spoke": "speak",
        "spoken": "speak",
        "sat": "sit",
        "stood": "stand",
        "led": "lead",
        "lost": "lose",
        "paid": "pay",
        "met": "meet",
        "men": "man",
        "eyes": "eye",
        "eyes": "eye",
        # Pronouns
        "me": "i",
        "my": "i",
        "mine": "i",
        "us": "we",
        "our": "we",
        "ours": "we",
        "him": "he",
        "his": "he",
        "her": "she",
        "hers": "she",
        "them": "they",
        "their": "they",
        "theirs": "they",
        "you": "you",
        "your": "you",
        "yours": "you",
    }

    if word in irregular_map:
        return irregular_map[word]

    # Try simple verb endings if resulting lemma exists in NGSL
    candidates = [word]
    if word.endswith("ies"):
        candidates.append(word[:-3] + "y")
    if word.endswith("es"):
        candidates.append(word[:-2])
    if word.endswith("s") and len(word) > 3:
        candidates.append(word[:-1])
    if word.endswith("ed") and len(word) > 3:
        candidates.append(word[:-2])
        candidates.append(word[:-1])
    if word.endswith("ing") and len(word) > 4:
        candidates.append(word[:-3])
        candidates.append(word[:-3] + "e")

    for cand in candidates:
        if cand in ngsl:
            return cand

    return word


def collect_word_result_files() -> list[str]:
    candidates: list[str] = []
    # Include canonical file if present
    if os.path.exists("Word_results.txt"):
        candidates.append("Word_results.txt")
    # Include all numbered exports
    candidates.extend(sorted(glob.glob("Word_results_*.txt")))
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for p in candidates:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def parse_and_merge(paths: list[str]) -> list[tuple[str, float]]:
    aggregate: dict[str, float] = {}
    for p in paths:
        for word, freq in parse_word_results(p):
            aggregate[word] = aggregate.get(word, 0.0) + float(freq)
    # Convert to list of tuples
    merged = list(aggregate.items())
    return merged


input_files = collect_word_result_files()
words_freq = parse_and_merge(input_files) if input_files else parse_word_results("Word_results.txt")
ngsl_words = load_ngsl_set("NGSL_1.2_stats.csv")

# Basic stoplist for function words and numerals not fully covered by NGSL
stoplist = {
    "a", "an", "the", "and", "or", "but", "if", "so", "to", "of", "in", "on", "at", "by", "for", "from", "as",
    "i", "me", "my", "you", "your", "we", "our", "he", "him", "his", "she", "her", "it", "its", "they", "them", "their",
    "is", "am", "are", "was", "were", "be", "been", "being", "do", "did", "done", "have", "has", "had",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "hundred", "thousand",
    "de", "s"
}

# Frequency ceiling to drop frequent names/common tokens (tune as needed)
FREQ_MAX = 1000.0

rare_words: list[tuple[str, float]] = []
for word, freq in words_freq:
    # frequency filter first
    if freq > FREQ_MAX:
        continue
    # normalize token and re-check
    norm = normalize_word(word)
    if not norm or len(norm) < 3:
        continue
    if norm in stoplist:
        continue
    # NGSL checks (surface and simple lemma)
    if norm in ngsl_words:
        continue
    lemma = lemmatize_simple(norm, ngsl_words)
    if lemma in ngsl_words:
        continue
    rare_words.append((norm, freq))

# Sort by frequency ascending (rarest first)
rare_words.sort(key=lambda pair: pair[1])

with open("difficult_words.csv", "w", newline="", encoding="utf-8") as out_csv:
    writer = csv.writer(out_csv)
    writer.writerow(["Word"])
    for word, _freq in rare_words:
        writer.writerow([word])

print(f"{len(rare_words)} difficult words saved to difficult_words.csv")

