import re
import unittest
from datetime import datetime

from ntscraper import Nitter


class TestSearch(unittest.TestCase):

    def getTweetId(self, tweet) -> str:
        return re.search(r'/status/(\d+)', tweet["link"]).group(1)

        def test_scrape_term(self):
            """
            Test scraping a term
            """
            nitter = Nitter()
            tweets = nitter.get_tweets("Twitter", 'term')
            self.assertGreater(len(tweets['tweets']), 0)

    def test_scrape_user(self):
        """
        Test scraping a user
        """
        nitter = Nitter()
        tweets = nitter.get_tweets("@X", mode='user', number=10)
        self.assertGreater(len(tweets['tweets']), 0)

    def scrape_hashtag(self):
        """
        Test scraping a hashtag
        """
        nitter = Nitter()
        tweets = nitter.get_tweets("ai", 'hashtag')
        self.assertGreater(len(tweets['tweets']), 0)

    def random_instance(self):
        """
        Test whether a random instance is returned
        """
        nitter = Nitter()
        self.assertIsNotNone(nitter.get_random_instance())

    def test_get_tweets_since_tweet_id(self):
        """
        Test scraping tweets since a specific tweet ID
        """
        proxies = [
            {'http': 'http://104.207.34.158:3128', 'https': 'http://104.207.34.158:3128'},
            {'http': 'http://104.167.27.40:3128', 'https': 'http://104.167.27.40:3128'},
            {'http': 'http://104.207.35.115:3128', 'https': 'http://104.207.35.115:3128'},
            {'http': 'http://104.167.30.204:3128', 'https': 'http://104.167.30.204:3128'},
            # Add the rest of the proxies here...
        ]
        nitter = Nitter(proxies=proxies, instances=["https://nitter.privacydev.net"])
        tweets0 = nitter.get_tweets("Snowden", 'user', number=30, ignore_pinned=True, ignore_retweets=True)['tweets']
        selected = self.getTweetId(tweets0[len(tweets0) - 2])
        tweets1 = nitter.get_tweets("Snowden", 'user', ignore_pinned=True,
                                    ignore_retweets=True, since_id=selected)['tweets']
        self.assertTrue(len(tweets1) == len(tweets0) - 2)
        for tweet in tweets1:
            self.assertTrue(int(self.getTweetId(tweet)) > int(selected))

    def test_get_tweets_since_date(self):
        """
        Test scraping tweets since a specific date
        """
        nitter = Nitter()
        tweets = nitter.get_tweets_since("jack", since_date="2023-08-01", count=5)
        self.assertGreater(len(tweets), 0)
        for tweet in tweets:
            tweet_date = datetime.strptime(tweet["date"].split(' · ')[0], '%b %d, %Y')
            self.assertGreaterEqual(tweet_date, datetime(2023, 8, 1))
