import yake
import re


def clean_text(text: str) -> str:
    """
    Removes noisy characters and extra spaces
    """
    text = re.sub(r"\s+", " ", text)            # normalize whitespace
    text = re.sub(r"[^\w\s]", " ", text)       # remove special chars
    return text.strip()


def split_joined_words(text: str) -> str:
    """
    Splits CamelCase and joined words
    """
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', text)
    return text


def generate_tags(text: str, language: str = "english", limit: int = 6):
    if not text or not text.strip():
        return []

    # Clean + Fix joined words
    text = clean_text(text)
    text = split_joined_words(text)

    lang_map = {
        "english": "en",
        "hindi": "hi",
    }

    yake_lang = lang_map.get(language, "en")

    # 🔥 Allow 1–2 word keywords
    kw_extractor = yake.KeywordExtractor(
        lan=yake_lang,
        n=2,              # <-- improved
        top=limit * 2,    # extract more, filter later
        dedupLim=0.8,
    )

    keywords = kw_extractor.extract_keywords(text)

    # Remove very short keywords
    cleaned = [
        kw.strip()
        for kw, score in keywords
        if len(kw.split()) <= 2 and len(kw) > 2
    ]

    return cleaned[:limit]
