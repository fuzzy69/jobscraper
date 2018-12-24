# -*- coding: utf-8 -*-

from scrapy import Field, Item


class JobPostItem(Item):
    """Scrapy item"""
    URL = Field()
    Title = Field()
    Location = Field()
    Description = Field()
    Date_Added = Field()
    Date_Job_Posted = Field()
