# StreamClip AI

Real-time Twitch chat analysis engine that detects hype moments 
using NLP sentiment analysis. Identifies when chat activity spikes 
significantly above baseline — the moments worth clipping.

## How It Works

Live Twitch Chat (IRC)
↓
Sentiment Analysis (RoBERTa, GPU-accelerated)
↓
Hype Scoring (keyword detection + model confidence)
↓
Spike Detection (recent vs baseline comparison)
↓
Clip Moment Alert + Timestamp Log

## Architecture

- **chat.py** — Anonymous Twitch IRC listener. Handles 400+ msg/min without dropping events.
- **sentiment.py** — RoBERTa model trained on 124M tweets. Chosen over general-purpose models because Twitch chat resembles Twitter linguistically.
- **hype.py** — Sliding window spike detector. Compares recent 5-second hype against 30-second baseline. Triggers when recent activity is 60%+ above baseline.
- **auth.py** — Twitch Helix API integration for stream metadata.
- **main.py** — Full pipeline with session logging.

## Key Design Decisions

**Why spike detection over fixed threshold?**  
High-volume channels have a naturally elevated sentiment baseline. 
A fixed threshold triggers constantly on large channels and never 
on small ones. Relative spike detection adapts to each channel automatically.

**Why anonymous IRC over OAuth?**  
StreamClip only needs read access to public chat. Anonymous IRC 
gives full read access without token management or expiry handling.

**Why RoBERTa over DistilBERT?**  
RoBERTa-twitter achieves higher accuracy on informal social media 
text. Twitch chat contains heavy abbreviations, emotes, and internet 
slang that general-purpose models misclassify.

## Validated Performance

Tested on CaseOh's stream (334 msg/min):
- Runtime: 21 minutes | Messages processed: 7,269
- Clips detected: 2 (~1 per 10 minutes)
- Zero dropped messages at peak load

## Known Limitations

- Chat delay (5–15s) means timestamps are approximate
- Text-only signal cannot assess video/audio clip quality
- Requires VOD to be saved for timestamp navigation

## Roadmap

- [ ] Unique user weighting (anti-spam)
- [ ] Direct Twitch VOD timestamp links  
- [ ] Discord webhook notifications
- [ ] Post-stream VOD analysis mode
- [ ] Streamlit dashboard

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install requests python-dotenv transformers torch websockets
```

Add to `.env`:

TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret

## Usage

```bash
python src/main.py xqc
python src/main.py caseoh
python src/main.py shroud
```

## Tech Stack
Python · PyTorch · HuggingFace Transformers · Twitch IRC · Twitch Helix API · RoBERTa