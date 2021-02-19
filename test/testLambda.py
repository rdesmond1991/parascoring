import sys
import unittest
from parascoring.scoring_lambda import handler


class TestHandler(unittest.TestCase):

    def test_malformed_request_no_competition_id(self):
        event = {
            'User_id': '53929f30-14b5-4a20-aa8a-49a44fd540f6'
        }
        response = handler.handler(event, None)
        self.assertEqual(400, response['statusCode'])

    def test_malformed_request_no_user_id(self):
        event = {
            'Competition_id': 'TEST_COMPETITION'
        }
        response = handler.handler(event, None)
        self.assertEqual(400, response['statusCode'])

    def test_score_id(self):
        event = {
            'Competition_id': 'TEST_COMPETITION',
            'User_id': '53929f30-14b5-4a20-aa8a-49a44fd540f6'
        }
        response = handler.handler(event, None)
        self.assertEqual(200, response['statusCode'])
        print(response)


