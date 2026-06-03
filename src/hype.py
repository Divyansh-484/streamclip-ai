import time
import datetime
from collections import deque

# ── CONFIG ────────────────────────────────────────────
WINDOW_SECONDS     = 30
MIN_MESSAGES       = 5
HYPE_THRESHOLD     = 0.60   # now means: recent is 60% higher than baseline
COOLDOWN_SECONDS   = 60
CLIP_REQUEST_BONUS = 0.15

# ── ANSI COLORS ───────────────────────────────────────
RESET  = "\033[0m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"

class HypeDetector:
    def __init__(self):
        # Each entry: {"timestamp": float, "hype_score": float,
        #              "username": str, "content": str, "clip_request": bool}
        self.window        = deque()
        self.last_clip_time = 0
        self.total_clips   = 0
        self.peak_hype     = 0.0

    def add_message(self, username, content, sentiment_result):
        now = time.time()

        # Add new message to window
        self.window.append({
            "timestamp":    now,
            "hype_score":   sentiment_result["hype_score"],
            "username":     username,
            "content":      content,
            "clip_request": sentiment_result.get("clip_request", False)
        })

        # Remove messages older than WINDOW_SECONDS
        while self.window and (now - self.window[0]["timestamp"]) > WINDOW_SECONDS:
            self.window.popleft()

        return self._evaluate()

    def _evaluate(self):
        now = time.time()

        if len(self.window) < MIN_MESSAGES:
            return {
                "should_clip":        False,
                "hype_score":         0.0,
                "spike_score":        0.0,
                "reason":             f"Not enough messages ({len(self.window)}/{MIN_MESSAGES})",
                "message_count":      len(self.window),
                "clip_requests":      0,
                "cooldown_active":    False,
                "cooldown_remaining": 0,
                "peak_hype":          self.peak_hype,
                "total_clips":        self.total_clips
            }

        messages = list(self.window)

        # Split window: last 5 seconds (recent) vs rest (baseline)
        recent = [m["hype_score"] for m in messages
                  if (now - m["timestamp"]) <= 5]
        baseline = [m["hype_score"] for m in messages
                    if (now - m["timestamp"]) > 5]

        avg_recent = sum(recent) / len(recent) if recent else 0
        avg_baseline = sum(baseline) / len(baseline) if baseline else 0.1

        # Spike = how much recent hype exceeds baseline
        spike_score = max(0, (avg_recent - avg_baseline) / max(avg_baseline, 0.1))

        # Also count clip requests in last 5 seconds
        recent_clip_requests = sum(
            1 for m in messages
            if m["clip_request"] and (now - m["timestamp"]) <= 5
        )
        clip_bonus = min(0.5, recent_clip_requests * 0.15)

        final_spike = min(1.0, spike_score + clip_bonus)

        # Update peak
        self.peak_hype = max(self.peak_hype, final_spike)

        # Cooldown check
        cooldown_active = (now - self.last_clip_time) < COOLDOWN_SECONDS
        cooldown_remaining = max(0, COOLDOWN_SECONDS - (now - self.last_clip_time))

        # Trigger: spike must be significant AND recent hype above minimum floor
        should_clip = (
            final_spike >= HYPE_THRESHOLD and
            avg_recent >= 0.45 and        # floor: recent msgs must be genuinely hype
            len(recent) >= 3 and           # need at least 3 msgs in last 5 seconds
            not cooldown_active
        )

        if should_clip:
            self.last_clip_time = now
            self.total_clips += 1

        return {
            "should_clip":        should_clip,
            "hype_score":         final_spike,
            "spike_score":        spike_score,
            "avg_recent":         avg_recent,
            "avg_baseline":       avg_baseline,
            "message_count":      len(self.window),
            "clip_requests":      recent_clip_requests,
            "cooldown_active":    cooldown_active,
            "cooldown_remaining": cooldown_remaining,
            "peak_hype":          self.peak_hype,
            "total_clips":        self.total_clips
        }

    def get_hype_bar(self, score):
        filled = int(score * 20)
        bar    = "█" * filled + "░" * (20 - filled)
        if score >= HYPE_THRESHOLD:
            color = GREEN
        elif score >= HYPE_THRESHOLD * 0.7:
            color = YELLOW
        else:
            color = RED
        return f"{color}[{bar}]{RESET} {score:.3f}"

    def status_line(self, result):
      timestamp = datetime.datetime.now().strftime("%H:%M:%S")
      bar       = self.get_hype_bar(result["hype_score"])
      msgs      = result["message_count"]
      recent    = result.get("avg_recent", 0)
      baseline  = result.get("avg_baseline", 0)

      line = (
          f"\r{CYAN}[{timestamp}]{RESET} "
          f"Spike: {bar} | "
          f"Recent: {recent:.2f} vs Base: {baseline:.2f} | "
          f"Msgs: {msgs}/30s"
      )
  
      if result["cooldown_active"]:
          line += f" | {YELLOW}CD: {result['cooldown_remaining']:.0f}s{RESET}"

      return line

    def clip_alert(self, result):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\n\n{'═'*60}")
        print(f"{BOLD}{GREEN}  🎬 CLIP MOMENT DETECTED  #{result['total_clips']}{RESET}")
        print(f"{'═'*60}")
        print(f"  Time:          {timestamp}")
        print(f"  Hype Score:    {result['hype_score']:.3f} "
              f"(threshold: {HYPE_THRESHOLD})")
        print(f"  Messages/30s:  {result['message_count']}")
        print(f"  Clip Requests: {result['clip_requests']}")
        print(f"  Peak Hype:     {result['peak_hype']:.3f}")
        print(f"{'═'*60}\n")


# ── SIMULATION TEST ───────────────────────────────────
if __name__ == "__main__":
    from sentiment import analyze
    import random

    detector = HypeDetector()

    # Simulate a stream with a hype spike in the middle
    normal_messages = [
        ("viewer1",  "this is pretty good"),
        ("viewer2",  "lol ok"),
        ("viewer3",  "what game is this"),
        ("viewer4",  "nice"),
        ("viewer5",  "ok"),
    ]
    hype_messages = [
        ("hype1",  "POGGERS POGGERS POGGERS"),
        ("hype2",  "LETS GO LETS GO"),
        ("hype3",  "clip it clip it"),
        ("hype4",  "NO WAY BRO"),
        ("hype5",  "OMEGALUL insane"),
        ("hype6",  "someone clip that"),
        ("hype7",  "LETS GOOOO"),
        ("hype8",  "POGCHAMP"),
        ("hype9",  "clip that clip that"),
        ("hype10", "holy shit"),
        ("hype11", "W W W W"),
        ("hype12", "KEKW KEKW"),
        ("hype13", "actual clip moment"),
        ("hype14", "POGGERS"),
        ("hype15", "insane play bro"),
    ]

    print(f"\n{BOLD}StreamClip AI — Hype Detection Simulation{RESET}")
    print(f"Threshold: {HYPE_THRESHOLD} | Window: {WINDOW_SECONDS}s | "
          f"Cooldown: {COOLDOWN_SECONDS}s\n")
    print("Phase 1: Normal chat...")

    # Phase 1: normal chat (15 messages)
    for i in range(15):
        msg = random.choice(normal_messages)
        result = detector.add_message(msg[0], msg[1], analyze(msg[1]))
        print(detector.status_line(result), end="", flush=True)
        time.sleep(0.3)

    print("\n\nPhase 2: HYPE SPIKE incoming...")
    time.sleep(0.5)

    # Phase 2: hype spike
    for msg in hype_messages:
        result = detector.add_message(msg[0], msg[1], analyze(msg[1]))
        print(detector.status_line(result), end="", flush=True)

        if result["should_clip"]:
            detector.clip_alert(result)

        time.sleep(0.2)

    print(f"\n\n{BOLD}Simulation complete.{RESET}")
    print(f"Peak hype: {detector.peak_hype:.3f}")
    print(f"Clips triggered: {detector.total_clips}")