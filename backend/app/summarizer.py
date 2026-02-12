from transformers import pipeline
from threading import Lock

_english_summarizer = None
_hindi_summarizer = None
_lock = Lock()


def get_english_summarizer():
    global _english_summarizer
    if _english_summarizer is None:
        with _lock:
            if _english_summarizer is None:
                _english_summarizer = pipeline(
                    "summarization",
                    model="sshleifer/distilbart-cnn-12-6",
                    device=-1
                )
    return _english_summarizer


def get_hindi_summarizer():
    global _hindi_summarizer
    if _hindi_summarizer is None:
        with _lock:
            if _hindi_summarizer is None:
                _hindi_summarizer = pipeline(
                    "summarization",
                    model="google/mt5-small",
                    device=-1
                )
    return _hindi_summarizer


def chunk_text(text, chunk_size=400):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])


def generate_summary(
    text: str,
    length="short",
    format="paragraph",
    language="english"
):
    length_map = {
        "short": (60, 30),
        "medium": (120, 60),
        "long": (200, 100),
        "detailed": (300, 150),
    }

    max_len, min_len = length_map.get(length, (120, 60))

    # Select summarizer
    if language == "hindi":
        summarizer = get_hindi_summarizer()
    else:
        summarizer = get_english_summarizer()

    # Limit input size
    text = " ".join(text.split()[:800])

    input_len = len(text.split())
    adaptive_max = min(max_len, max(30, input_len // 2))
    adaptive_min = min(min_len, adaptive_max - 5)

    result = summarizer(
        text,
        max_length=adaptive_max,
        min_length=adaptive_min,
        do_sample=False,
        truncation=True,
    )

    summary = result[0]["summary_text"]

    if format == "bullets":
        summary = "\n".join(
            f"• {s.strip()}"
            for s in summary.replace(".", ".\n").split("\n")
            if s.strip()
        )

    return summary, text
