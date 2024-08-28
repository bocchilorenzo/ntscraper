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
        nitter = Nitter()
        tweets0 = nitter.get_tweets("Snowden", 'user', number=30, ignore_pinned=True, ignore_retweets=True)['tweets']
        selected = self.getTweetId(tweets0[len(tweets0) - 2])
        tweets1 = nitter.get_tweets("Snowden", 'user', ignore_pinned=True,
                                    ignore_retweets=True, since_id=selected)['tweets']
        self.assertTrue(len(tweets1) == len(tweets0) - 2)
        for tweet in tweets1:
            self.assertTrue(int(self.getTweetId(tweet)) > int(selected))

    def test_get_tweets_since_tweet_date(self):
        """
        Test scraping tweets since a specific tweet ID
        """
        nitter = Nitter()
        tweets0 = nitter.get_tweets("Snowden", 'user', number=30, ignore_pinned=True, ignore_retweets=True)['tweets']
        tweet_date = datetime.strptime(tweets0[len(tweets0) - 2]["date"].split(' · ')[0], '%b %d, %Y')
        tweets1 = nitter.get_tweets("Snowden", 'user', ignore_pinned=True,
                                    ignore_retweets=True, since_date=tweet_date.strftime('%Y-%m-%d'))['tweets']
        self.assertTrue(len(tweets1) == len(tweets0) - 2)
