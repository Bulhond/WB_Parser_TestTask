import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "wb_parser"

SPIDER_MODULES = ["wb_parser.spiders"]
NEWSPIDER_MODULE = "wb_parser.spiders"

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 0.25
RANDOMIZE_DOWNLOAD_DELAY = True

COOKIES_ENABLED = True

LOG_LEVEL = "INFO"
LOG_FILE = f"./logs/{datetime.now().strftime('%Y.%m.%d')}.log"
TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Safari/537.36 OPR/128.0.0.0"
    ),
}

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504]

DOWNLOADER_MIDDLEWARES = {
    "wb_parser.middlewares.RateLimitMiddleware": 550,
}

SEARCH_QUERY = "пальто из натуральной шерсти"
DEST = "-1205339"

BASKETS_URL = "https://cdn.wbbasket.ru/api/v3/upstreams"
SEARCH_URL_TEMPLATE = (
    "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search"
    "?ab_testing=false&appType=1&curr=rub&dest={dest}"
    "&hide_vflags=4294967296&inheritFilters=false&lang=ru"
    "&query={query}&resultset=catalog&sort=popular"
    "&spp=30&suppressSpellcheck=false&page={page}&limit=100"
)
CARD_URL_TEMPLATE = "{basket}/vol{vol}/part{part}/{nm}/info/ru/card.json"
IMAGE_URL_TEMPLATE = "{basket}/vol{vol}/part{part}/{nm}/images/big/{index}.webp"

X_WBAAS_TOKEN = os.getenv("X_WBAAS_TOKEN", "")

FEEDS = {
    f"./data/products_{datetime.now().strftime('%Y.%m.%d_%H-%M-%S')}.json": {
        "format": "json",
        "encoding": "utf-8",
        "store_empty": False,
        "overwrite": True,
    }
}
