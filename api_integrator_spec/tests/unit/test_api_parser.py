import unittest
from api_integrator_spec.domain.services.api_parser import ApiParser

class TestApiParser(unittest.TestCase):
    def test_action_requests(self):
        api = ApiParser('api_parser_conf.yml')
        requests = api.action_requests('auth', {'user': 'test', 'pass': 'test'})
        self.assertIsNotNone(requests)

if __name__ == '__main__':
    unittest.main()
