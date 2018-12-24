# -*- coding: UTF-8 -*-
# !/usr/bin/env python

import datetime
import logging
from os.path import isfile, join
from pprint import pprint
from random import choice

import celery
import celery.bin.base
import celery.bin.celery
import celery.platforms
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from twisted.internet import asyncioreactor

asyncioreactor.install()  # FIXME:
from billiard import Process
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings as ScrapySettings

from config import (
    __short_title__, __title__, WEBUI_DB_URI, FEEDS_DIR, EXTENSIONS, RESULTS_DIR, DEBUG,
    USER_AGENT, SETTINGS, SETTINGS_FILE, TIMESTAMP_FORMAT2, ROTATING_PROXY_LIST_PATH,
    ROTATING_PROXY_BACKOFF_BASE,
    ROTATING_PROXY_BACKOFF_CAP, USER_AGENTS_FILE, SPIDER_LOG_DIR,
)
from application.misc import text_file_to_lines
from application.spiders import SPIDERS
from application.scrapers.scrapers.common import SpiderStatus, ScrapeType
from application.webui.misc import Settings
from application.webui.models import Jobs


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Settings
settings = Settings(**SETTINGS)
if isfile(SETTINGS_FILE):  # Load existing settings
    settings.load(SETTINGS_FILE)
else:  # Create settings file if it doesn't exists
    settings.save(SETTINGS_FILE)

settings = Settings()
settings.load(SETTINGS_FILE)
BROKER_URI = "amqp://{user}:{pwd}@{host}:{port}".format(
    host=settings.key("broker_host"), port=settings.key("broker_port"),
    user=settings.key("broker_user"), pwd=settings.key("broker_pass"),
)

# WebUI SQLite DB
engine = create_engine(WEBUI_DB_URI)
DBSession = sessionmaker(bind=engine)
db_session = DBSession()
db_session.close()

# Celery
app = Celery(
    __short_title__,
    broker=BROKER_URI,
    # backend=BACKEND_URI,
)
status = celery.bin.celery.CeleryCommand.commands['status']()
status.app = status.get_app()


def run_crawler(params: dict):
    """
    Create and run scrapy spider
    :param dict params: scrapy spider parameters
    """
    spider = SPIDERS[params["spider"]]
    scrapy_settings = ScrapySettings()
    crawler = CrawlerProcess(scrapy_settings)
    # Global settings
    downloader_middlewares = {}
    item_pipelines = {}
    scrapy_settings["BOT_NAME"] = "{} [{}]".format(__title__, spider.name)
    scrapy_settings["ROBOTSTXT_OBEY"] = False
    scrapy_settings["COOKIES_ENABLED"] = False
    scrapy_settings["CONCURRENT_REQUESTS"] = params["concurrent_requests"]
    scrapy_settings["DOWNLOAD_DELAY"] = params["delay"]
    scrapy_settings["DOWNLOAD_TIMEOUT"] = params["timeout"]
    scrapy_settings["RETRY_TIMES"] = params["retries"]
    scrapy_settings["LOG_LEVEL"] = "INFO"
    # User agents
    user_agents = text_file_to_lines(USER_AGENTS_FILE)
    scrapy_settings["USER_AGENT"] = choice(user_agents) if user_agents else USER_AGENT
    # Proxies
    if params["use_proxies"] and user_agents:
        proxies = text_file_to_lines(ROTATING_PROXY_LIST_PATH)
        if proxies:
            scrapy_settings["USER_AGENTS"] = user_agents
            downloader_middlewares.update({
                "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
                "application.scrapers.scrapers.middlewares.RotatingUserAgentMiddleware": 300,
            })
            scrapy_settings["ROTATING_PROXY_BACKOFF_BASE"] = ROTATING_PROXY_BACKOFF_BASE
            scrapy_settings["ROTATING_PROXY_BACKOFF_CAP"] = ROTATING_PROXY_BACKOFF_CAP
            scrapy_settings["ROTATING_PROXY_LIST_PATH"] = ROTATING_PROXY_LIST_PATH
            downloader_middlewares.update({
                "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
                "rotating_proxies.middlewares.BanDetectionMiddleware": 620,
            })
    if params["save_to_db"]:
        scrapy_settings["DB_HOST"] = params["db_host"]
        scrapy_settings["DB_PORT"] = params["db_port"]
        scrapy_settings["DB_NAME"] = params["db_name"]
        scrapy_settings["DB_USER"] = params["db_user"]
        scrapy_settings["DB_PASS"] = params["db_pass"]
        scrapy_settings["DB_URI"] = "mysql+pymysql://{user}:{passw}@{host}/{db}?host={host}?port={port}".format(
            host=params["db_host"],
            port=params["db_port"],
            db=params["db_name"],
            user=params["db_user"],
            passw=params["db_pass"],
        )
        item_pipelines.update({
            "application.scrapers.scrapers.pipelines.MySQLPipeline": 400,
        })
    # Spider specific settings
    if params["save_to_feed"]:
        scrapy_settings["FEEDS_DIR"] = FEEDS_DIR
        scrapy_settings["FEED_URI"] = params["feed_file"]
        # ITEM_PIPELINES.update({
        #     "application.scrapers.scrapers.pipelines.CustomJSONPipeline": 600,
        # })
    if params["log"]:
        scrapy_settings["LOG_FILE"] = params["log"]
    scrapy_settings["DOWNLOADER_MIDDLEWARES"] = downloader_middlewares
    scrapy_settings["ITEM_PIPELINES"] = item_pipelines
    scrapy_settings["EXTENSIONS"] = EXTENSIONS
    scrapy_settings["SCRAPE_TYPE"] = params["scrape_type"]
    scrapy_settings["RESULTS_DIR"] = RESULTS_DIR
    scrapy_settings["JOB_ID"] = params["job_id"]
    scrapy_settings["TASK_ID"] = params["task_id"]
    scrapy_settings["WEBUI_DB_URI"] = WEBUI_DB_URI
    scrapy_settings["SCRAPE_TEST"] = DEBUG
    scrapy_settings["KEYWORDS"] = params["keywords"]
    scrapy_settings["SELECTED_COUNTRIES"] = params["selected_countries"]
    scrapy_settings["REDIS_HOST"] = params["redis_host"]
    scrapy_settings["REDIS_PORT"] = params["redis_port"]
    # print(params)

    crawler.crawl(spider)
    crawler.start()


def run_crawler_process(params: dict) -> Process:
    """
    Start scrapy spider from a separate process
    :param dict params: scrapy spider parameters
    :return: process instance
    """
    process = Process(target=run_crawler, args=(params, ), )
    process.start()

    return process


@app.task
def run_job(job_id: int, params: dict):
    """
    Run one scrape job
    :param int job_id: row ID of a job from the jobs table in webui.db
    :param dict params: scrapy spider parameters
    """
    # Update job
    job = db_session.query(Jobs).filter_by(id=job_id).first()
    if job is None:
        return False
    job.task_id = run_job.request.id
    time_stamp = datetime.datetime.now()
    job.date_started = time_stamp
    file_name = "{} {}".format(job.spider_name, time_stamp.strftime(TIMESTAMP_FORMAT2))
    log_file = file_name + ".log"
    feed_file = file_name + ".json"
    job.spider_status = SpiderStatus.RUNNING
    db_session.commit()
    params["log"] = join(SPIDER_LOG_DIR, log_file)
    params["feed_file"] = join(FEEDS_DIR, feed_file)
    params["scrape_type"] = ScrapeType(params["scrape_type"])
    params["job_id"] = job_id
    params["task_id"] = job.task_id
    # print(params)

    run_crawler_process(params)
    # process = run_crawler_process(params)


@app.task
def run_periodic_job(job_id: int, params: dict):
    """
    Run periodic scrape job managed by APScheduler
    :param int job_id: row ID of a job from the periodic_jobs table in webui.db
    :param dict params: scrapy spider parameters
    """
    time_stamp = datetime.datetime.now()
    file_name = "{} {}".format(params["spider_name"], time_stamp.strftime(TIMESTAMP_FORMAT2))
    log_file = file_name + ".log"
    feed_file = file_name + ".json"
    job = Jobs(
        task_id=run_periodic_job.request.id,
        spider_name=params["spider_name"],
        spider_status=SpiderStatus.RUNNING,
        scrape_type=params["scrape_type"],
        use_proxies=params["use_proxies"],
        file=params["save_to_feed"],
        db=params["save_to_db"],
        # images=params["images"],
        date_started=datetime.datetime.now(),
    )
    db_session.add(job)
    db_session.commit()
    params["log"] = join(SPIDER_LOG_DIR, log_file)
    params["save_to_feed"] = None
    params["feed_file"] = join(FEEDS_DIR, feed_file)
    params["scrape_type"] = ScrapeType(params["scrape_type"])
    params["job_id"] = job.id
    params["task_id"] = job.task_id
    # print(params)

    run_crawler_process(params)
    # process = run_crawler_process(params)


@app.task
def run_test_job(params):
    pprint(params, indent=4)
    process = run_crawler_process(params)
    print(process)


def is_celery_up():
    try:
        status.run()
        return True
    except celery.bin.base.Error as e:
        if e.status == celery.platforms.EX_UNAVAILABLE:
            return False
        # raise e
        return False


if __name__ == "__main__":
    logging.info("Starting Celery ...")
    logging.info(BROKER_URI)
    app.start()
