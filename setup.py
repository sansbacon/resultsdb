# resultsdb/setup.py
# -*- coding: utf-8 -*-
# Copyright (C) 2021 Eric Truett
# Licensed under the MIT License

from setuptools import setup, find_packages

PACKAGE_NAME = "resultsdb"


def run():
    setup(name=PACKAGE_NAME,
          version="0.1",
          description="python library for analzying resultsdb",
          author="Eric Truett",
          author_email="eric@erictruett.com",
          license="MIT",
          packages=find_packages(),
          entry_points={'console_scripts': ['rdb=scripts.resultsdb:main']},
          package_data={PACKAGE_NAME: ["data/*.*"]},
          zip_safe=False,
          install_requires=["python-dateutil", "tzlocal", "requests"],
    )


if __name__ == '__main__':
    run()
