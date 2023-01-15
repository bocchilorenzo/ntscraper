from setuptools import setup, find_packages

from codecs import open
from os import path

HERE = path.abspath(path.dirname(__file__))

with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="nitter_unofficial",
    version="0.1.0",
    description="Unofficial library to scrape Twitter profiles and posts from Nitter instances",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        'Homepage': 'https://github.com/bocchilorenzo/nitter_unofficial',
        'Source': 'https://github.com/bocchilorenzo/nitter_unofficial',
        'Documentation': 'https://github.com/bocchilorenzo/nitter_unofficial'
    },
    author="Lorenzo Bocchi",
    author_email="lorenzobocchi99@yahoo.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent"
    ],
    packages=["nitter_unofficial"],
    include_package_data=True,
    install_requires=["requests", "beautifulsoup4", "lxml"],
)