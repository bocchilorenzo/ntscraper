import unittest
from ntscraper import Nitter

class TestSearch(unittest.TestCase):

    def scrape_term(self):
        """
        Test scraping a term
        """
        nitter = Nitter()
        tweets = nitter.get_tweets("Twitter", 'term')
        self.assertGreater(len(tweets['tweets']), 0)

    def scrape_hashtag(self):
        """
        Test scraping a hashtag
        """
        nitter = Nitter()
        tweets = nitter.get_tweets("twitter", 'hashtag')
        self.assertGreater(len(tweets['tweets']), 0)

    def random_instance(self):
            """
            Test whether a random instance is returned
            """
            nitter = Nitter()
            self.assertIsNotNone(nitter.get_random_instance())