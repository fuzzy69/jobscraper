# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from datetime import datetime
from os.path import isfile, join

from flask import jsonify
from jinja2 import Template

from config import (
    WEBUI_TEMPLATES_DIR, DATA_DIR
)
from application.webui.base import app, db, utility_processor
from application.scrapers.scrapers.common import SpiderStatus, ScrapeType
from application.webui.models import Jobs, PeriodicJobs


# Load templates
next_jobs_template = None
template_file = join(WEBUI_TEMPLATES_DIR, "xhr", "table_next_jobs.html")
with open(template_file) as f:
    next_jobs_template = Template(f.read())
running_jobs_template = None
template_file = join(WEBUI_TEMPLATES_DIR, "xhr", "table_running_jobs.html")
with open(template_file) as f:
    running_jobs_template = Template(f.read())
enabled_jobs_template = None
template_file = join(WEBUI_TEMPLATES_DIR, "xhr", "table_enabled_jobs.html")
with open(template_file) as f:
    enabled_jobs_template = Template(f.read())


@app.route("/xhr/next-jobs-table")
def _xhr_next_jobs_table():
    """Returns a JSON with a list of next jobs data and a rendered next jobs table"""
    next_jobs = list()
    for job in db.session.query(Jobs).filter(Jobs.spider_status == SpiderStatus.PENDING).all():
        next_jobs.append({
            "id": job.id,
            "spider_name": job.spider_name,
            "scrape_type": ScrapeType(job.scrape_type),
            "use_proxies": bool(job.use_proxies),
            "save_to_file": bool(job.file),
            "save_to_db": bool(job.db),
        })
    html = next_jobs_template.render(
        next_jobs=next_jobs,
        scrape_type=ScrapeType,
    )
    
    return jsonify({
        "next_jobs": next_jobs,
        "html": html,
    })


@app.route("/xhr/running-jobs-table")
def _xhr_running_jobs_table():
    """Returns a JSON with a list of running jobs data and a rendered running jobs table"""
    running_jobs = list()
    for job in db.session.query(Jobs).filter(Jobs.spider_status == SpiderStatus.RUNNING).all():
        running_jobs.append({
            "id": job.id,
            "spider_name": job.spider_name,
            "scrape_type": ScrapeType(job.scrape_type),
            "use_proxies": bool(job.use_proxies),
            "date_started": job.date_started,
            "save_to_file": bool(job.file),
            "save_to_db": bool(job.db),
        })
    util_proc = utility_processor()
    html = running_jobs_template.render(
        running_jobs=running_jobs,
        now=datetime.now(),
        time_delta=util_proc["time_delta"],
        str_date=util_proc["str_date"],
        scrape_type=ScrapeType,
    )
    
    return jsonify({
        "running_jobs": running_jobs,
        "html": html,
    })


@app.route("/xhr/enabled-jobs-table")
def _xhr_enabled_jobs_table():
    """Returns a JSON with a list of enabled periodic jobs data and a rendered enabled jobs table"""
    enabled_jobs = list()
    for job in db.session.query(PeriodicJobs).filter(PeriodicJobs.enabled == 1).all():
        enabled_jobs.append({
            "id": job.id,
            "spider_name": job.spider_name,
            "scrape_type": ScrapeType(job.scrape_type),
            "use_proxies": bool(job.use_proxies),
            "date_started": job.date_started,
            "save_to_file": bool(job.file),
            "save_to_db": bool(job.db),
            "repeat_time": job.repeat_time,
        })
    util_proc = utility_processor()
    html = enabled_jobs_template.render(
        enabled_jobs=enabled_jobs,
        now=datetime.now(),
        str_date=util_proc["str_date"],
        next_date_event=util_proc["next_date_event"],
        scrape_type=ScrapeType,
    )
    
    return jsonify({
        "enabled_jobs": enabled_jobs,
        "html": html,
    })
