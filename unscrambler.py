"""Unscramber module, scraping from word.tips"""

import requests

BASE_URL = "https://fly.wordfinderapi.com/api/search"

BASE_PARAMS = {
    "letters": None,
    "word_sorting": "points",
    "group_by_length": True,
    "page_size": 200,
    "dictionary": "all_en",  # Words with Friends (wwf2)
}

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US;q=0.5,en;q=0.3",
    "Sec-GPC": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
}


def unscramble(letters: str) -> list | None:
    """Returns unscramble results dictionary,
    with word lengths as keys and word lists as values"""

    params = BASE_PARAMS.copy()
    params["letters"] = letters

    res = requests.get(BASE_URL, params=params, headers=BASE_HEADERS, timeout=5)
    if res.status_code != 200:
        return None

    j = res.json()
    if not "word_pages" in j:
        return None

    return [
        wl["word"]
        for wp in j["word_pages"]
        if int(wp["length"]) >= 4
        for wl in wp["word_list"]
    ]


if __name__ == "__main__":
    print(unscramble(input("\nInput letters\n>>").strip()))
