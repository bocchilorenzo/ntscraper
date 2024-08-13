from setuptools import setup

from os import path

HERE = path.abspath(path.dirname(__file__))

with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="ntscraper",
    version="0.3.15",
    description="Unofficial library to scrape Twitter profiles and posts from Nitter instances",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        'Homepage': 'https://github.com/bocchilorenzo/ntscraper',
        'Source': 'https://github.com/bocchilorenzo/ntscraper',
        'Documentation': 'https://github.com/bocchilorenzo/ntscraper'
    },
    keywords=["twitter", "nitter", "scraping"],
    author="Lorenzo Bocchi",
    author_email="lorenzobocchi99@yahoo.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent"
    ],
    packages=["ntscraper"],
    include_package_data=True,
    install_requires=["requests>=2.28", "beautifulsoup4>=4.11", "lxml>=4.9", "tqdm>=4.66"],
)