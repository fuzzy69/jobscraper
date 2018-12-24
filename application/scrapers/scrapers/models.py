# -*- coding: UTF-8 -*-
#!/usr/bin/env python


from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime, Integer, String, Text


Base = declarative_base()


class JobPosts(Base):
    """Job Post table model"""
    __tablename__ = "job_posts"

    id = Column(Integer, primary_key=True)
    job_post_id = Column(String(32), unique=True, nullable=False)
    url = Column(String(512), nullable=False)
    title = Column(String(512), nullable=False)
    location = Column(String(256))
    description = Column(Text(), nullable=False)
    date_added = Column(DateTime, nullable=False)
    date_job_posted = Column(DateTime, nullable=False)


def create_db(db_uri: str, db_name: str):
    """Creates database if not exists"""
    engine = create_engine(db_uri)
    engine.execute("SHOW DATABASES LIKE `{}`".format(db_name))
    engine.execute("CREATE DATABASE IF NOT EXISTS `{}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(db_name))
    engine.execute("USE `{}`".format(db_name))


def init_db(db_uri: str):
    """Creates tables for given database"""
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    # JobPosts.metadata.create_all(engine)


def create_tables(db_uri: str):
    """Creates tables for given database"""
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)


def table_exists(db_uri: str, table: str):
    engine = create_engine(db_uri)
    return engine.dialect.has_table(engine, table)
