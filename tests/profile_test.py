import unittest
from ntscraper import Nitter

class TestProfile(unittest.TestCase):
    
        def scrape_profile_info(self):
            """
            Test scraping profile info of a username (Twitter, we need a stable username)
            """
            nitter = Nitter()
            profile = nitter.get_profile_info("Twitter")
            self.assertEqual(profile['name'], "Twitter")
            self.assertEqual(profile['username'], "@Twitter")
            self.assertEqual(profile['bio'], "What's happening?!")
            self.assertEqual(profile['location'], 'everywhere')
            self.assertEqual(profile['website'], 'https://about.twitter.com/')
            self.assertEqual(profile['joined'], '2:35 PM - 20 Feb 2007')
            self.assertGreater(profile['stats']['tweets'], 0)
            self.assertGreater(profile['stats']['following'], 0)
            self.assertGreater(profile['stats']['followers'], 0)
            self.assertGreater(profile['stats']['likes'], 0)
            self.assertGreater(profile['stats']['media'], 0)
            self.assertEqual(profile['image'], 'https://pbs.twimg.com/profile_images/1488548719062654976/u6qfBBkF_400x400.jpg')
        
        def scrape_profile_tweets(self):
            """
            Test scraping profile tweets of a username (Twitter, we need a stable username)
            """
            nitter = Nitter()
            tweets = nitter.get_tweets("Twitter", 'user')
            self.assertGreater(len(tweets['tweets']), 0)

        def scrape_profile_tweets_since(self):
            """
            Test scraping profile tweets of a username (Twitter, we need a stable username) in a certain time period
            """
            nitter = Nitter()
            tweets = nitter.get_tweets("Twitter", mode='user', since='2022-12-01', until='2022-12-31', number=1)
            self.assertGreater(len(tweets['threads']), 1)