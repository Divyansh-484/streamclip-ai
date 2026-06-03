import torch
from transformers import pipeline
import datetime

# ── MODEL SETUP ───────────────────────────────────────
# distilbert is lightweight (67MB) and fast enough for real-time chat
# cardiffnlp/twitter-roberta is trained on social media text
# We use twitter-roberta because Twitch chat resembles Twitter more than formal text
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

print("Loading sentiment model...")
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME,
    device=0 if torch.cuda.is_available() else -1,  # GPU if available
    truncation=True,
    max_length=128
)
print(f"✓ Model loaded on {'GPU' if torch.cuda.is_available() else 'CPU'}")

# ── LABEL MAPPING ─────────────────────────────────────
# cardiffnlp model outputs: Negative, Neutral, Positive
LABEL_COLORS = {
    "positive": "\033[92m",   # green
    "neutral":  "\033[93m",   # yellow
    "negative": "\033[91m",   # red
}
RESET = "\033[0m"

# ── HYPE KEYWORDS (Twitch-specific) ───────────────────
# These are strong positive signals regardless of sentiment score
HYPE_KEYWORDS = {
    "pog", "pogchamp", "poggers", "pogg", "pogcrazy",
    "letsgo", "lets go", "let's go", "hyper", "hype",
    "omegalul", "lul", "lmao", "lmfao", "omg",
    "clutch", "insane", "crazy", "goat", "w", "gg",
    "clip", "clip it", "clipit", "clipped", "clip that",
    "holy", "holy shit", "bro",
    "what", "no way", "noway", "no wayyy",
    "actual", "actually did", "he did it", "she did it",
    "kekw", "pepega", "monkas", "peeposad",
    "ez", "easy", "rip", "dead", "dies",
    "play", "insane play", "sick", "cracked",
    "someone clip", "please clip", "need a clip",
    "w play", "w moment", "massive w",
}

def contains_hype_keyword(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in HYPE_KEYWORDS)

def analyze(text):
    result    = sentiment_pipeline(text)[0]
    label     = result["label"].lower()
    score     = result["score"]
    is_hype   = contains_hype_keyword(text)

    # Detect explicit clip requests — always high hype
    clip_request = any(kw in text.lower() for kw in
                       ["clip", "clip it", "clip that", "someone clip", "please clip"])

    keyword_bonus = 0.35 if is_hype else 0.0
    clip_bonus    = 0.25 if clip_request else 0.0

    if label == "positive":
        hype_score = min(1.0, score * 0.7 + keyword_bonus + clip_bonus)
    elif label == "neutral":
        hype_score = min(1.0, score * 0.2 + keyword_bonus + clip_bonus)
    else:
        hype_score = min(1.0, keyword_bonus * 0.8 + clip_bonus)

    return {
        "label":        label,
        "score":        score,
        "is_hype":      is_hype,
        "clip_request": clip_request,
        "hype_score":   hype_score
    }

def format_result(username, content, result):
    color     = LABEL_COLORS.get(result["label"], RESET)
    hype_bar  = "█" * int(result["hype_score"] * 10)
    hype_bar  = hype_bar.ljust(10, "░")
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    flags = ""
    if result["is_hype"]:    flags += "  ⚡ HYPE"
    if result["clip_request"]: flags += "  🎬 CLIP REQUEST"

    return (
        f"\033[90m[{timestamp}]\033[0m "
        f"\033[96m{username}\033[0m: "
        f"{content}\n"
        f"  {color}▶ {result['label'].upper()} "
        f"({result['score']:.2f}){RESET} "
        f"| Hype [{hype_bar}] {result['hype_score']:.2f}"
        f"{flags}"
    )


# ── TEST MODE ─────────────────────────────────────────
if __name__ == "__main__":
    test_messages = [
        ("xqcfan1",    "POGGERS he actually did it"),
        ("viewer123",  "that was so bad lol"),
        ("chatter99",  "clip it clip it clip it"),
        ("lurker42",   "this is fine"),
        ("hypetrain",  "LETS GO LETS GO LETS GO"),
        ("sadchatter", "this stream is boring today"),
        ("omega99",    "OMEGALUL"),
        ("normalguy",  "what game is this"),
        ("hypemaster", "NO WAY BRO WHAT"),
        ("clipper11",  "someone clip that insane play"),
    ]

    print("\n" + "═"*60)
    print("  SENTIMENT ANALYSIS TEST")
    print("═"*60 + "\n")

    for username, message in test_messages:
        result = analyze(message)
        print(format_result(username, message, result))
        print()