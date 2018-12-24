# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from enum import IntEnum


class ScrapeType(IntEnum):
    """Scrape types"""
    ALL, NEW, UNSCRAPED = range(3)


class SpiderStatus(IntEnum):
    """Spider statuses"""
    PENDING, RUNNING, FINISHED, CANCELED = range(4)


class JobStatus(IntEnum):
    """Job statuses"""
    DISABLED, ENABLED = range(2)


class JobType(IntEnum):
    """Job types"""
    ONETIME, PERIODIC = range(2)


class UseProxies(IntEnum):
    """Proxy usage enabled"""
    NO, YES = range(2)


class OK(IntEnum):
    """Dummy OK"""
    NO, YES = range(2)
