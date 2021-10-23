import os
import unittest

from parascoring.scoring_lambda import handler


class TestHandler(unittest.TestCase):
    def setUp(self):
        os.environ['STORAGE_S34FF28839_BUCKETNAME'] = \
            'creativecompetitions092919f18fad469faf10c60bf4394337-dev'

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
            'pathParameters': {'compid': 'WANAKA_2021'},
            'queryStringParameters': {'userid': 'fa9e1bf2-a515-49f2-9c79-668c067f63c3', 'night_checkpoint': 'false'}
        }
        response = handler.handler(event, None)
        print(response)
        self.assertEqual(200, response['statusCode'])

    # def update_score(self):
    #     WPT_DICT = parse_wpt_file('resources/WanakaHikeFly.wpt')
    #     WPT_CONFIG = {'cylinder_km': 1, 'time_landed_min': 1, 'time_altitude_var_meters': 30,
    #                   'distance_variance_meters': 10}
    #     score_report = score_igcs(['resources/2021-02-05-XFH-000-01.IGC',
    #                                'resources/2020-11-29-XCT-KMA-01.igc',
    #                                'resources/2020-11-11-XCT-KMA-01.igc'],
    #                               WPT_DICT, WPT_CONFIG)
    #     print('Total points: ' + str(score_report['total']))
    #     print(score_report['wpt_list'])
    #     response = BusinessHandler()
    #     print(response)
    #     self.assertEqual(200, response['statusCode'])
