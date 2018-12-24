# -*- coding: utf-8 -*-

BOT_NAME = 'scrapers'

SPIDER_MODULES = ['scrapers.spiders']
NEWSPIDER_MODULE = 'scrapers.spiders'


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 " \
             "Safari/537.36"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 3
# CONCURRENT_REQUESTS_PER_DOMAIN = 1
# CONCURRENT_REQUESTS_PER_IP = 16
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

# ITEM_PIPELINES = {
#    "scrapers.pipelines.MySQLPipeline": 300,
# }

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

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

HOST = "10.0.3.123"

# DB
DB_HOST = HOST
DB_PORT = 3306
DB_NAME = "job_posts"
DB_USER = "dummy"
DB_PASS = "dummy"

# Redis
REDIS_HOST = HOST
REDIS_PORT = 6379
