# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from time import sleep

from lxml.html import fromstring
from requests import get, post, session
from requests.exceptions import RequestException, Timeout, TooManyRedirects


class WebClientError(Exception):
    """Web Client Error"""
    pass


class WebClient:
    """Web Client class"""
    def __init__(self, user_agent: str, delay: float):
        """
        :param str user_agent: user agent string
        :param float delay: delay in seconds between requests
        """
        self.__headers = {}
        self.user_agent = user_agent
        self.__delay = delay
        self.__session = session()
        self.__status_code = None
        self.__error_message = None
        self.__dom = None
        self.__html = None
        self.__head = None
        self.__body = None
        self.__text = None
        self.__url = None
        self.__last_url = None
        self.__response = None

    def _request(self, url: str):
        pass

    @property
    def header(self, key: str) -> object:
        """
        Get header value by header name
        :param str key: header name
        :return: header value object
        """
        return self.headers[key]

    @header.setter
    def header(self, key: str, value: object):
        """
        Set header value
        :param str key: header name
        :param object value: header value
        """
        if key in self.headers:
            self.__headers[key] = value
        else:
            self.__headers.update({key: value})

    def set_header(self, key: str, value: object):
        """
        Set header value
        :param str key: header name
        :param object value: header value
        """
        if key in self.headers:
            self.__headers[key] = value
        else:
            self.__headers.update({key: value})

    @property
    def headers(self) -> dict:
        """Return headers dictionary"""
        return self.__headers

    @headers.setter
    def headers(self, headers: dict):
        """
        Set request headers dictionary
        :param dict headers: headers dictionary, key -> header name : header value
        :return:
        """
        self.__headers = headers

    @property
    def user_agent(self) -> str:
        """Get user agent string"""
        return self.__headers["User-Agent"]

    @user_agent.setter
    def user_agent(self, user_agent: str):
        """
        Set user agent string
        :param str user_agent: user agent string
        :return:
        """
        self.__headers["User-Agent"] = user_agent

    @property
    def status_code(self) -> int:
        """Response status code number"""
        return self.__status_code

    @property
    def html(self) -> str:
        """Response HTML string"""
        return self.__html

    @property
    def url(self) -> str:
        """Current URL"""
        return self.__url

    @property
    def last_url(self) -> str:
        """Last visited URL"""
        return self.__last_url

    @property
    def error_message(self) -> str:
        """Error message string"""
        return self.__error_message

    @property
    def response(self):
        return self.__response

    @property
    def dom(self):
        """Response HTML DOM"""
        return self.__dom

    @property
    def head(self):
        """Response head"""
        return self.__head

    @property
    def body(self):
        """Response body"""
        return self.__body

    @property
    def text(self):
        """Response HTML text"""
        if self.dom is None:
            self.__dom = fromstring(self.html)
        self.__text = self.dom.text_content()

        return self.__text

    def init(self, headers: dict = None):
        """
        Return instance properties to init values
        :param dict headers: request headers
        """
        self.__session = session()
        if headers is not None:
            self.__headers = headers
        self.__status_code = None
        self.__error_message = None
        self.__dom = None
        self.__html = None
        self.__head = None
        self.__body = None
        self.__text = None
        self.__response = None

    def get(self, url: str) -> tuple:
        """
        Perform GET request
        :param str url: URL address
        :return: tuple of response status code number and HTML string
        :raise: WebClientError
        """
        # self.init()
        sleep(self.__delay)
        try:
            # self.__response = get(url, headers=self.headers)
            self.__response = self.__session.get(url, headers=self.headers)
        except Timeout as e:
            self.__error_message = e
            # raise WebClientError(e)
        except TooManyRedirects as e:
            self.__error_message = e
        except RequestException as e:
            self.__error_message = e
        except Exception as e:
            raise WebClientError(e)
        if self.__response is None:
            return None, None
        self.__status_code = self.__response.status_code
        self.__html = self.__response.text
        self.__url = self.__response.url
        self.__last_url = self.url

        return self.status_code, self.html

    def post(self, url: str, data: dict=None) -> bool:
        # self.init()
        sleep(self.__delay)
        try:
            if data is None:
                # self.__response = post(url, headers=self.headers)
                self.__response = self.__session.post(url, headers=self.headers)
            else:
                # self.__response = post(url, data, headers=self.headers)
                self.__response = self.__session.post(url, data, headers=self.headers)
        except Timeout as e:
            self.__error_message = e
            # raise WebClientError(e)
        except TooManyRedirects as e:
            self.__error_message = e
        except RequestException as e:
            self.__error_message = e
        except Exception as e:
            raise WebClientError(e)
        if self.__response is None:
            return None, None
        self.__status_code = self.__response.status_code
        self.__html = self.__response.text
        self.__url = self.__response.url
        self.__last_url = self.url

        return self.status_code, self.html

    def options(self, url: str):
        # self.init()
        sleep(self.__delay)
        try:
            self.__response = self.__session.options(url, headers=self.headers)
        except Timeout as e:
            self.__error_message = e
            # raise WebClientError(e)
        except TooManyRedirects as e:
            self.__error_message = e
        except RequestException as e:
            self.__error_message = e
        except Exception as e:
            raise WebClientError(e)
        if self.__response is None:
            return None, None
        self.__status_code = self.__response.status_code
        self.__html = self.__response.text
        self.__url = self.__response.url
        self.__last_url = self.url

        return self.status_code, self.html

    def json(self, url: str) -> dict:
        """
        Return JSON resource from GET request
        :param str url: URL address
        :return: JSON dictionary or None
        """
        status_code, _ = self.get(url)
        if status_code != 200:
            return None

        return self.__response.json()

    def xpath(self, selector: str) -> object:
        """
        Perform XPATH query on response object
        :param str selector: XPATH selector
        :return: XPATH object
        """
        if self.dom is None:
            self.__dom = DOMSelector(self.html)

        return self.dom.xpath(selector)


class DOMSelector:
    """DOM Selector class"""
    def __init__(self, html: str):
        """
        :param str html: HTML string
        """
        self._dom = fromstring(html)
        self._elements = []
        self._element = None

    def xpath(self, selector: str) -> object:
        """
        Perform XPATH query on provided HTML string
        :param str selector: XPATH selector string
        :return: DOMSelector instance
        """
        self._elements = self._dom.xpath(selector)
        return self

    def all(self) -> list:
        """Return all DOM elements from result"""
        return self._elements

    def first(self) -> object:
        """Return first DOM element from result"""
        self._element = self._elements[0] if len(self._elements) > 0 else None
        return self

    def text(self) -> str:
        """Return text content of DOM element or None"""
        return self._element.text_content() if self._element is not None else None
