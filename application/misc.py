# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from config import FEEDS_DIR, SPIDER_LOG_DIR
from os.path import isfile, join


def text_file_to_lines(file_path: str) -> list:
    """
    Returns list of text file lines (skips empty lines)
    :param str file_path: path to text file
    :return: list of line strings
    """
    lines = []
    if isfile(file_path):
        with open(file_path, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line:
                    lines.append(line)

    return lines


def log_file_path(spider_name: str, date_time: str) -> str:
    file_name = "{} {}.log".format(spider_name, str(date_time).split('.')[0].strip().replace(':', '-'))
    log_file = join(SPIDER_LOG_DIR, file_name)

    return log_file


def feed_file_path(spider_name: str, date_time: str) -> str:
    file_name = "{} {}.json".format(spider_name, str(date_time).split('.')[0].strip().replace(':', '-'))
    feed_file = join(FEEDS_DIR, file_name)

    return feed_file
