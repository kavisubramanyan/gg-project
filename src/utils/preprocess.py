import re
from html import unescape
from typing import Dict, Any

URL = re.compile(r"https?://\S+")
RT_PREFIX = re.compile(r"^RT\s+@\w+:\s*", re.IGNORECASE)
HANDLE = re.compile(r"@\w+")
HASHTAG = re.compile(r"#([A-Za-z0-9_]+)")
WHITESPACE = re.compile(r"\s+")
HTML_ENTITY = re.compile(r"&[A-Za-z]+;")

def normalize_hashtag_token(tag: str) -> str:
    return tag.lower()

def clean_text(text: str) -> str:
    # Unescape HTML entities (&amp; etc.)
    text = unescape(text)
    # Remove RT prefix
    text = RT_PREFIX.sub("", text)
    # Drop URLs
    text = URL.sub(" ", text)
    # Normalize hashtags to plain tokens (keep content, drop '#')
    text = HASHTAG.sub(lambda m: " " + normalize_hashtag_token(m.group(1)) + " ", text)
    # Keep handles as tokens or strip — we strip since we don't use them
    text = HANDLE.sub(" ", text)
    # Collapse whitespace
    text = WHITESPACE.sub(" ", text).strip()
    return text

def preprocess_tweet(obj: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(obj)
    txt = obj.get("text", "")
    out["text"] = clean_text(txt)
    return out
