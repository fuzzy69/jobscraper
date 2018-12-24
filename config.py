# -*- coding: UTF-8 -*-

from os.path import abspath, dirname, join
from time import strftime

__title__ = "Job Posts Scraper"
__short_title__ = "JPS"
__description__ = "Scrapy based scraper for job posts extraction"
__version__ = (0, 1, 15, 181212)

DEBUG = False
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMESTAMP_FORMAT2 = "%Y-%m-%d %H-%M-%S"

# Dirs
ROOT_DIR = abspath(dirname(__file__))
DATA_DIR = join(ROOT_DIR, "data")
LOG_DIR = join(ROOT_DIR, "logs")
RESULTS_DIR = join(ROOT_DIR, "results")
FEEDS_DIR = join(RESULTS_DIR, "feeds")

# Files
KEYWORDS_FILE = join(ROOT_DIR, "data", "keywords.txt")
PROXIES_FILE = join(ROOT_DIR, "data", "proxies.txt")
USER_AGENTS_FILE = join(ROOT_DIR, "data", "user_agents.txt")

# DB
DB_HOST = "10.0.3.100"
DB_PORT = 3306
DB_NAME = "job_posts"
DB_USER = "dummy"
DB_PASS = "dummy"

# Redis
REDIS_HOST = "10.0.3.100"
REDIS_PORT = 6379

# Celery
CELERY_LOGGING = True
BROKER_HOST = "10.0.3.100"
BROKER_PORT = 5672
BROKER_USER = "dummy"
BROKER_PASS = "dummy"

# Scrapy
DELAY = 3  # seconds
TIMEOUT = 30  # seconds
RETRIES = 2
CONCURRENT_REQUESTS = 1
SPIDERS = (
    ("indeed", "https://www.indeed.com/"),
    ("testspider", "https://httpbin.org/"),
    ("testspider2", "https://httpbin.org/"),
)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
             "Chrome/63.0.3239.132 Safari/537.36"
ROTATING_PROXY_LIST_PATH = PROXIES_FILE
ROTATING_PROXY_BACKOFF_BASE = 30
ROTATING_PROXY_BACKOFF_CAP = 60
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,  # Disable telnet console to avoid port errors
}
SAVE_TO_FEED = False
SAVE_TO_DB = False
USE_PROXIES = False
SCRAPE_TYPE = 0
SPIDER_LOG_DIR = join(LOG_DIR, "spiders")

# WebUI
WEBUI_HOST = "127.0.0.1"  # Dev
# WEBUI_HOST = "0.0.0.0"  # Production
WEBUI_PORT = 4000
WEBUI_SECRET_KEY = "_9\Z{$YkntY[v~*`n%SB{kL~m=vB^pjy"  # NOTE: it's desirable to change this key
WEBUI_STATIC_DIR = join(ROOT_DIR, "application", "webui", "static")
WEBUI_TEMPLATES_DIR = join(ROOT_DIR, "application", "webui", "templates")
WEBUI_DB_FILE = join(ROOT_DIR, "data", "webui.db")
WEBUI_DB_URI = "sqlite:///" + WEBUI_DB_FILE
WEBUI_LOGGING = True
WEBUI_LOG_FILE = join(LOG_DIR, "webui", "webui {}.log".format(strftime(TIMESTAMP_FORMAT2)))
# WEBUI_LOG_FORMAT = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"
WEBUI_LOG_FORMAT = "[%(asctime)s] <%(filename)s:%(funcName)s:%(lineno)d> %(levelname)s - %(message)s", \
                   "%Y-%m-%d %H:%M:%S",

SETTINGS_FILE = join(ROOT_DIR, "data", "settings.pickle")
REFRESH = 1  # Refresh page after delay
IPP = 50  # Pagination items per page

SETTINGS = {
    "refresh": REFRESH,
    "ipp": IPP,
    "delay": DELAY,
    "retries": RETRIES,
    "timeout": TIMEOUT,
    "save_to_feed": SAVE_TO_FEED,
    "save_to_db": SAVE_TO_DB,
    "use_proxies": USE_PROXIES,
    "scrape_type": SCRAPE_TYPE,
    "concurrent_requests": CONCURRENT_REQUESTS,
    "db_host": DB_HOST,
    "db_port": DB_PORT,
    "db_name": DB_NAME,
    "db_user": DB_USER,
    "db_pass": DB_PASS,
    "broker_host": BROKER_HOST,
    "broker_port": BROKER_PORT,
    "broker_user": BROKER_USER,
    "broker_pass": BROKER_PASS,
    "redis_host": REDIS_HOST,
    "redis_port": REDIS_PORT,
    "keywords": [],
    "selected_countries": [],
    "selected_spiders": [],
}

COUNTRIES = {
    "sa": ("Saudi Arabia", "https://sa.indeed.com/"),
    "us": ("United States", "https://www.indeed.com/"),
    "uk": ("United Kingdom", "https://www.indeed.co.uk/"),
    "none": ('-' * 100, ''),
    "ar": ("Argentina", "https://ar.indeed.com/"),
    "au": ("Australia", "https://au.indeed.com/"),
    "at": ("Austria", "https://at.indeed.com/"),
    "bh": ("Bahrain", "https://bh.indeed.com/"),
    "be": ("Belgium", "https://be.indeed.com/"),
    "br": ("Brazil", "https://www.indeed.com.br/"),
    "ca": ("Canada", "https://ca.indeed.com/"),
    "cl": ("Chile", "https://www.indeed.cl/"),
    "cn": ("China", "https://cn.indeed.com/"),
    "co": ("Colombia", "https://co.indeed.com/"),
    "cr": ("Costa Rica", "https://cr.indeed.com/"),
    "cz": ("Czech Republic", "https://cz.indeed.com/"),
    "dk": ("Denmark", "https://dk.indeed.com/"),
    "ec": ("Ecuador", "https://ec.indeed.com/"),
    "eg": ("Egypt", "https://eg.indeed.com/"),
    "fi": ("Finland", "https://www.indeed.fi/"),
    "fr": ("France", "https://www.indeed.fr/"),
    "de": ("Germany", "https://de.indeed.com/"),
    "gr": ("Greece", "https://gr.indeed.com/"),
    "hk": ("Hong Kong", "https://www.indeed.hk/"),
    "hu": ("Hungary", "https://hu.indeed.com/"),
    "in": ("India", "https://www.indeed.co.in/"),
    "id": ("Indonesia", "https://id.indeed.com/"),
    "ie": ("Ireland", "https://ie.indeed.com/"),
    "il": ("Israel", "https://il.indeed.com/"),
    "it": ("Italy", "https://it.indeed.com/"),
    "jp": ("Japan", "https://jp.indeed.com/"),
    "kw": ("Kuwait", "https://kw.indeed.com/"),
    "lu": ("Luxembourg", "https://www.indeed.lu/"),
    "my": ("Malaysia", "https://www.indeed.com.my/"),
    "mx": ("Mexico", "https://www.indeed.com.mx/"),
    "ma": ("Morocco", "https://ma.indeed.com/"),
    "nl": ("Netherlands", "https://www.indeed.nl/"),
    "nz": ("New Zealand", "https://nz.indeed.com/"),
    "ng": ("Nigeria", "https://ng.indeed.com/"),
    "no": ("Norway", "https://no.indeed.com/"),
    "om": ("Oman", "https://om.indeed.com/"),
    "pk": ("Pakistan", "https://www.indeed.com.pk/"),
    "pa": ("Panama", "https://pa.indeed.com/"),
    "pe": ("Peru", "https://www.indeed.com.pe/"),
    "ph": ("Philippines", "https://www.indeed.com.ph/"),
    "pl": ("Poland", "https://pl.indeed.com/"),
    "pt": ("Portugal", "https://www.indeed.pt/"),
    "qa": ("Qatar", "https://qa.indeed.com/"),
    "ro": ("Romania", "https://ro.indeed.com/"),
    "ru": ("Russia", "https://ru.indeed.com/"),
    "sg": ("Singapore", "https://www.indeed.com.sg/"),
    "za": ("South Africa", "https://www.indeed.co.za/"),
    "kr": ("South Korea", "https://kr.indeed.com/"),
    "es": ("Spain", "https://www.indeed.es/"),
    "se": ("Sweden", "https://se.indeed.com/"),
    "ch": ("Switzerland", "https://www.indeed.ch/"),
    "tw": ("Taiwan", "https://tw.indeed.com/"),
    "th": ("Thailand", "https://th.indeed.com/"),
    "tr": ("Turkey", "https://tr.indeed.com/"),
    "ua": ("Ukraine", "https://ua.indeed.com/"),
    "ae": ("United Arab Emirates", "https://www.indeed.ae/"),
    "uy": ("Uruguay", "https://uy.indeed.com/"),
    "ve": ("Venezuela", "https://ve.indeed.com/"),
    "vn": ("Vietnam", "https://vn.indeed.com/"),
}
