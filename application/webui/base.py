# -*- coding: UTF-8 -*-
#!/usr/bin/env python

import logging
from datetime import datetime, timedelta
from os.path import isfile

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from application.scrapers.scrapers.common import ScrapeType
from application.webui.misc import StaticFilesFilter
from application.webui.models import init_db
from config import (DEBUG, ROOT_DIR, TIMESTAMP_FORMAT, WEBUI_DB_FILE, WEBUI_DB_URI, WEBUI_SECRET_KEY, WEBUI_STATIC_DIR,
                    WEBUI_TEMPLATES_DIR, __title__, __version__)

version = '.'.join(map(str, __version__))

# Filter static files info from Flask log
flask_log = logging.getLogger("werkzeug")
flask_log.addFilter(StaticFilesFilter())

# App
app = Flask(
    __name__,
    static_folder=WEBUI_STATIC_DIR,
    template_folder=WEBUI_TEMPLATES_DIR,
)
app.secret_key = WEBUI_SECRET_KEY
app.config["SCRIPT_ROOT"] = ROOT_DIR
app.config["SQLALCHEMY_DATABASE_URI"] = WEBUI_DB_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DATABASE_CONNECT_OPTIONS"] = {}

db = SQLAlchemy(app)

# WebUI DB
if not isfile(WEBUI_DB_FILE):
    print("Rebuilding database ...")
    init_db(WEBUI_DB_URI)  # TODO
    print("Done.")

# # Settings
# settings = Settings(**SETTINGS)
# settings.load(SETTINGS_FILE)

# Scheduler
scheduler = None


@app.context_processor
def utility_processor():
    """Template helper functions"""
    def time_delta(end_time, start_time):
        """
        Calculates and shows time difference in a readable form
        :param end_time:
        :param start_time:
        :return:
        """
        if not end_time or not start_time:
            return ''
        if type(end_time) == str:
            end_time = datetime.strptime(end_time, TIMESTAMP_FORMAT)
        if type(start_time) == str:
            start_time = datetime.strptime(start_time, TIMESTAMP_FORMAT)
        total_seconds = (end_time - start_time).total_seconds()
        total_seconds = int(total_seconds)

        return readable_time(total_seconds)

    def readable_time(total_seconds):
        """Returns elapsed time in human readable format"""
        if not total_seconds:
            return '-'
        if total_seconds < 60:
            return '%s s' % total_seconds
        if total_seconds < 3600:
            return '%s m' % int(total_seconds / 60)

        return '%s h %s m' % (int(total_seconds / 3600), int((total_seconds % 3600) / 60))

    def str_date(date):
        """Returns date string without milliseconds"""
        return str(date).split('.')[0]

    def add_time(date, minutes):
        """Returns result date with added minutes"""
        return date + timedelta(minutes=minutes)

    def next_date_event(date, minutes):
        """"""
        while True:
            date = date + timedelta(minutes=minutes)
            if date > datetime.now():
                return date

    return dict(
        time_delta=time_delta,
        readable_time=readable_time,
        str_date=str_date,
        add_time=add_time,
        next_date_event=next_date_event,
    )


@app.context_processor
def ctx():
    """Variables/constants accessible from all templates"""
    return {
        "title": __title__,
        "version": version,
        "debug": DEBUG,
        "ScrapeType": ScrapeType,
    }


# @app.before_first_request
# def _initialize():
#     """"""
#     # Periodic Job init/update
#     periodic_jobs = db.session.query(PeriodicJobs).all()
#     current = dict()
#     new = set()
#     for job in periodic_jobs:
#         current[job.spider_name] = job
#     for spider in SPIDERS:
#         new.add(spider[0])
#     if not (set(current.keys()) == new):
#         print("Updating periodic jobs table ...")
#         # Delete all rows
#         db.session.query(PeriodicJobs).delete()
#         db.session.commit()
#         # Insert
#         for spider in SPIDERS:
#             if spider[0] in current:
#                 pj = current[spider[0]]
#                 job = PeriodicJobs(
#                     spider_name=pj.spider_name,
#                     scrape_type=pj.scrape_type,
#                     use_proxies=pj.use_proxies,
#                     file=pj.file,
#                     db=pj.db,
#                     # images=pj.images,
#                     repeat_time=pj.repeat_time,
#                     enabled=pj.enabled,
#                 )
#             else:
#                 job = PeriodicJobs(
#                     spider_name=spider[0],
#                 )
#             db.session.add(job)
#         db.session.commit()
#     # Disable active jobs
#     jobs = db.session.query(Jobs).filter(Jobs.spider_status < 2).all()
#     for job in jobs:
#         job.spider_status = 3
#     db.session.commit()
#     # # Add periodic jobs to scheduler
#     # periodic_jobs = db.session.query(PeriodicJobs).all()
#     # for job in periodic_jobs:
#     #     if JobStatus(job.enabled) == JobStatus.ENABLED:
#     #         print(job)
#     #
#     # exit()
#
#     # Init scheduler
#     # global scheduler
#     # scheduler = BackgroundScheduler()
#     # scheduler.start()
#     # atexit.register(lambda: scheduler.shutdown())


@app.teardown_request
def teardown_request(exception):
    """"""
    if exception:
        db.session.rollback()
        db.session.remove()
    db.session.remove()


from application.webui import admin
from application.webui import xhr
