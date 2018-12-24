# -*- coding: utf-8 -*-

from re import compile, sub, UNICODE
import sys
from time import strftime
from urllib.parse import parse_qs, quote, urljoin, urlparse

from dateparser import parse
from scrapy import Request

try:  # main
    from config import COUNTRIES, TIMESTAMP_FORMAT
    from application.scrapers.scrapers.basespider import BaseSpider
    from application.scrapers.scrapers.common import ScrapeType
    from application.scrapers.scrapers.items import JobPostItem
    from application.scrapers.scrapers.models import JobPosts
except ImportError:  # scrapy crawl
    sys.path.append("..")  # allow imports from application directory
    from scrapers.basespider import BaseSpider
    from scrapers.common import ScrapeType
    from scrapers.items import JobPostItem
    from scrapers.models import JobPosts
    from scrapers.settings import COUNTRIES, TIMESTAMP_FORMAT


ALPHANUMSPACE_REGEX = compile(r"\W+ ", UNICODE)


class IndeedSpider(BaseSpider):
    """indeed.com job posts spider"""
    name = "indeed"
    allowed_domains = ["indeed.com"]
    start_urls = []
    base_url = "https://www.indeed.com/"
    pagination_xpath = "//div[@class='pagination']/a/@href"
    item_xpath = "//h2[@class='jobtitle']/a/@href"  # 10 items per page

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scraped_job_post_count = 0

    def start_requests(self):
        """Overridden"""
        countries = self.settings.get("SELECTED_COUNTRIES", [])
        keywords = self.settings.get("KEYWORDS", [])
        if not keywords or not countries:
            self.logger.warning("In order to start scrape please add keywords and select target countries")
            return
        self.logger.info("Target keywords: '{}'".format(', '.join(keywords)))
        self.logger.info("Target countries: '{}'".format(', '.join(countries)))
        for country in countries:
            if country in COUNTRIES:
                query = '+'.join([quote(kw) for kw in keywords])
                start_url = urljoin(COUNTRIES[country][1], "jobs?q={query}&l=".format(query=query))
                self.__class__.start_urls.append(start_url)
        for url in self.__class__.start_urls:
            yield Request(url, self.parse)

    def parse(self, response):
        """Overridden"""
        # if self._scraped_job_post_count > 4:
        #     return
        job_post_urls = response.xpath(self.__class__.item_xpath).extract()
        self.logger.info("Scraping {} job posts ...".format(len(job_post_urls)))
        for i, job_post_url in enumerate(job_post_urls):
            job_post_url = urljoin(self.__class__.base_url, job_post_url)
            job_post_id = self._get_job_post_id(job_post_url)
            if job_post_id is None:
                continue
            if self._db is not None:
                job_post = self._db.query(JobPosts).filter_by(job_post_id=job_post_id).first()
                if job_post is not None:
                    self.logger.info("Skipping already scraped job post '{}'".format(job_post_url))
                    continue
            item = JobPostItem()
            yield Request(job_post_url, self._parse_job_post, meta={"item": item})
            # if i > 0:
            #     break
        # Pagination
        if self.__class__.pagination_xpath is not None:
            # Go to the next pagination page
            if self._scrape_type == ScrapeType.ALL:
                next_pages_url = response.xpath(self.__class__.pagination_xpath).extract()
                if next_pages_url is not None:
                    for url in next_pages_url:
                        url = urljoin(self.__class__.base_url, url)  # Fix relative URL paths
                        # Skip already visited pagination URLs
                        if url in self._pagination_urls:
                            continue
                        self.logger.info("Scraping next pagination page \"{}\"".format(url))
                        # Scrape pagination page
                        yield Request(url)
                        self._pagination_urls.add(url)
                        break

    def _parse_job_post(self, response):
        item = response.meta["item"]
        self.logger.info("Scraping job post '{}' ...".format(response.url))
        title = response.xpath("//title/text()").extract_first()
        title, location = title.rsplit('-', 1)[0].rsplit('-', 1)
        item["Title"] = title.strip()
        item["URL"] = response.url
        description = response.xpath(
            "//div[contains(@class, 'jobsearch-JobComponent-description')]//text()"
        ).extract()
        item["Description"] = ''.join(description).strip()
        item["Location"] = location.strip()
        item["Date_Added"] = strftime(TIMESTAMP_FORMAT)
        # Convert relative to absolute date
        date_job_posted = None
        relative_time_job_posted = response.xpath("//div[@class='jobsearch-JobMetadataFooter']/text()").extract_first()
        if isinstance(relative_time_job_posted, str):
            relative_time_job_posted = sub(ALPHANUMSPACE_REGEX, '', relative_time_job_posted)
            date_job_posted = parse(relative_time_job_posted)
            if date_job_posted is not None:
                date_job_posted = date_job_posted.strftime(TIMESTAMP_FORMAT)
        if date_job_posted is None:
            self.logger.warning("Failed extracting posted date for job '{}'!".format(item["URL"]))
            return
        item["Date_Job_Posted"] = date_job_posted
        self.logger.info("Successfully scraped '{}'".format(response.url))
        self._scraped_job_post_count += 1

        yield item

    def _get_job_post_id(self, url: str) -> str:
        try:
            job_post_id = parse_qs(urlparse(url).query)["jk"][0]
        except Exception as e:  # TODO: Add specific exceptions
            job_post_id = None
            self.logger.warning("Failed extracting job post ID from '{}'!".format(url))

        return job_post_id
