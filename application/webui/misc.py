# -*- coding: UTF-8 -*-
#!/usr/bin/env python

from logging import Filter
from os import listdir, makedirs, remove
from os.path import exists, isfile, join, splitext
from pickle import dump, load


class Data:
    def __init__(self, **data):
        self.__dict__.update(data)


class Settings:
    """Simple generic settings class"""

    def __init__(self, **kwargs):
        self._data = {}
        for name, value in kwargs.items():
            self._data.update({
                name: (value, type(value)),
            })

    def __str__(self):
        """Overridden"""
        return str(self._to_dict())

    def __contains__(self, item):
        """Overridden"""
        return item in self._data

    def _to_dict(self):
        """"""
        data = {}
        for key, (value, _) in self._data.items():
            data[key] = value

        return data

    def to_dict(self) -> dict:
        """Returns current Settings instance as a dict"""
        return self._to_dict()

    def to_object(self):
        """Returns current Settings instance as a Data instance"""
        data = {}
        for key, (value, _) in self._data.items():
            data[key] = value

        return Data(**data)

    def key(self, name: str) -> object:
        """
        Returns key value object
        :param str name: key name
        :return: key value
        """
        if name not in self._data:
            raise KeyError("'{}' key not in {}!".format(name, self.__class__.__name__))

        return self._data[name][0]

    def set_key(self, name: str, value: object, from_string: bool=False):
        """
        Sets existing key to given value
        :param str name: key name
        :param object value: key value
        :param bool from_string:
        """
        if name not in self._data:
            raise KeyError("'{}' key not in {}!".format(name, self.__class__.__name__))
        _, type_ = self._data[name]
        if from_string:
            value = type_(value)
        if not isinstance(value, type_):
            raise TypeError("'{}' key should be {} type".format(name, type_))
        self._data[name] = value, type_

    def create_key(self, name: str, value: object, type_: type=None):
        """
        Sets key value object
        :param str name: key name
        :param object value: key value
        :param type type_: key type
        """
        value = type_(value)  # Force key cast to type
        if name in self:
            self._data[name] = value, type_
        else:
            self._data.update({
                name: (value, type_),
            })

    def save(self, file_path: str):
        """
        Serialize keys to file
        :param str file_path: pickle file path
        """
        with open(file_path, "wb") as f:
            dump(self._data, f)

    def load(self, file_path: str):
        """
        Deserialize keys from the file
        :param str file_path: pickle file path
        """
        with open(file_path, "rb") as f:
            data = load(f)
        self._data = data


def text_to_unique_lines(text: str) -> set:
    """
    Splits text by newlines to set of lines ignoring the blank ones
    :param str text: source text
    :return: set of text lines
    """
    lines = set()
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            lines.add(line)

    return lines


class StaticFilesFilter(Filter):
    """Custom logging filter"""
    def filter(self, record):
        """Removes details about static files and dynamic pages from logs"""
        show_message = True
        if "GET /static/" in record.getMessage():
            show_message = False
        elif "GET /xhr/" in record.getMessage():
            show_message = False

        return show_message


def list_files(dir_path: str, file_types: list=[],  recursive: bool=False) -> list:
    files = []
    for file_name in listdir(dir_path):
        file_path = join(dir_path, file_name)
        if file_types:
            _, ext = splitext(file_path)
            if ext.strip('.') in file_types:
                files.append(file_path)
        else:
            files.append(file_path)

    return files


def remove_files(files: list) -> list:
    removed_files = []
    for file_path in files:
        if isfile(file_path):
            remove(file_path)
            removed_files.append(file_path)

    return removed_files


def ensure_dir(dir_path: str) -> bool:
    """
    Create directory path if it doesn't exists
    :param str dir_path: full path to target directory
    :return: return True if directory path is created or False if it already exists
    :raise: when creating directories fails (permission issue, unreachable target media, etc ...)
    """
    if not exists(dir_path):
        makedirs(dir_path)
        return True

    return False
