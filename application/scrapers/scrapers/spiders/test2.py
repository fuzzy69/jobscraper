# -*- coding: UTF-8 -*-
#!/usr/bin/env python

import sys
from time import sleep

try:  # main
    from application.scrapers.scrapers.basespider import BaseSpider
    from application.scrapers.scrapers.items import JobPostItem
except ImportError:  # scrapy crawl
    sys.path.append("..")  # allow imports from application directory
    from scrapers.basespider import BaseSpider
    from scrapers.items import JobPostItem


class TestSpider2(BaseSpider):
    """Dummy test spider"""
    name = "testspider2"
    start_urls = [
        # "http://httpbin.org/ip",
        # "https://httpbin.org/ip",
        "http://httpbin.org/headers",
        "https://httpbin.org/headers",
        "http://httpbin.org/user-agent",
        "https://httpbin.org/user-agent",
    ]

    # def start_requests(self):
    #     print(self.settings.get("SELECTED_COUNTRIES", []))
    #     print(self.settings.get("KEYWORDS", None))
    #     self.__class__.start_urls = ["http://httpbin.org/ip"]
    #     for url in self.__class__.start_urls:
    #         yield Request(url, self.parse)

    def parse(self, response):
        self.logger.info("Scraping article urls from \"{}\"".format(response.url))
        print(response.text)
        sleep(2)

        return {
            "URL": response.url,
            "status_code": response.status,
            "text": response.text,
        }

    # def close(self, reason):
    #     print("Done.")
