import unittest
from ntscraper import Nitter

class TestProfile(unittest.TestCase):
    def get_instances(self):
        """
        Test retrieval of instances. Should only return updated instances.
        """
        nitter = Nitter()
        instances = nitter.__get_instances()
        self.assertGreater(len(instances), 0)