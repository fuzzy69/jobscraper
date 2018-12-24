# -*- coding: utf-8 -*-

import logging
import sys
from urllib.parse import parse_qs, urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


try:  # main
    from application.scrapers.scrapers.models import JobPosts
except ImportError:  # scrapy crawl
    sys.path.append("..")  # allow imports from application directory
    from scrapers.models import JobPosts


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ScrapersPipeline:
    """Base Scrapy pipeline class"""

    def process_item(self, item, spider):
        return item


class MySQLPipeline(ScrapersPipeline):
    """Scrapy pipeline for MySQL"""

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def __init__(self, crawler):
        self._stats = crawler.stats
        self._settings = crawler.settings
        # db_uri = "mysql+pymysql://{user}:{passw}@{host}/{db}?host={host}?port={port}".format(
        #     host=self._settings.get("DB_HOST"),
        #     port=self._settings.get("DB_PORT"),
        #     db=self._settings.get("DB_NAME"),
        #     user=self._settings.get("DB_USER"),
        #     passw=self._settings.get("DB_PASS"),
        # )
        # self._engine = create_engine(db_uri)
        self._engine = create_engine(self._settings["DB_URI"])
        self._db_session = None

    def open_spider(self, spider):
        DBSession = sessionmaker(bind=self._engine)
        self._db_session = DBSession()
        # self._db_session = self._engine.connect()

    def close_spider(self, spider):
        self._db_session.close()

    def process_item(self, item, spider):
        try:
            job_post = JobPosts(
                job_post_id=MySQLPipeline._get_job_post_id(item["URL"]),
                url=item["URL"],
                title=item["Title"],
                location=item["Location"],
                description=item["Description"],
                date_added=item["Date_Added"],
                date_job_posted=item["Date_Job_Posted"],
            )
            self._db_session.add(job_post)
            self._db_session.commit()
            # self._db_session.flush()
            logger.info("Successfully added job post '{}' to DB".format(item["Title"]))
        except Exception as e:  # TODO: Add specific exceptions
            logger.error("Failed inserting job post to DB, details: {}".format(e))
            self._db_session.rollback()
            
        return item

    @staticmethod
    def _get_job_post_id(url: str) -> str:
        try:
            job_post_id = parse_qs(urlparse(url).query)["jk"][0]
        except Exception as e:  # TODO: Add specific exceptions
            job_post_id = None

        return job_post_id
