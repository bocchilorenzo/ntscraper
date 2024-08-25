import unittest
from ntscraper import Nitter


class TestProfile(unittest.TestCase):
    def setUp(self):
        self.nitter = Nitter()

    def test_scrape_profile_info(self):
        """
        Test scraping profile info of a username (Twitter, we need a stable username)
        """
        profile = self.nitter.get_profile_info("X")
        self.assertEqual(profile['name'], "X")
        self.assertEqual(profile['username'], "@X")
        self.assertEqual(profile['bio'], "what's happening?!")
        self.assertEqual(profile['location'], 'everywhere')
        self.assertEqual(profile['website'], 'https://x.com')
        self.assertEqual(profile['joined'], '2:35 PM - 20 Feb 2007')
        self.assertGreater(profile['stats']['tweets'], 0)
        self.assertGreater(profile['stats']['likes'], 0)

    def test_scrape_profile_tweets(self):
        """
        Test scraping profile tweets of a username (Twitter, we need a stable username)
        """
        tweets = self.nitter.get_tweets("X", 'user')
        self.assertGreater(len(tweets['tweets']), 0)

    def test_scrape_profile_tweets_since(self):
        """
        Test scraping profile tweets of a username (Twitter, we need a stable username) in a certain time period
        """
        tweets = self.nitter.get_tweets("X", mode='user', since='2023-12-01', until='2024-04-21', number=1)
        print(tweets)
        self.assertGreater(len(tweets['threads']), 0)
