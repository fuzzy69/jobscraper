# -*- coding: UTF-8 -*-
#!/usr/bin/env python

import atexit
from copy import deepcopy
from datetime import datetime
from os import remove
from os.path import isfile, join
from pprint import pprint

from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import flash, jsonify, redirect, render_template, request
from redis import ConnectionError, Redis
from requests import get
from requests.auth import HTTPBasicAuth
from sqlalchemy_utils import create_database, database_exists

from application.misc import feed_file_path, log_file_path, text_file_to_lines
from application.scrapers.scrapers.common import JobStatus, OK, ScrapeType, SpiderStatus
from application.scrapers.scrapers.models import create_tables, table_exists
from application.webui.base import app, db, scheduler
from application.webui.misc import Settings, list_files, remove_files, text_to_unique_lines
from application.webui.models import Jobs, PeriodicJobs, SettingsStatus
from config import (COUNTRIES, FEEDS_DIR, LOG_DIR, PROXIES_FILE, SETTINGS, SETTINGS_FILE, SPIDERS, USER_AGENTS_FILE,
                    WEBUI_LOG_FILE)
from tasks import run_job, run_periodic_job

# Settings
settings = Settings(**SETTINGS)
settings.load(SETTINGS_FILE)

# Init scheduler
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


@app.before_first_request
def _initialize():
    """"""
    # Periodic Job init/update
    periodic_jobs = db.session.query(PeriodicJobs).all()
    current = dict()
    new = set()
    for job in periodic_jobs:
        current[job.spider_name] = job
    for spider in SPIDERS:
        new.add(spider[0])
    if not (set(current.keys()) == new):
        print("Updating periodic jobs table ...")
        # Delete all rows
        db.session.query(PeriodicJobs).delete()
        db.session.commit()
        # Insert
        for spider in SPIDERS:
            if spider[0] in current:
                pj = current[spider[0]]
                job = PeriodicJobs(
                    spider_name=pj.spider_name,
                    scrape_type=pj.scrape_type,
                    use_proxies=pj.use_proxies,
                    file=pj.file,
                    db=pj.db,
                    # images=pj.images,
                    repeat_time=pj.repeat_time,
                    enabled=pj.enabled,
                )
            else:
                job = PeriodicJobs(
                    spider_name=spider[0],
                )
            db.session.add(job)
        db.session.commit()

    # FIXME: Move periodic jobs init after restart to other place
    # Add periodic jobs to scheduler after restart
    periodic_jobs = db.session.query(PeriodicJobs).all()
    for job in periodic_jobs:
        if JobStatus(job.enabled) == JobStatus.ENABLED:
            print(job)
            try:
                params = {
                    "spider": job.id,
                    "spider_name": job.spider_name,
                    #
                    "delay": settings.key("delay"),
                    "timeout": settings.key("timeout"),
                    "retries": settings.key("retries"),
                    "concurrent_requests": settings.key("concurrent_requests"),
                    #
                    "scrape_type": job.scrape_type,
                    "save_to_feed": bool(job.file),
                    "save_to_db": bool(job.db),
                    "use_proxies": bool(job.use_proxies),
                    "keywords": settings.key("keywords"),
                    "selected_countries": settings.key("selected_countries"),
                }
                print(params)
                # continue
                scheduler.add_job(
                    func=run_periodic_job.delay,
                    trigger=IntervalTrigger(minutes=job.repeat_time),
                    id=job.spider_name,
                    args=(job.id, params),
                    name=job.spider_name,
                    replace_existing=True,
                )
                job.enabled = OK.YES
                db.session.commit()
                msg = "Successfully added periodic job ID {}".format(job.id)
                app.logger.info(msg)
                # flash(msg, "success")
            except ConflictingIdError:
                # job.enabled = OK.NO
                # db.session.commit()
                msg = "Job ID {} already exists".format(job.id)
                app.logger.error(msg, exc_info=True)
                # flash(msg, "danger")
            except Exception as e:
                # job.enabled = OK.NO
                # db.session.commit()
                msg = "Failed starting the job ID {}, details: {}".format(job.id, e)
                app.logger.error(msg, exc_info=True)
                # flash(msg, "danger")

    # Disable active jobs
    # jobs = db.session.query(Jobs).filter(Jobs.spider_status < 2).all()
    # for job in jobs:
    #     job.spider_status = 3
    # db.session.commit()
    # # Add periodic jobs to scheduler
    # periodic_jobs = db.session.query(PeriodicJobs).all()
    # for job in periodic_jobs:
    #     if JobStatus(job.enabled) == JobStatus.ENABLED:
    #         print(job)
    #
    # exit()

    # Init scheduler
    # global scheduler
    # scheduler = BackgroundScheduler()
    # scheduler.start()
    # atexit.register(lambda: scheduler.shutdown())


@app.route('/')
@app.route("/index")
def _index():
    """Root page, redirects to active jobs endpoint"""
    return redirect("/jobs/active")


@app.route("/jobs/active")
@app.route("/jobs/active/<int:job_id>")
def _jobs_active(job_id=None):
    """Shows and manages currently active/running jobs"""
    if job_id is not None:
        flash("Stopping the job id {}".format(job_id), "info")
        return redirect("/jobs/active")
    next_jobs = db.session.query(Jobs).filter(Jobs.spider_status == SpiderStatus.PENDING).all()
    running_jobs = db.session.query(Jobs).filter(Jobs.spider_status == SpiderStatus.RUNNING).all()
    
    return render_template(
        "jobs_active.html",
        next_jobs=next_jobs,
        running_jobs=running_jobs,
        now=datetime.now(),
        refresh=settings.key("refresh"),
    )


@app.route("/jobs/periodic")
def _jobs_periodic():
    """Shows and manages periodic jobs"""
    global settings
    disabled_jobs = db.session.query(PeriodicJobs).filter(PeriodicJobs.enabled == 0).all()
    enabled_jobs = db.session.query(PeriodicJobs).filter(PeriodicJobs.enabled == 1).all()
    
    return render_template(
        "jobs_periodic.html",
        disabled_jobs=disabled_jobs,
        enabled_jobs=enabled_jobs,
        settings=settings.to_object(),
        spiders=SPIDERS,
        countries=COUNTRIES,
    )


@app.route("/jobs/completed", defaults={"page": 1})
@app.route("/jobs/completed/<int:page>")
def _jobs_completed(page):
    """Shows completed jobs details"""
    pagination = db.session.query(Jobs).filter(Jobs.spider_status > 1).order_by(Jobs.id.desc()). \
        paginate(page, settings.key("ipp"))
    
    return render_template(
        "jobs_completed.html",
        pagination=pagination,
        ipp=settings.key("ipp"),
        now=datetime.now(),
    )


@app.route("/jobs/completed/delete", methods=["POST"])
def _jobs_completed_delete():
    """Deletes periodic jobs records from WebUI DB, associated log and feed files"""
    global settings
    all_jobs = request.form.get("_all_jobs", False)
    selected_jobs = request.form.get("_selected_jobs", '').strip().split(',')
    selected_jobs = list(filter(None, selected_jobs))
    # Delete selected
    deleted_jobs = []
    log_files = []
    feed_files = []
    if selected_jobs:
        for job_id in selected_jobs:
            try:
                job_id = int(job_id)
                # job = db.session.query(Jobs).filter(Jobs.id == job_id).first()
                job = db.session.query(Jobs).get(job_id)
                if job is None:
                    msg = "Can't find the job ID {} in WebUI DB".format(job_id)
                    app.logger.warning(msg)
                    continue
                # Delete job from WebUI DB
                db.session.delete(job)
                db.session.commit()
                deleted_jobs.append(job_id)
                log_files.append(log_file_path(job.spider_name, job.date_started))
                feed_files.append(feed_file_path(job.spider_name, job.date_started))
            except Exception as e:
                app.logger.error("Failed deleting job ID {}!".format(job_id), exc_info=True)
                flash("Failed deleting job ID {}! Details: {}".format(job_id, e), "error")
    # Delete all
    elif all_jobs:
        try:
            jobs = db.session.query(Jobs).all()
            # db.session.execute('''TRUNCATE TABLE jobs''')
            # db.session.commit()
            for job in jobs:
                db.session.delete(job)
                deleted_jobs.append(job.id)
                log_files.append(log_file_path(job.spider_name, job.date_started))
                feed_files.append(feed_file_path(job.spider_name, job.date_started))
            if not db.session.commit():
                log_files = []
                feed_files = []
        except Exception as e:
            app.logger.error("Failed truncating WebUI jobs table!", exc_info=True)
            flash("Failed truncating WebUI jobs table! Details: {}".format(e), "error")
    # Delete log files
    for log_file in log_files:
        if isfile(log_file):
            try:
                remove(log_file)
            except Exception as e:
                app.logger.error("Failed deleting log file {}!".format(log_file), exc_info=True)
        else:
            app.logger.warning("Can't locate the log file {}!".format(log_file))
    # Delete feed files
    for feed_file in feed_files:
        if isfile(feed_file):
            try:
                remove(feed_file)
            except Exception as e:
                app.logger.error("Failed deleting feed file {}!".format(feed_file), exc_info=True)
        else:
            app.logger.warning("Can't locate the feed file {}".format(feed_file))
    flash("Successfully deleted {} jobs".format(len(deleted_jobs)), "info")

    return redirect("/jobs/completed")


@app.route("/job/add", methods=["POST"])
def _job_add():
    """Adds a job to WebUI DB and runs it in a background task"""
    global settings
    try:
        # Selected spiders
        selected_spiders = request.form.get("_selected_spiders", '')
        selected_spiders = selected_spiders.split(',') if selected_spiders else []
        if all(selected_spiders):
            selected_spiders = list(map(int, selected_spiders))
        if selected_spiders:
            settings.set_key("selected_spiders", selected_spiders)
        else:
            msg = "Please select at least one spider!"
            app.logger.warning(msg)
            flash(msg, "warning")
        # Selected countries
        selected_countries = request.form.getlist("countries")
        if selected_countries:
            settings.set_key("selected_countries", selected_countries)
        else:
            msg = "Please select at least one country!"
            app.logger.warning(msg)
            flash(msg, "warning")
        # Keywords
        keywords = list(text_to_unique_lines(request.form.get("keywords", '')))
        if keywords:
            settings.set_key("keywords", keywords)
        else:
            msg = "Please enter at least one keyword!"
            app.logger.warning(msg)
            flash(msg, "warning")
        scrape_type = ScrapeType(int(request.form.get("scrape_type", '')))
        save_to_feed = bool(request.form.get("save_to_feed", ''))
        save_to_db = bool(request.form.get("save_to_db", ''))
        use_proxies = bool(request.form.get("use_proxies", ''))
        settings.set_key("scrape_type", scrape_type)
        settings.set_key("save_to_feed", save_to_feed)
        settings.set_key("save_to_db", save_to_db)
        settings.set_key("use_proxies", use_proxies)
        settings.save(SETTINGS_FILE)
        # print(selected_spiders, keywords, selected_countries)
        # return redirect(request.referrer)
        # Spider jobs
        if selected_spiders and keywords and selected_countries:
            params = {
                # Global
                "db_host": settings.key("db_host"),
                "db_port": settings.key("db_port"),
                "db_name": settings.key("db_name"),
                "db_user": settings.key("db_user"),
                "db_pass": settings.key("db_pass"),
                "redis_host": settings.key("redis_host"),
                "redis_port": settings.key("redis_port"),
                "delay": settings.key("delay"),
                "timeout": settings.key("timeout"),
                "retries": settings.key("retries"),
                "concurrent_requests": settings.key("concurrent_requests"),
                # "countries": settings.key("countries"),
                # Job specific
                "spider": None,
                "spider_name": None,
                "scrape_type": scrape_type.value,
                "save_to_feed": save_to_feed,
                "save_to_db": save_to_db,
                "use_proxies": use_proxies,
                "keywords": keywords,
                "selected_countries": selected_countries,
            }
            # pprint(params, indent=4)
            app.logger.debug("Job add params {}".format(params))
            # return redirect(request.referrer)
            # Set jobs
            jobs = []
            for spider_idx in selected_spiders:
                if spider_idx < len(SPIDERS):
                    spider_params = deepcopy(params)
                    spider_params["spider"] = spider_idx
                    spider_params["spider_name"] = SPIDERS[spider_idx][0]
                    job = Jobs(
                        task_id='',
                        spider_name=spider_params["spider_name"],
                        spider_status=SpiderStatus.PENDING,
                        scrape_type=spider_params["scrape_type"],
                        use_proxies=int(spider_params["use_proxies"]),
                        file=int(spider_params["save_to_feed"]),
                        db=int(spider_params["save_to_db"]),
                    )
                    jobs.append((job, spider_params))
            # Run spiders
            if jobs:
                # Save to WebUI DB
                for job, spider_params in jobs:
                    db.session.add(job)
                db.session.commit()
                msg = "Successfully added {} scrape job(s)".format(len(jobs))
                app.logger.info(msg)
                flash(msg, "success")
                # Run jobs
                for job, spider_params in jobs:
                    task_id = run_job.delay(job.id, spider_params)
                #             flash("Job id {} already exists".format(j.id), "danger")
                #         except Exception as e:
                #             flash("Failed starting the job id {}, details: {}".format(j.id, e))
                #     # flash("Successfully added {} periodic scrape job(s)".format(len(jobs)), "success")
    except Exception as e:
        msg = "Failed adding scrape job, details: {}".format(e)
        app.logger.error(msg, exc_info=True)
        flash(msg, "danger")
    
    return redirect(request.referrer)


@app.route("/periodic-jobs/add", methods=["POST"])
def _periodic_jobs_add():
    """Adds a periodic job to WebUI DB and job scheduler"""
    global settings
    try:
        # Selected spiders
        selected_spiders = request.form.get("_selected_spiders", '')
        selected_spiders = selected_spiders.split(',') if selected_spiders else []
        if all(selected_spiders):
            selected_spiders = list(map(int, selected_spiders))
        if selected_spiders:
            settings.set_key("selected_spiders", selected_spiders)
        else:
            msg = "Please select at least one spider!"
            app.logger.warning(msg)
            flash(msg, "warning")
        # Selected countries
        selected_countries = request.form.getlist("countries")
        if selected_countries:
            settings.set_key("selected_countries", selected_countries)
        else:
            msg = "Please select at least one country!"
            app.logger.warning(msg)
            flash(msg, "warning")
        # Keywords
        keywords = list(text_to_unique_lines(request.form.get("keywords", '')))
        if keywords:
            settings.set_key("keywords", keywords)
        else:
            msg = "Please enter at least one keyword!"
            app.logger.warning(msg)
            flash(msg, "warning")
        scrape_type = ScrapeType(int(request.form.get("scrape_type", '')))
        save_to_feed = bool(request.form.get("save_to_feed", ''))
        save_to_db = bool(request.form.get("save_to_db", ''))
        use_proxies = bool(request.form.get("use_proxies", ''))
        cron_minutes = int(request.form.get("cron_minutes"))
        cron_hour = int(request.form.get("cron_hour"))
        if cron_minutes == 0 and cron_hour == 0:
            flash("Please choose repeat time", "warning")
            return redirect("/jobs/periodic")
        repeat_time = cron_hour * 60 + cron_minutes
        settings.set_key("scrape_type", scrape_type)
        settings.set_key("save_to_feed", save_to_feed)
        settings.set_key("save_to_db", save_to_db)
        settings.set_key("use_proxies", use_proxies)
        # settings.set_key("repeat_time", repeat_time)
        settings.save(SETTINGS_FILE)
        # Periodic spider jobs
        if selected_spiders and keywords and selected_countries and repeat_time:
            params = {
                # Global
                "db_host": settings.key("db_host"),
                "db_port": settings.key("db_port"),
                "db_name": settings.key("db_name"),
                "db_user": settings.key("db_user"),
                "db_pass": settings.key("db_pass"),
                "redis_host": settings.key("redis_host"),
                "redis_port": settings.key("redis_port"),
                "delay": settings.key("delay"),
                "timeout": settings.key("timeout"),
                "retries": settings.key("retries"),
                "concurrent_requests": settings.key("concurrent_requests"),
                # Job specific
                "spider": None,
                "spider_name": None,
                "scrape_type": scrape_type.value,
                "save_to_feed": save_to_feed,
                "save_to_db": save_to_db,
                "use_proxies": use_proxies,
                "keywords": keywords,
                "selected_countries": selected_countries,
            }
            app.logger.debug(params)
            # pprint(params, indent=4)
            # Set periodic jobs
            for spider_id in selected_spiders:
                if spider_id - 1 < len(SPIDERS):
                    spider_name = SPIDERS[spider_id - 1][0]
                    try:
                        spider_params = deepcopy(params)
                        spider_params["spider"] = spider_id
                        spider_params["spider_name"] = spider_name
                        # Get periodic job by spider ID
                        job = db.session.query(PeriodicJobs).filter(PeriodicJobs.id == spider_id).first()
                        # Update periodic job settings
                        job.scrape_type = params["scrape_type"]
                        job.use_proxies = int(params["use_proxies"])
                        job.file = int(params["save_to_feed"])
                        job.db = int(params["save_to_db"])
                        job.repeat_time = repeat_time
                        job.enabled = OK.YES
                        job.date_started = datetime.now()
                        db.session.commit()
                        # Add periodic job to schedule
                        p = deepcopy(params)
                        p["spider"] = spider_id - 1
                        p["spider_name"] = spider_name
                        scheduler.add_job(
                            func=run_periodic_job.delay,
                            trigger=IntervalTrigger(minutes=repeat_time),
                            id=job.spider_name,
                            args=(job.id, p),
                            name=job.spider_name,
                            replace_existing=True,
                        )
                        flash("Successfully added periodic job {}".format(job.id), "success")
                    except ConflictingIdError:
                        job.enabled = OK.NO
                        db.session.commit()
                        msg = "Job ID {} already exists".format(job.id)
                        app.logger.error(msg, exc_info=True)
                        flash(msg, "danger")
                    except Exception as e:
                        job.enabled = OK.NO
                        db.session.commit()
                        app.logger.error("Failed starting the job ID {}!".format(job.id), exc_info=True)
                        flash("Failed starting the job ID {}, details: {}".format(job.id, e), "danger")
    except Exception as e:
        app.logger.error("Failed to add the scrape job!", exc_info=True)
        flash("Failed to add the scrape job, details: {}".format(e), "danger")
    
    return redirect(request.referrer)


@app.route("/periodic-jobs/<int:job_id>/start")
def _periodic_job_start(job_id):
    """Adds a saved periodic job from WebUI DB to job scheduler"""
    job = db.session.query(PeriodicJobs).filter(PeriodicJobs.id == job_id).first()
    if job is None:
        msg = "Can't find the job ID {} in WebUI DB".format(job_id)
        app.logger.warning(msg)
        flash(msg, "danger")
    else:
        try:
            # TODO: Refactor this
            spider_index = None
            for i, s in enumerate(SPIDERS):
                if job.spider_name == s[0]:
                    spider_index = i
            if spider_index is None:
                raise Exception("Can't find {} spider's ID".format(job.spider_name))
            params = {
                "spider": spider_index,
                "spider_name": job.spider_name,
                #
                "delay": settings.key("delay"),
                "timeout": settings.key("timeout"),
                "retries": settings.key("retries"),
                "concurrent_requests": settings.key("concurrent_requests"),
                #
                "scrape_type": job.scrape_type,
                "save_to_feed": bool(job.file),
                "save_to_db": bool(job.db),
                "use_proxies": bool(job.use_proxies),
                "keywords": settings.key("keywords"),
                "selected_countries": settings.key("selected_countries"),
            }
            # print(params)
            scheduler.add_job(
                func=run_periodic_job.delay,
                trigger=IntervalTrigger(minutes=job.repeat_time),
                id=job.spider_name,
                args=(job.id, params),
                name=job.spider_name,
                replace_existing=True,
            )
            job.enabled = OK.YES
            db.session.commit()
            msg = "Successfully added periodic job ID {}".format(job.id)
            app.logger.info(msg)
            flash(msg, "success")
        except ConflictingIdError:
            # job.enabled = OK.NO
            # db.session.commit()
            msg = "Job ID {} already exists".format(job.id)
            app.logger.error(msg, exc_info=True)
            flash(msg, "danger")
        except Exception as e:
            # job.enabled = OK.NO
            # db.session.commit()
            msg = "Failed starting the job ID {}, details: {}".format(job.id, e)
            app.logger.error(msg, exc_info=True)
            flash(msg, "danger")
    
    # return redirect("/jobs/periodic")
    return redirect(request.referrer)


@app.route("/jobs/<int:job_id>/stop")
def _job_stop(job_id):
    """Stops a active/running job"""
    job = db.session.query(Jobs).filter(Jobs.id == job_id).first()
    if job is None:
        flash("Can't find the job id {} in db".format(job_id), "danger")
    else:
        redis = Redis(settings.key("redis_host"), settings.key("redis_port"))
        r = redis.sadd("{}:stop".format(job.spider_name), job.task_id)
        app.logger.info("Stopping '{}' spider, job id {} ... Redis response '{}'".format(job.spider_name, job.task_id, r))
        job.spider_status = SpiderStatus.CANCELED.value
        db.session.commit()
    
    return redirect("/jobs/active/{}".format(job_id))


@app.route("/periodic-jobs/<int:job_id>/stop")
def _periodic_job_stop(job_id):
    """Disables saved periodic job in WebUI DB and removes it from job scheduler"""
    job = db.session.query(PeriodicJobs).filter(PeriodicJobs.id == job_id).first()
    if job is None:
        flash("Can't find the job ID {} in db".format(job_id), "danger")
    else:
        try:
            scheduler.remove_job(job.spider_name)
            job.enabled = OK.NO
            db.session.commit()
            flash("Successfully stopped periodic job {}".format(job_id), "success")
        except JobLookupError:
            msg = "Can't find the job ID {} in enabled jobs, moving it to disabled ones".format(job_id)
            flash(msg, "danger")
            app.logger.warning(msg)
        except Exception as e:
            flash("Failed stopping the job ID {}, details: {}".format(job_id, e), "danger")
            app.logger.warning("Failed stopping the job ID {}!".format(job_id), exc_info=True)
        finally:
            job.enabled = OK.NO
            db.session.commit()

    return redirect("/jobs/periodic")


@app.route("/project/settings", methods=["GET", "POST"])
def _project_settings():
    """Shows and manages WebUI and spider details"""
    global settings

    if request.method == "POST":
        try:
            db_uri, db_host, db_port, db_name, db_user, db_pass = None, None, None, None, None, None
            db_table = "job_posts"
            for key, value in request.form.items():
                settings.set_key(key, value, from_string=True)
                # DB
                if key == "db_host":
                    db_host = value
                elif key == "db_port":
                    db_port = value
                elif key == "db_name":
                    db_name = value
                elif key == "db_user":
                    db_user = value
                elif key == "db_pass":
                    db_pass = value
            settings.save(SETTINGS_FILE)
            flash("Successfully updated settings", "success")
            # Create DB and tables
            if all((db_host, db_port, db_name, db_user, db_pass)):
                db_uri = "mysql://{user}:{passw}@{host}:{port}/{db}".format(
                    host=db_host,
                    port=db_port,
                    db=db_name,
                    user=db_user,
                    passw=db_pass,
                )
                # Create DB
                if not database_exists(db_uri):
                    create_database(db_uri, encoding="utf8mb4")
                    flash("Successfully created database '{}'".format(db_name), "success")
                if database_exists(db_uri):
                    # Create DB tables
                    if not table_exists(db_uri, db_table):
                        create_tables(db_uri)
                        flash("Successfully created table '{}'".format(db_table), "success")
            else:
                flash("Please provide all DB connection details!", "warning")
        except Exception as e:
            app.logger.error("Failed updating settings!", exc_info=True)
            flash("Failed updating settings, details: {}".format(e), "danger")

        return redirect("/project/settings")
    
    return render_template(
        "project_settings.html",
        settings=settings.to_object(),
    )


@app.route("/project/maintenance", methods=["GET", "POST"])
def _project_maintenance():
    """Manages WebUI and spider maintenance tasks"""
    if request.method == "POST":
        try:
            results = []
            for key, value in request.form.items():
                # Remove log files
                if key == "webui_log_files":
                    log_files = list_files(join(LOG_DIR, "webui"))
                    if WEBUI_LOG_FILE in log_files:  # Keep current WebUI log file
                        log_files.remove(WEBUI_LOG_FILE)
                    removed_files = remove_files(log_files)
                    results.append("Removed total {} WebUI log file(s)".format(len(removed_files)))
                if key == "celery_log_files":
                    log_files = list_files(join(LOG_DIR, "celery"))
                    removed_files = remove_files(log_files)
                    results.append("Removed total {} Celery log file(s)".format(len(removed_files)))
                # Remove feed files
                if key == "feed_files":
                    feed_files = list_files(FEEDS_DIR)
                    removed_files = remove_files(feed_files)
                    results.append("Removed total {} spider feed file(s)".format(len(removed_files)))
                # # Clear Scrapy cache
                # if key == "clear_cache":
                #     pass
                # # Clear DB data
                # if key == "drop_db":
                #     pass
            flash("Successfully run maintenance tasks", "success")
            flash("<br />".join(results), "info")
        except Exception as e:
            flash("Failed running maintenance tasks, details: {}".format(e), "danger")
            app.logger.warning("Failed running maintenance tasks!", exc_info=True)
        return redirect("/project/maintenance")
    
    return render_template(
        "project_maintenance.html",
    )


@app.route("/project/spiders")
def _project_spiders():
    """Shows and runs selected spiders"""
    app.logger.debug(settings._to_dict())
    spiders = [(i, spider[0], spider[1]) for i, spider in enumerate(SPIDERS)]
    
    return render_template(
        "project_spiders.html",
        spiders=spiders,
        settings=settings.to_object(),
        countries=COUNTRIES,
    )


@app.route("/project/user-agents", methods=["GET", "POST"])
def _project_user_agents():
    """Shows and updates spider user agent list"""
    user_agents = ''
    if request.method == "POST":
        user_agents = request.form.get("user-agents", None)
        with open(USER_AGENTS_FILE, 'w') as f:
            f.write(user_agents.strip() + '\n')
            flash("Successfully updated user agents list", "success")
    else:
        if isfile(USER_AGENTS_FILE):
            with open(USER_AGENTS_FILE, 'r') as f:
                user_agents = f.read().strip()
    
    return render_template(
        "project_ua.html",
        user_agents=user_agents,
    )


@app.route("/project/proxies", methods=["GET", "POST"])
def _project_proxies():
    """Shows and updates spider proxy list"""
    proxies = ''
    if request.method == "POST":
        proxies = request.form.get("proxies", None)
        with open(PROXIES_FILE, 'w') as f:
            f.write(proxies.strip() + '\n')
            flash("Successfully updated proxies", "success")
    else:
        if isfile(PROXIES_FILE):
            with open(PROXIES_FILE, 'r') as f:
                proxies = f.read().strip()
    
    return render_template(
        "project_proxies.html",
        proxies=proxies,
    )


@app.route("/jobs/<int:job_id>/log")
def _job_log(job_id):
    """Shows a job's log file contents"""
    job = db.session.query(Jobs).filter(Jobs.id == job_id).first()
    refresh = False
    if job is None:
        flash("Can't find the job id {} in db".format(job_id), "danger")
    else:
        log_file = log_file_path(job.spider_name, job.date_started)
        log_lines = []
        if isfile(log_file):
            log_lines = text_file_to_lines(log_file)
            if SpiderStatus(job.spider_status) == SpiderStatus.RUNNING:
                refresh = True
        else:
            msg = "Can't locate the log file {}".format(log_file)
            flash(msg, "danger")
            app.logger.warning(msg)

    return render_template(
        "job_log.html",
        log_lines=log_lines,
        refresh=refresh,
    )


@app.route("/spiders/<int:job_id>/feed")
def _job_feed(job_id):
    """Shows a job's JSON feed"""
    job = db.session.query(Jobs).filter(Jobs.id == job_id).first()
    refresh = False
    if job is None:
        flash("Can't find the job id {} in db".format(job_id), "danger")
    else:
        feed_file = feed_file_path(job.spider_name, job.date_started)
        feed_lines = []
        if isfile(feed_file):
            feed_lines = text_file_to_lines(feed_file)
            if SpiderStatus(job.spider_status) == SpiderStatus.RUNNING:
                refresh = True
        else:
            msg = "Can't locate the JSON feed file {}".format(feed_file)
            flash(msg, "danger")
            app.logger.warning(msg)

    return render_template(
        "spider_feed.html",
        feed_lines=feed_lines,
        refresh=refresh,
    )


@app.route("/xhr/test-settings", methods=["POST"])
def _test_settings():
    """Starts test settings background job"""
    try:
        scheduler.add_job(
            func=test_settings,
            id="1",
            args=tuple(),
            name="test_settings",
            replace_existing=True,
        )
        status = True
        message = ''
    except Exception as e:
        status = False
        message = e
        app.logger.warning("Failed to start test settings background job!", exc_info=True)

    return jsonify({
        "status": status,
        "message": message,
    })


@app.route("/xhr/test-settings-results", methods=["POST"])
def _xhr_test_settings_results():
    """Returns test settings results"""
    row = db.session.query(SettingsStatus).first()
    # total = 4 - (row.db_status, row.celery_broker_status, row.celery_status, row.redis_status).count(0)
    total = 3 - (row.db_status, row.celery_broker_status, row.redis_status).count(0)
    progress = int(float(total) / 3 * 100)
    done = True if progress == 100 else False

    return jsonify({
        "db_status": row.db_status,
        "celery_broker_status": row.celery_broker_status,
        "celery_status": row.celery_status,
        "redis_status": row.redis_status,
        "progress": progress,
        "done": done,
    })


def test_settings():
    """Runs tests and stores the results in WebUI DB (0 = Unknown, 1 = Failed, 2 = Success)"""
    db_status, celery_broker_status, celery_status, redis_status = 0, 0, 0, 0
    if db.session.query(SettingsStatus).count() == 0:
        settings_status = SettingsStatus(
            db_status=db_status,
            celery_broker_status=celery_broker_status,
            celery_status=celery_status,
            redis_status=redis_status,
        )
        db.session.add(settings_status)
        db.session.commit()
    else:
        row = db.session.query(SettingsStatus).first()
        row.db_status = db_status
        row.celery_broker_status = celery_broker_status
        row.celery_status = celery_status
        row.redis_status = redis_status
        db.session.commit()
    # DB
    db_uri = "mysql://{user}:{passw}@{host}:{port}/{db}".format(
        host=settings.key("db_host"),
        port=settings.key("db_port"),
        db=settings.key("db_name"),
        user=settings.key("db_user"),
        passw=settings.key("db_pass"),
    )
    try:
        if database_exists(db_uri):
            db_status = 2
        else:
            db_status = 1
    except Exception as e:
        db_status = 1
        app.logger.warning("DB connection test failed!", exc_info=True)
    row = db.session.query(SettingsStatus).first()
    row.db_status = db_status
    db.session.commit()
    # RabbitMQ
    url = "http://{host}:15672/api/aliveness-test/%2F".format(
        host=settings.key("broker_host"),
    )
    try:
        r = get(url, auth=HTTPBasicAuth(settings.key("broker_user"), settings.key("broker_pass")), timeout=10)
        if r.status_code == 200 and r.json()["status"] == "ok":
            print('+' * 50)
            celery_broker_status = 2
        else:
            celery_broker_status = 1
    except Exception as e:
        celery_broker_status = 1
        app.logger.warning("Celery broker connection test failed!", exc_info=True)
    row = db.session.query(SettingsStatus).first()
    row.celery_broker_status = celery_broker_status
    db.session.commit()
    # Celery
    # try:
    #     print(foo.delay())
    #     celery_status = 2
    # except Exception as e:
    #     celery_status = 1
    #     app.log.warrning(e)
    # if is_celery_up():
    #     celery_broker_status, celery_status = 2, 2
    # else:
    #     celery_broker_status, celery_status = 1, 1
    # row = db.session.query(SettingsStatus).first()
    # row.celery_broker_status = celery_broker_status
    # row.celery_status = celery_status
    # db.session.commit()
    # Redis
    redis_host, redis_port = settings.key("redis_host"), settings.key("redis_port")
    r = Redis(redis_host, redis_port)
    try:
        r.ping()
        redis_status = 2
    except ConnectionError as e:
        redis_status = 1
        app.logger.warning("Redis connection test failed!", exc_info=True)
    row = db.session.query(SettingsStatus).first()
    row.redis_status = redis_status
    db.session.commit()


# TODO: Remove this
@app.route("/test")
def _test():
    """Do test"""
    return "OK"


if __name__ == "__main__":
    pass
