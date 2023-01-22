# Unofficial Nitter scraper

This is a simple library to scrape Nitter instances for tweets. It can:

- search and scrape tweets with a certain term

- search and scrape tweets with a certain hashtag

- scrape tweets from a user profile

- get profile information of a user, such as display name, username, number of tweets, profile picture ...

If the instance to use is not provided to the scraper, it will use a random instance among those listed in https://github.com/zedeus/nitter/wiki/Instances.

---

## Installation

```
pip install nitter_unofficial
```

## How to use

First, initialize the library:

```
from nitter_unofficial import Nitter

scraper = Nitter()
```

Then, choose the proper function for what you want to do from the following.

### Scrape tweets

```
github_hash_tweets = scraper.get_tweets("github", mode='hashtag')

bezos_tweets = scraper.get_tweets("JeffBezos", mode='user')
```

Parameters:
- term: search term
- mode: modality to scrape the tweets. Default is 'term' which will look for tweets containing the search term. Other modes are 'hashtag' to search for a hashtag and 'user' to scrape tweets from a user profile
- number: number of tweets to scrape. Default is 5
- max_retries: max retries to scrape a page. Default is 5
- instance: Nitter instance to use. Default is None and will be chosen at random

Returns a dictionary with tweets and threads for the term.

### Get profile information

```
bezos_information = scraper.get_profile_info("JeffBezos")
```

Parameters:
- username: username of the page to scrape
- max_retries: max retries to scrape a page. Default is 5
- instance: Nitter instance to use. Default is None

Returns a dictionary of the profile's information.

### Get random Nitter instance

```
random_instance = scraper.get_random_instance()
```

Returns a random Nitter instance.

## To do list

- [ ] Add scraping of posts and comments