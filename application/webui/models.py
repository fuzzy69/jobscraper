# -*- coding: UTF-8 -*-

from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime, Integer, String
from sqlalchemy.dialects.mysql import INTEGER

from application.scrapers.scrapers.common import ScrapeType, SpiderStatus, OK


Base = declarative_base()


class BaseTable(Base):
    """Abstract base table clas"""
    __abstract__ = True

    id = Column(Integer, primary_key=True)


class Jobs(BaseTable):
    """Jobs table model"""
    __tablename__ = "jobs"

    task_id = Column(String(100))
    spider_name = Column(String(100), nullable=False, index=True)
    spider_status = Column(INTEGER, nullable=False, default=SpiderStatus.PENDING)
    scrape_type = Column(INTEGER, nullable=False, default=ScrapeType.ALL)
    use_proxies = Column(INTEGER, nullable=False, default=OK.NO)
    file = Column(INTEGER, nullable=False, default=OK.NO)
    db = Column(INTEGER, nullable=False, default=OK.NO)
    items_scraped = Column(INTEGER, default=0)
    date_started = Column(DateTime)
    date_finished = Column(DateTime)


class PeriodicJobs(BaseTable):
    """Periodic jobs table model"""
    __tablename__ = "periodic_jobs"

    spider_name = Column(String(100), nullable=False, index=True, unique=True)
    scrape_type = Column(INTEGER, nullable=False, default=ScrapeType.ALL)
    use_proxies = Column(INTEGER, nullable=False, default=OK.NO)
    file = Column(INTEGER, nullable=False, default=OK.NO)
    db = Column(INTEGER, nullable=False, default=OK.NO)
    repeat_time = Column(INTEGER, nullable=False, default=0)
    enabled = Column(INTEGER, nullable=False, default=OK.NO)
    date_started = Column(DateTime)


class SettingsStatus(BaseTable):
    """Test settings results table model"""
    __tablename__ = "settings_status"

    db_status = Column(INTEGER, nullable=False, default=0)
    celery_broker_status = Column(INTEGER, nullable=False, default=0)
    celery_status = Column(INTEGER, nullable=False, default=0)
    redis_status = Column(INTEGER, nullable=False, default=0)


def init_db(db_uri):
    """Create new database and tables"""
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
