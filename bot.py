"""Words on Stream bot"""

from os import environ
from time import sleep
from queue import Empty
from dataclasses import dataclass
from multiprocessing import Process, Queue, Event
from screeninfo import get_monitors
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

WOS_INPUT_TEXT_CSSS = 'input[id="inputText"]'
ROOM_WORD_CSSS = 'div[class^="Room_word"]'
ICON_LOCK_BUTTON_CSSS = 'i[class^="Button_ico_lock"]'


@dataclass(frozen=True)
class SendWordEvent:
    """Event for when sending a word"""

    word: str


class WosBot:
    """Words on Stream bot class"""

    def __init__(
        self,
        game_url: str,
        firefox_profile: str = None,
        headless: bool = True,
    ) -> None:
        self._game_url = game_url
        self._driver = None

        # Set Chrome options
        self._opts = self._get_firefox_options(
            firefox_profile=firefox_profile, headless=headless
        )

        # Queue holding bot events
        self._events: Queue = Queue()

        self._running = Event()
        self._process: Process = None
        self._cached_words = set()

    def _get_firefox_options(
        self,
        firefox_profile: str = None,
        headless: bool = False,
        private_mode: bool = False,
    ) -> Options:
        """Returns chrome options instance with given configuration set"""
        options = Options()

        if firefox_profile and isinstance(firefox_profile, str):
            options.profile = firefox_profile

        if headless:
            monitor = get_monitors()[0]

            # Headless window size patch
            environ["MOZ_HEADLESS_WIDTH"] = str(monitor.width)
            environ["MOZ_HEADLESS_HEIGHT"] = str(monitor.height)
            options.add_argument("--headless")
            options.add_argument(f"--window-size={monitor.width},{monitor.height}")
            options.add_argument("--start-maximized")

            # Disables volume
            options.set_preference("media.volume_scale", "0.0")

            # Disable browser cache
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("browser.cache.offline.enable", False)
            options.set_preference("network.http.use-cache", False)

            # Disables WebRTC
            options.set_preference("media.peerconnection.enabled", False)

            # Disables homepage
            options.set_preference("browser.startup.homepage_welcome_url", "")
            options.set_preference("startup.homepage_welcome_url.additional", "")

            # Disable Firefox's new tab page suggestions and highlights
            options.set_preference("browser.newtabpage.enabled", False)
            options.set_preference("browser.sessionstore.resume_from_crash", False)

        if private_mode:
            options.set_preference("browser.privatebrowsing.autostart", True)

        return options

    def _type_word(self, word: str) -> bool:

        try:
            inp_text = self._driver.find_element(By.CSS_SELECTOR, WOS_INPUT_TEXT_CSSS)
            inp_text.click()
            sleep(0.1)
            inp_text.clear()
            inp_text.send_keys(word)
            ActionChains(self._driver).key_down(Keys.ENTER).key_up(Keys.ENTER).perform()
        except Exception:
            # Was unable to type word, signal to stop sending words
            return False

        try:
            self._driver.find_element(By.CSS_SELECTOR, ICON_LOCK_BUTTON_CSSS)
            # Lock icon found, possible word match, signal to stop sending words
            return False
        except Exception:
            return True

    def _update_word_cache(self) -> None:

        self._cached_words.clear()
        try:
            # Read already typed words from the page
            words = self._driver.find_elements(By.CSS_SELECTOR, ROOM_WORD_CSSS)
        except Exception:
            # No words found
            return

        for word in words:
            self._cached_words.add(word.text.replace("\n", "").lower())

    def _event_loop(self) -> None:

        while self._running.is_set():
            sleep(0.01)

            try:
                event = self._events.get_nowait()
            except Empty:
                continue

            if isinstance(event, SendWordEvent):

                # Read words sent from page
                self._update_word_cache()

                # Skip already typed words
                if event.word in self._cached_words:
                    continue

                # Type word
                if not self._type_word(event.word):
                    # Probably a hit, stop sending further messages
                    while not self._events.empty():
                        try:
                            self._events.get_nowait()
                        except Empty:
                            break

    def _process_task(self) -> None:

        self._driver = webdriver.Firefox(options=self._opts)

        try:
            self._driver.get(self._game_url)
            self._event_loop()
        finally:
            self._driver.quit()
            self._running.clear()

    def close(self) -> None:
        """Wait for bot thread to close"""
        self._running.clear()
        self._process.join()

    def start(self) -> None:
        """Starts the bot in a daemon thread"""

        if self._running.is_set():
            raise RuntimeError("This bot already started!")

        self._running.set()

        self._process = Process(target=self._process_task, daemon=True)
        self._process.start()

    def send_word(self, word: str) -> None:
        """Signal the bot to send a word"""
        self._events.put(SendWordEvent(word))
