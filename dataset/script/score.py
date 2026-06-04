import re

# Common English/function words that appear in code-mixed text
ENGLISH_LEAKAGE = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "had",
    "her", "was", "one", "our", "out", "day", "get", "has", "him", "his",
    "how", "man", "new", "now", "old", "see", "two", "way", "who", "boy",
    "did", "its", "let", "put", "say", "she", "too", "use", "control",
    "super", "isbn", "http", "https", "doi", "www", "com", "org", "xd",
    "lol", "omg", "wtf", "fyi", "btw", "imo", "imho", "aka", "etc", "vs",
    "ie", "eg", "et", "al", "op", "cit", "ibid", "vol", "pp", "ed",
    "eds", "trans", "rev", "press", "university", "college", "institute",
    "foundation", "center", "centre", "school", "academy", "academic",
    "journal", "review", "quarterly", "annals", "proceedings", "symposium",
    "conference", "workshop", "seminar", "lecture", "thesis", "dissertation",
    "monograph", "bibliography", "catalogue", "catalog", "index", "abstract",
    "summary", "introduction", "preface", "foreword", "appendix", "glossary",
    "bibliography", "references", "notes", "footnote", "endnote", "citation",
    "cite", "cited", "quotation", "quote", "excerpt", "extract", "passage",
    "paragraph", "section", "chapter", "volume", "book", "page", "pages",
    "line", "lines", "figure", "figures", "table", "tables", "diagram",
    "chart", "graph", "map", "plate", "illustration", "photo", "photograph",
    "image", "picture", "drawing", "sketch", "plan", "scheme", "model",
    "sample", "specimen", "example", "instance", "case", "cases", "item",
    "items", "piece", "pieces", "part", "parts", "portion", "section",
    "segment", "fragment", "bit", "bits", "unit", "units", "element",
    "component", "constituent", "ingredient", "factor", "aspect", "facet",
    "feature", "characteristic", "quality", "property", "attribute", "trait",
    "mark", "sign", "symbol", "token", "emblem", "badge", "brand", "label",
    "tag", "stamp", "seal", "imprint", "impression", "print", "printing",
    "edition", "version", "copy", "issue", "number", "num", "no", "nos",
    "vol", "pg", "p", "pp", "ff", "et", "seq", "sq", "sqq", "passim",
    "ibid", "op", "cit", "loc", "cit", "supra", "infra", "ante", "post",
    "contra", "inter", "intra", "extra", "infra", "ultra", "supra", "hyper",
    "meta", "para", "per", "pro", "re", "sub", "trans", "vice", "versa",
    "ad", "hoc", "bono", "fide", "hoc", "lib", "raison", "dêtre", "tour",
    "de", "force", "en", "masse", "passé", "façon", "de", "parler", "agent",
    "provocateur", "cause", "célèbre", "coup", "détat", "coup", "de",
    "grâce", "cri", "coeur", "double", "entendre", "esprit", "escalier",
    "fait", "accompli", "faux", "pas", "haute", "couture", "hors", "concours",
    "je", "ne", "sais", "quoi", "laissez", "faire", "passer", "mal", "de",
    "mer", "ménage", "trois", "noblesse", "oblige", "nom", "plume", "nuit",
    "blanche", "pièce", "résistance", "raison", "détre", "sang", "froid",
    "savoir", "faire", "tour", "de", "force", "tout", "de", "suite", "vieux",
    "jeu", "vis", "comica", "volte", "face", "id", "eg", "etc", "et", "al",
    "ibid", "op", "cit", "loc", "cit", "passim", "viz", "sc", "vs", "ca",
    "circa", "cf", "confer", "cp", "compare", "do", "ditto", "et", "seq",
    "et", "seqq", "fl", "floruit", "f", "folio", "ff", "folios", "fn",
    "footnote", "ib", "ibidem", "id", "idem", "l", "line", "ll", "lines",
    "loc", "cit", "loco", "citato", "log", "logarithm", "mo", "month",
    "mod", "modo", "nem", "con", "nemine", "contradicente", "nem", "dis",
    "nemine", "dissentiente", "no", "number", "nos", "numbers", "op", "cit",
    "opere", "citato", "p", "page", "pp", "pages", "par", "paragraph",
    "pt", "part", "pub", "published", "publisher", "q", "quart", "qto",
    "quarto", "qv", "quod", "vide", "re", "regarding", "recto", "r", "right",
    "r", "recto", "rs", "right", "side", "s", "solidus", "sc", "scilicet",
    "scil", "scilicet", "sec", "second", "sect", "section", "seq", "sequentia",
    "s", "shilling", "sic", "sic", "sign", "signed", "sin", "sine", "sp",
    "spelling", "ss", "sections", "st", "stanza", "stat", "immediately",
    "subl", "sublimated", "sup", "supra", "sup", "above", "supp", "supplement",
    "s", "shilling", "syn", "synonym", "t", "time", "temp", "temperature",
    "tit", "title", "trans", "translated", "translator", "trans", "transpose",
    "u", "unit", "ult", "ultimo", "ut", "dict", "ut", "supra", "v", "see",
    "v", "verb", "v", "versus", "v", "vide", "v", "volume", "v", "vowel",
    "verso", "v", "left", "vide", "see", "viz", "videlicet", "vol", "volume",
    "v", "volume", "vs", "versus", "wt", "weight", "xn", "christian", "name",
    "yd", "yard", "yr", "year", "yrs", "years",
}

def is_english_leakage(text: str) -> bool:
    """Check if text contains significant English or French loanwords that indicate contamination."""
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    if not words:
        return False
    
    english_count = sum(1 for w in words if w in ENGLISH_LEAKAGE)
    return english_count / len(words) > 0.15  # More than 15% English words


def clean_malagasy(text: str) -> str | None:
    if not text:
        return None

    text = text.strip()
    
    # Length check
    words = text.split()
    if len(words) < 3 or len(text) < 15:
        return None

    # Drop obvious metadata / garbage
    if re.search(r"(ISBN|doi:|http|https|www\.|@\w+|#\w+)", text, re.I):
        return None

    # Drop lines that are mostly non-letters
    letters = len(re.findall(r"[A-Za-zÀ-ÿ]", text))
    if letters / len(text) < 0.4:
        return None

    # Drop English/French contamination
    if is_english_leakage(text):
        return None

    # Fix hyphenation artifacts
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Drop unmatched quotes or brackets (likely truncated)
    if text.count('"') % 2 != 0:
        # Only drop if it's not a common Malagasy quotation pattern
        if not re.search(r'"\w+', text):
            return None
    
    # Penalize excessive repetition (stuttering artifacts like "nanananananana")
    if re.search(r'(\w{2,})\1{3,}', text):
        return None

    return text