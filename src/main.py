import asyncio
import datetime
import sys
import re
import os
from sentiment import analyze, format_result
from hype import HypeDetector

# ── CONFIG ────────────────────────────────────────────
IRC_HOST = "irc.chat.twitch.tv"
IRC_PORT = 6667

COLORS = {
    "reset":   "\033[0m",
    "cyan":    "\033[96m",
    "yellow":  "\033[93m",
    "green":   "\033[92m",
    "red":     "\033[91m",
    "magenta": "\033[95m",
    "white":   "\033[97m",
    "grey":    "\033[90m",
    "bold":    "\033[1m",
}

# ── STATS ─────────────────────────────────────────────
stats = {
    "total_messages": 0,
    "total_clips":    0,
    "start_time":     None,
}

chat_regex = re.compile(r"^:([^!]+).*?PRIVMSG #[^ ]+ :(.*)$")

def print_header(channel):
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{COLORS['bold']}{COLORS['magenta']}")
    print("  ╔══════════════════════════════════════╗")
    print("  ║        StreamClip AI  v1.0           ║")
    print("  ║   Real-time Hype Detection Engine    ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"{COLORS['reset']}")
    print(f"  Channel  : {COLORS['cyan']}#{channel}{COLORS['reset']}")
    print(f"  Started  : {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"  Mode     : Live sentiment + hype detection")
    print(f"\n  {COLORS['grey']}Press Ctrl+C to stop{COLORS['reset']}\n")
    print("─" * 60)

async def run(channel):
    print(f"{COLORS['yellow']}Loading sentiment model...{COLORS['reset']}")
    detector = HypeDetector()
    stats["start_time"] = datetime.datetime.now()

    print(f"{COLORS['yellow']}Connecting to #{channel}...{COLORS['reset']}")
    reader, writer = await asyncio.open_connection(IRC_HOST, IRC_PORT)

    # Anonymous IRC login
    writer.write(b"PASS N/A\r\n")
    writer.write(b"NICK justinfan99999\r\n")
    writer.write(f"JOIN #{channel.lower()}\r\n".encode())
    await writer.drain()

    print_header(channel)

    try:
        async for data in reader:
            line = data.decode("utf-8", errors="ignore").strip()

            # Keep connection alive
            if line.startswith("PING"):
                writer.write(b"PONG :tmi.twitch.tv\r\n")
                await writer.drain()
                continue

            match = chat_regex.match(line)
            if not match:
                continue

            username = match.group(1)
            content  = match.group(2)
            stats["total_messages"] += 1

            # Analyze sentiment
            result = analyze(content)

            # Print message with sentiment
            print(format_result(username, content, result))

            # Feed into hype detector
            hype_result = detector.add_message(username, content, result)

            # Print live hype bar
            print(detector.status_line(hype_result), end="", flush=True)

            # Clip moment detected
            if hype_result["should_clip"]:
                stats["total_clips"] += 1
                detector.clip_alert(hype_result)
                log_clip(channel, hype_result, username, content)

    except asyncio.CancelledError:
        pass
    finally:
        writer.close()
        print_summary()


def log_clip(channel, hype_result, username, content):
    """
    Logs clip moments to a file for later review.
    """
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"[{timestamp}] Channel: #{channel} | "
        f"Hype: {hype_result['hype_score']:.3f} | "
        f"Msgs/30s: {hype_result['message_count']} | "
        f"Clip Reqs: {hype_result['clip_requests']} | "
        f"Trigger msg: {content[:50]}\n"
    )
    with open("outputs/clip_log.txt", "a") as f:
        f.write(log_entry)
    print(f"\n  {COLORS['grey']}✓ Logged to outputs/clip_log.txt{COLORS['reset']}")


def print_summary():
    elapsed = (datetime.datetime.now() - stats["start_time"]).seconds
    print(f"\n\n{'═'*60}")
    print(f"{COLORS['bold']}  SESSION SUMMARY{COLORS['reset']}")
    print(f"{'═'*60}")
    print(f"  Duration:       {elapsed//60}m {elapsed%60}s")
    print(f"  Messages:       {stats['total_messages']:,}")
    print(f"  Clips detected: {stats['total_clips']}")
    if elapsed > 0:
        rate = stats["total_messages"] / elapsed * 60
        print(f"  Chat rate:      {rate:.0f} msg/min")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    channel = sys.argv[1] if len(sys.argv) > 1 else "xqc"
    channel = channel.lstrip("#")
    try:
        asyncio.run(run(channel))
    except KeyboardInterrupt:
        pass