# Unofficial Nitter scraper

This is a simple library to scrape Nitter instances for tweets. It can:

- search and scrape tweets with a certain term

- search and scrape tweets with a certain hashtag

- scrape tweets from a user profile

- get profile information of a user, such as display name, username, number of tweets, profile picture ...

If the instance to use is not provided to the scraper, it will use a random instance among those listed as "online" and "working" in https://github.com/zedeus/nitter/wiki/Instances.

---

## Installation

```
pip install ntscraper
```

## How to use

First, initialize the library:

```python
from ntscraper import Nitter

scraper = Nitter(log_level=1)
```
The valid logging levels are:
- None = no logs
- 0 = only warning and error logs
- 1 = previous + informational logs (default)

Then, choose the proper function for what you want to do from the following.

### Scrape tweets

```python
github_hash_tweets = scraper.get_tweets("github", mode='hashtag')

bezos_tweets = scraper.get_tweets("JeffBezos", mode='user')
```

Parameters:
- term: search term
- mode: modality to scrape the tweets. Default is 'term' which will look for tweets containing the search term. Other modes are 'hashtag' to search for a hashtag and 'user' to scrape tweets from a user profile
- number: number of tweets to scrape. Default is 5. If 'since' is specified, this is bypassed.
- since: date to start scraping from, formatted as YYYY-MM-DD. Default is None
- until: date to stop scraping at, formatted as YYYY-MM-DD. Default is None
- max_retries: max retries to scrape a page. Default is 5
- instance: Nitter instance to use. Default is None and will be chosen at random

Returns a dictionary with tweets and threads for the term.

#### Multiprocessing

You can also scrape multiple terms at once using multiprocessing:

```python
terms = ["github", "bezos", "musk"]

results = scraper.get_tweets_multiprocessing(terms, mode='term')
```

Each term will be scraped in a different process. The result will be a list of dictionaries, one for each term.

NOTE: only run the multiprocessing code in a `if __name__ == "__main__"` block to avoid errors. With multiprocessing, only full logging is supported. Also, the number of processes is limited to the number of available cores on your machine. Finally, you could experience more rate limiting with multiprocessing (still investigating this).

### Get profile information

```python
bezos_information = scraper.get_profile_info("JeffBezos")
```

Parameters:
- username: username of the page to scrape
- max_retries: max retries to scrape a page. Default is 5
- instance: Nitter instance to use. Default is None

Returns a dictionary of the profile's information.

### Get random Nitter instance

```python
random_instance = scraper.get_random_instance()
```

Returns a random Nitter instance.

## Note

Due to recent changes on Twitter's side, some Nitter instances may not work properly even if they are marked as "working" on Nitter's wiki. If you have trouble scraping with a certain instance, try changing it and check if the problem persists.

## To do list

- [ ] Add scraping of individual posts with comments