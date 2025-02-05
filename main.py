"""Words on Stream auto solver"""

from json import loads as json_loads
from time import sleep
from queue import Empty
from ws_listener import WSListener, WebSocketMessage
from bot import WosBot
from unscrambler import unscramble

# Each of these profiles must have a Twitch login,
# and a recent Words of Stream login.

# Chrome profile to use for Websocket listener
CHROME_PROFILE_LISTENER = "Default"

# Firefox profiles root folder paths to use for bots
# Leave empty to only spawn listener
FIREFOX_BOT_PROFILES = []

# Turn off headless in order to debug listener profile
HEADLESS_LISTENER = False

# Turn off headless in order to debug bot profiles
HEADLESS_BOTS = False


def _get_packet(payload: str) -> dict:
    if not payload.startswith("42"):
        return None

    packet = payload.split(",", maxsplit=2)[2].rstrip("]")
    return json_loads(packet)


def _event_loop(bot_pool: list[WosBot], ws: WSListener) -> None:

    current_letters = None
    wordlists = []

    while True:
        sleep(0.01)

        try:
            message: WebSocketMessage = ws.messages.get_nowait()
        except Empty:
            continue

        if not message.url.startswith("wss://wos2.gartic.es/socket.io"):
            continue

        packet = _get_packet(message.payload)
        if packet is None or "uid" in packet:
            continue

        if "level" in packet:
            # New level detected
            current_letters = "".join(packet["letters"])
            print(f"\nLevel {packet['level']} started, letters -> [{current_letters}]")
            # Get unscrambled wordlists
            words = unscramble(current_letters)
            # Split wordlist for each bot
            wordlists = [words[i :: len(bot_pool)] for i in range(len(bot_pool))]
            print(f"\nSending wordlists to bots: {wordlists}")

            # Notify bots to send their words
            for bot, words in zip(bot_pool, wordlists):
                for word in words:
                    bot.send_word(word)
        elif "falseLetters" in packet:
            # Remove false letters
            if current_letters is None:
                continue

            # Remove false letters
            new_letters = list(current_letters)
            for letter in packet["falseLetters"]:
                new_letters.remove(letter)
            current_letters = "".join(new_letters)

            print(
                f"\nFalse letters: {packet['falseLetters']}, new letters: {current_letters}"
            )
            # Update wordlists
            words = unscramble(current_letters)
            wordlists = [words[i :: len(bot_pool)] for i in range(len(bot_pool))]

        elif "hiddenLetters" in packet:
            if current_letters is None:
                continue

            # Add hidden letters
            new_letters = list(current_letters)
            for letter in packet["hiddenLetters"]:
                try:
                    new_letters.remove("?")
                except ValueError:
                    continue
                else:
                    new_letters.append(letter)
            current_letters = "".join(new_letters)

            print(
                f"\nHidden letters: {packet['hiddenLetters']}, new letters: {current_letters}"
            )
            # Update wordlist
            words = unscramble(current_letters)
            wordlists = [words[i :: len(bot_pool)] for i in range(len(bot_pool))]
        elif "marks" in packet:
            if current_letters is None or not wordlists:
                continue
            # Mark reached
            print(f"\nMark {packet['marks'][0]-packet['marks'][1]} reached!")
            print(f"\nSending wordlists to bots: {wordlists}")

            # Notify bots to send their words
            for bot, words in zip(bot_pool, wordlists):
                for word in words:
                    bot.send_word(word)

        elif "ranking" in packet:
            # End of level reached
            print("\nLevel ended!")
            current_letters = None
            wordlists = []


def _main() -> None:

    game_code = input("\nInsert WoS Game Code >>").strip()

    url = f"https://play.wos.gg/{game_code}/system"

    print(
        f"\nMake sure to have a Twitch login on Chrome profile -> {CHROME_PROFILE_LISTENER}"
    )
    print(f"You also need a previous log in into this WoS game {url}")
    input("\nPress Enter to confirm and proceed...")

    # Create listener and bots
    ws = WSListener(
        url=url, chrome_profile=CHROME_PROFILE_LISTENER, headless=HEADLESS_LISTENER
    )
    bot_pool = [
        WosBot(url, firefox_profile=profile, headless=HEADLESS_BOTS)
        for profile in FIREFOX_BOT_PROFILES
    ]
    try:
        # Start websocket listener thread
        ws.start()

        # Start bot threads
        for bot in bot_pool:
            bot.start()

        # Run event loop
        _event_loop(bot_pool, ws)
    except KeyboardInterrupt:
        print("\nKeyboard Interrupted, closing listener and bots...")
        return
    finally:
        # Closes listener thread
        ws.close()

        # Closes bot threads
        for bot in bot_pool:
            bot.close()


if __name__ == "__main__":
    _main()
