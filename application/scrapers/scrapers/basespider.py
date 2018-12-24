# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from datetime import datetime
import sys

from redis import Redis
from scrapy import Request, Spider, signals
from scrapy.exceptions import CloseSpider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:  # main
    from config import REDIS_PORT, REDIS_HOST
    from application.webui.models import Jobs
    from application.scrapers.scrapers.common import SpiderStatus
    SCRAPY_CRAWL = False
except ImportError:  # scrapy crawl
    sys.path.append("..")  # allow imports from application directory
    from scrapers.common import SpiderStatus
    from scrapers.settings import REDIS_HOST, REDIS_PORT
    SCRAPY_CRAWL = True


class BaseSpider(Spider):
    """Base spider class"""
    name = "basespider"
    start_urls = []
    base_url = None
    pagination_xpath = None
    article_xpath = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scrape_type = None
        self._job_id = None
        self._task_id = None
        self._redis = None
        self._webui_db = None
        self._db = None
        self._pagination_urls = set()
        self._job_urls = set()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """"""
        spider = super().from_crawler(crawler, *args, **kwargs)
        # Signals
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        # crawler.signals.connect(spider.request_scheduled, signals.request_scheduled)
        crawler.signals.connect(spider.response_received, signals.response_received)

        return spider

    def spider_opened(self, spider):
        """"""
        if not SCRAPY_CRAWL:
            # Redis
            redis_host = self.settings.get("REDIS_HOST", None)
            if redis_host is None:
                raise CloseSpider("Redis host isn't set!")
            redis_port = self.settings.get("REDIS_PORT", None)
            if redis_port is None:
                raise CloseSpider("Redis port isn't set!")
            self._redis = Redis(redis_host, redis_port)
            if not self._redis.ping():
                raise CloseSpider("Can't connect to Redis instance at {host}:{port}".format(
                    host=redis_host,
                    port=redis_port,
                ))
            # WebUI
            webui_db_uri = self.settings.get("WEBUI_DB_URI", None)
            if webui_db_uri is None:
                raise CloseSpider("Can't connect to WebUI DB!")
            engine = create_engine(webui_db_uri)
            db_session = sessionmaker(bind=engine)
            self._webui_db = db_session()
            # DB
            if self.settings.get("DB_URI", None) is not None:
                # db_uri = "mysql+pymysql://{user}:{passw}@{host}/{db}?host={host}?port={port}".format(
                #     host=self.settings.get("DB_HOST"),
                #     port=self.settings.get("DB_PORT"),
                #     db=self.settings.get("DB_NAME"),
                #     user=self.settings.get("DB_USER"),
                #     passw=self.settings.get("DB_PASS"),
                # )
                # engine = create_engine(db_uri)
                engine = create_engine(self.settings.get("DB_URI"))
                db_session = sessionmaker(bind=engine)
                self._db = db_session()
            # Job ID, Task ID
            self._scrape_type = self.settings.get("SCRAPE_TYPE")
            self._job_id = self.settings.get("JOB_ID", None)
            self._task_id = self.settings.get("TASK_ID", None)
            if self._job_id is None:
                raise CloseSpider("Job ID not set!")
            if self._task_id is None:
                raise CloseSpider("Task ID not set!")
            self.logger.info("Job ID [{}], Task ID [{}]".format(self._job_id, self._task_id))

    def spider_closed(self, spider):
        """"""
        if not SCRAPY_CRAWL:
            stats = spider.crawler.stats.get_stats()
            job = self._webui_db.query(Jobs).filter(Jobs.id == self._job_id).first()
            if job is None:
                self.logger.warning("Failed updating spider state for job id <{}>".format(self._job_id))
                return
            job.date_finished = datetime.now()
            if "item_scraped_count" in stats:
                job.items_scraped = stats["item_scraped_count"]
            if job.spider_status != SpiderStatus.CANCELED:
                job.spider_status = SpiderStatus.FINISHED
            self._webui_db.commit()
            self.logger.info("Updated spider state for job id {}".format(self._job_id))
            # DB
            if self._db is not None:
                self._db.close()

    def response_received(self, response, request, spider):
        if not SCRAPY_CRAWL:
            if self._redis.sismember("{}:stop".format(self.__class__.name), self._task_id):
                self.crawler.engine.close_spider(spider, "Requested spider task {} cancellation".format(self._task_id))

    def start_requests(self):
        for url in self.__class__.start_urls:
            yield Request(url, self.parse)
