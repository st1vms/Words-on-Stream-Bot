# Words on Stream Bots

Words on Stream bot pool based off Selenium, using both chromedriver and geckodriver.

## Requirements

- Windows

- Python >= 3.10

- Latest Chrome and Firefox installed

- Latest stable [chromedriver.exe](https://googlechromelabs.github.io/chrome-for-testing/) and [geckodriver](https://github.com/mozilla/geckodriver/releases) inside a PATH folder

- Python requirements for this project installed:

```shell
pip install -r requirements.txt
```

### Browser Preparation

You will need one Chrome profile logged to Twitch and with a recent login to a WoS game,
you can login to a WoS game using their play link `https://play.wos.gg/{GAME_CODE}`

For each bot you would like to spawn, you would need a dedicated Firefox profile, with a Twitch login and also a recent WoS game login.

## Usage

Clone this repository, and edit the file [main.py](main.py) using your configuration:

```py
# Each of these profiles must have a Twitch login,
# and a recent Words of Stream login.

# Chrome profile to use for Websocket listener
CHROME_PROFILE_LISTENER = "Default"

# Firefox profiles root folder paths to use for bots
# Leave empty to only spawn listener
FIREFOX_BOT_PROFILES = [
    # Example profile path
    r'C:\Users\user\AppData\Roaming\Mozilla\Firefox\Profiles\quwr39tp.profile'
]

# Turn off headless in order to debug listener profile
HEADLESS_LISTENER = False

# Turn off headless in order to debug bot profiles
HEADLESS_BOTS = False
```

Turn off headless mode in order to verify that all the profiles can connect to the game page correctly, turn it on if you want the bot to hide browser windows.

Run the bots by running:

```shell
python main.py
```

They will begin answering words once a new level starts.
