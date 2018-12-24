# -*- coding: UTF-8 -*-

from application.scrapers.scrapers.spiders.indeed import IndeedSpider
from application.scrapers.scrapers.spiders.test import TestSpider
from application.scrapers.scrapers.spiders.test2 import TestSpider2


SPIDERS = (
    IndeedSpider,
    TestSpider,
    TestSpider2,
)
