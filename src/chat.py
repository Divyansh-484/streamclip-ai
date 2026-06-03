import asyncio
import datetime
import sys
import re

# ── ANSI COLOR CODES ───────────────────────────────────
COLORS = {
    "reset":   "\033[0m",
    "cyan":    "\033[96m",
    "yellow":  "\033[93m",
    "green":   "\033[92m",
    "red":     "\033[91m",
    "magenta": "\033[95m",
    "white":   "\033[97m",
    "grey":    "\033[90m",
}

stats = {
    "total_messages": 0,
    "start_time": None,
}

async def listen(channel):
    print(f"{COLORS['magenta']}StreamClip AI — Anonymous Chat Listener{COLORS['reset']}")
    print(f"{COLORS['grey']}Connecting to #{channel}...{COLORS['reset']}")

    # 1. Connect directly to Twitch's IRC server
    reader, writer = await asyncio.open_connection('irc.chat.twitch.tv', 6667)
    
    # 2. Use the legacy anonymous login trick (justinfan + random numbers)
    writer.write(b'PASS N/A\r\n')
    writer.write(b'NICK justinfan12345\r\n')
    writer.write(f'JOIN #{channel.lower()}\r\n'.encode('utf-8'))
    await writer.drain()

    stats["start_time"] = datetime.datetime.now()
    
    print(f"\n{COLORS['green']}✓ Connected to #{channel} anonymously{COLORS['reset']}")
    print(f"{COLORS['grey']}  Listening for chat messages...{COLORS['reset']}")
    print(f"{COLORS['grey']}  Press Ctrl+C to stop{COLORS['reset']}\n")
    print(f"{'─'*60}")

    # Regex to extract the username and message from Twitch's raw IRC format
    chat_regex = re.compile(r"^:([^!]+).*?PRIVMSG #[^ ]+ :(.*)$")

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
                
            message = data.decode('utf-8', errors='ignore').strip()
            
            # 3. Twitch sends PINGs to check if you are still there. We must PONG back.
            if message.startswith("PING"):
                writer.write(b"PONG :tmi.twitch.tv\r\n")
                await writer.drain()
                continue
                
            # 4. Parse standard chat messages
            match = chat_regex.match(message)
            if match:
                stats["total_messages"] += 1
                username = match.group(1)
                content = match.group(2)
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")

                print(
                    f"{COLORS['grey']}[{timestamp}]{COLORS['reset']} "
                    f"{COLORS['cyan']}{username}{COLORS['reset']}"
                    f"{COLORS['grey']}:{COLORS['reset']} "
                    f"{COLORS['white']}{content}{COLORS['reset']}"
                )

                if stats["total_messages"] % 50 == 0:
                    elapsed = (datetime.datetime.now() - stats["start_time"]).seconds
                    rate    = stats["total_messages"] / max(elapsed, 1) * 60
                    print(
                        f"\n{COLORS['yellow']}── Stats: "
                        f"{stats['total_messages']} messages | "
                        f"{rate:.1f} msg/min | "
                        f"{elapsed}s elapsed ──{COLORS['reset']}\n"
                    )

    except asyncio.CancelledError:
        pass
    finally:
        writer.close()
        await writer.wait_closed()

if __name__ == "__main__":
    # Allow passing the channel name via terminal argument, defaulting to xqc
    channel_arg = sys.argv[1] if len(sys.argv) > 1 else "xqc"
    
    # Strip the '#' just in case it is accidentally typed in the terminal
    channel_arg = channel_arg.lstrip('#')
    
    try:
        asyncio.run(listen(channel_arg))
    except KeyboardInterrupt:
        print(f"\n{COLORS['red']}Disconnected.{COLORS['reset']}")