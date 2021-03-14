import sys
import unittest

import parascoring.scoring.IgcUtils
import parascoring.scoring.Utils
from parascoring.scoring import scorer as s
import time
from datetime import datetime, timedelta

from parascoring.scoring.WaypointOptimizer import WaypointOptimizer
from parascoring.scoring.scorer import _score_igc
from parascoring.scoring.WptOriginal import WaypointCounter
from parascoring.scoring.Utils import parse_wpt_file, WptType

WPT_DICT = parse_wpt_file('resources/WanakaHikeFly2.wpt')
WPT_CONFIG = {'cylinder_km': 1, 'time_landed_min': 1,
              'time_altitude_var_meters': 30, 'distance_variance_meters': 10,
              'precision_km': 1,
              'finish_penalty_pts': 0}


class TestScorerMethods(unittest.TestCase):
    def test_real_igc_1(self):
        import time
        seconds = time.time()
        self.real_igc_1(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.real_igc_1(WaypointOptimizer)
        print(time.time() - seconds)

    def test_real_igc_2(self):
        import time
        seconds = time.time()
        self.real_igc_2(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.real_igc_2(WaypointOptimizer)
        print(time.time() - seconds)

    def test_real_igc_3(self):
        import time
        seconds = time.time()
        self.real_igc_3(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.real_igc_3(WaypointOptimizer)
        print(time.time() - seconds)

    def test_multi_real_igc_3(self):
        import time
        seconds = time.time()
        self.multi_real_igc_3(s.score_igcs)
        print(time.time() - seconds)
        seconds = time.time()
        self.multi_real_igc_3(s.score_igcs_optimized)
        print(time.time() - seconds)

    def test_parse_wpt(self):
        data = parascoring.scoring.Utils.parse_wpt_file('resources/WanakaHikeFly.wpt')
        self.assertTrue('START' in data)
        self.assertTrue('1_MTALPH' in data)
        self.assertTrue('1_MTHYDE' in data)
        self.assertEqual(data['START'].name, 'START')
        self.assertAlmostEqual(data['START'].longitude, -44.68671111111111, delta=sys.float_info.epsilon)
        self.assertAlmostEqual(data['START'].latitude, 169.09749722222224, delta=sys.float_info.epsilon)
        self.assertEqual(data['START'].msl, 284)
        self.assertEqual(data['START'].wpt_type, WptType.TOUCH)
        self.assertEqual(data['START'].pts, 0)
        self.parse_1_pt(data)
        self.parse_1_pt_land(data)
        self.parse_2_pt(data)
        self.parse_2_pt_land(data)
        self.parse_camp(data)

    def parse_1_pt(self, data):
        self.assertEqual(data['1_MTHYDE'].name, '1_MTHYDE')
        self.assertEqual(data['1_MTHYDE'].pts, 1)
        self.assertEqual(data['1_MTHYDE'].wpt_type, WptType.TOUCH)

    def parse_1_pt_land(self, data):
        self.assertEqual(data['1X_SAWYER'].name, '1X_SAWYER')
        self.assertEqual(data['1X_SAWYER'].pts, 1)
        self.assertEqual(data['1X_SAWYER'].wpt_type, WptType.LAND)

    def parse_2_pt(self, data):
        self.assertEqual(data['2_MTLARK'].name, '2_MTLARK')
        self.assertEqual(data['2_MTLARK'].pts, 2)
        self.assertEqual(data['2_MTLARK'].wpt_type, WptType.TOUCH)

    def parse_2_pt_land(self, data):
        self.assertEqual(data['2X_MCINTO'].name, '2X_MCINTO')
        self.assertEqual(data['2X_MCINTO'].pts, 2)
        self.assertEqual(data['2X_MCINTO'].wpt_type, WptType.LAND)

    def parse_camp(self, data):
        self.assertEqual(data['5S_NIGHT'].name, '5S_NIGHT')
        self.assertEqual(data['5S_NIGHT'].pts, 5)
        self.assertEqual(data['5S_NIGHT'].wpt_type, WptType.CAMP)

    def test_parse_igc_line(self):
        igc_line = 'B1102255206417N00006098WA0063100596'
        curr_date = datetime(year=2020, month=10, day=19)

        igc_info = parascoring.scoring.IgcUtils.parse_igc_basic_line(igc_line, curr_date)

        actual_date = datetime(year=2020, month=10, day=19, hour=11, minute=2, second=25)
        self.assertEqual(igc_info.time, actual_date)
        self.assertAlmostEqual(igc_info.longitude, 52.10695, delta=sys.float_info.epsilon)
        self.assertAlmostEqual(igc_info.latitude, -0.10163333333333333, delta=sys.float_info.epsilon)
        self.assertEqual(igc_info.alt_pressure, 631)
        self.assertEqual(igc_info.alt_gps, 596)

    def test_get_score_report_1_pt(self):
        import time
        seconds = time.time()
        self.get_score_report_1_pt(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.get_score_report_1_pt(WaypointOptimizer)
        print(time.time() - seconds)

    def test_get_score_report_2_pts(self):
        import time
        seconds = time.time()
        self.get_score_report_2_pts(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.get_score_report_2_pts(WaypointOptimizer)
        print(time.time() - seconds)

    def test_get_score_report_1_pt_land(self):
        import time
        seconds = time.time()
        self.get_score_report_1_pt_land(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.get_score_report_1_pt_land(WaypointOptimizer)
        print(time.time() - seconds)

    def test_get_score_report_2_pt_land(self):
        import time
        seconds = time.time()
        self.get_score_report_2_pt_land(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.get_score_report_2_pt_land(WaypointOptimizer)
        print(time.time() - seconds)

    def test_get_score_report_2_pt_land_within_10m_margin(self):
        import time
        seconds = time.time()
        self.get_score_report_2_pt_land_within_10m_margin(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.get_score_report_2_pt_land_within_10m_margin(WaypointOptimizer)
        print(time.time() - seconds)

    def test_get_score_report_2_pt_fail_no_land(self):
        import time
        seconds = time.time()
        self.get_score_report_2_pt_fail_no_land(WaypointCounter)
        print(time.time() - seconds)
        seconds = time.time()
        self.get_score_report_2_pt_fail_no_land(WaypointOptimizer)
        print(time.time() - seconds)

    def test_score_report_2_pts_finish(self):
        wpt_config = {'cylinder_km': 1, 'time_landed_min': 1,
                      'time_altitude_var_meters': 30, 'distance_variance_meters': 10,
                      'precision_km': 1,
                      'finish_penalty_pts': -8}
        lon_1 = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 56 57.78')
        lat_1 = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 168 32 20.86')
        igc_list = ['HFDTE270920', 'B110225{}{}A0063100596'.format(lon_1, lat_1)]  # B1102254435000S16849015EA0063100596
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 40 20.36')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 169 00 26.78')
        igc_list.append('B110325{}{}A0063100596'.format(lon, lat))  # B1102254435000S16849015EA0063100596
        print(igc_list)
        wpt_counter = WaypointOptimizer(WPT_DICT, wpt_config)
        _score_igc(igc_list, wpt_counter)
        score_report = wpt_counter.get_score_report()
        self.assertEqual(2, score_report['total'])
        self.assertEqual('2_BENMOR', score_report['wpt_list'][0]['wpt'])

    def test_score_report_2_pts_no_finish(self):
        wpt_config = {'cylinder_km': 1, 'time_landed_min': 1,
                      'time_altitude_var_meters': 30, 'distance_variance_meters': 10,
                      'precision_km': 1,
                      'finish_penalty_pts': -8}
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 56 57.78')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 168 32 20.86')
        igc_list = ['HFDTE270920', 'B110225{}{}A0063100596'.format(lon, lat)]  # B1102254435000S16849015EA0063100596
        print(igc_list)
        wpt_counter = WaypointOptimizer(WPT_DICT, wpt_config)
        _score_igc(igc_list, wpt_counter)
        score_report = wpt_counter.get_score_report()
        self.assertEqual(-6, score_report['total'])
        self.assertEqual('2_BENMOR', score_report['wpt_list'][0]['wpt'])

    def real_igc_1(self, counter_type):
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        s.score_igc('resources/2020-11-11-XCT-KMA-01.igc', wpt_counter)
        score_report = wpt_counter.get_score_report()
        print('2020-11-11-XCT-KMA-01.igc')
        print('Total points: ' + str(score_report['total']))
        print(score_report['wpt_list'])
        self.assertEqual(6, score_report['total'])

    def real_igc_2(self, counter_type):
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        s.score_igc('resources/2020-11-29-XCT-KMA-01.igc', wpt_counter)
        score_report = wpt_counter.get_score_report()
        print('2020-11-29-XCT-KMA-01.igc')
        print('Total points: ' + str(score_report['total']))
        print(score_report['wpt_list'])
        self.assertEqual(6, score_report['total'])

    def real_igc_3(self, counter_type):
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        s.score_igc('resources/2021-02-05-XFH-000-01.IGC', wpt_counter)
        score_report = wpt_counter.get_score_report()
        print('2021-02-05-XFH-000-01.IGC')
        print('Total points: ' + str(score_report['total']))
        print(score_report['wpt_list'])
        self.assertEqual(7, score_report['total'])

    def multi_real_igc_3(self, score_igcs_func):
        score_report = score_igcs_func(
            ['resources/2021-02-05-XFH-000-01.IGC',
             'resources/2020-11-29-XCT-KMA-01.igc',
             'resources/2020-11-11-XCT-KMA-01.igc'],
            WPT_DICT, WPT_CONFIG)
        print('Total points: ' + str(score_report['total']))
        print(score_report['wpt_list'])
        self.assertEqual(11, score_report['total'])

    def test_multi_real_igc_with_finish_penalty(self):
        wpt_config = {'cylinder_km': 1, 'time_landed_min': 1,
                      'time_altitude_var_meters': 30, 'distance_variance_meters': 10,
                      'precision_km': 1,
                      'finish_penalty_pts': -8}
        score_report = s.score_igcs_optimized(
            ['resources/2021-02-05-XFH-000-01.IGC',
             'resources/2020-11-29-XCT-KMA-01.igc',
             'resources/2020-11-11-XCT-KMA-01.igc'],
            WPT_DICT, wpt_config)
        print('Total points: ' + str(score_report['total']))
        print(score_report['wpt_list'])
        self.assertEqual(3, score_report['total'])

    def get_score_report_1_pt(self, counter_type):
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 35 00.91')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 168 49 54.69')
        igc_list = ['HFDTE270920', 'B110225{}{}A0063100596'.format(lon, lat)]  # B1102254435000S16849015EA0063100596
        print(igc_list)
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        _score_igc(igc_list, wpt_counter)
        score_report = wpt_counter.get_score_report()
        self.assertEqual(score_report['total'], 1)

    def get_score_report_2_pts(self, counter_type):
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 56 57.78')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 168 32 20.86')
        igc_list = ['HFDTE270920', 'B110225{}{}A0063100596'.format(lon, lat)]  # B1102254435000S16849015EA0063100596
        print(igc_list)
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        _score_igc(igc_list, wpt_counter)
        score_report = wpt_counter.get_score_report()
        self.assertEqual(2, score_report['total'])
        self.assertEqual('2_BENMOR', score_report['wpt_list'][0]['wpt'])

    def get_score_report_1_pt_land(self, counter_type):
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 33 43.70')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 169 21 26.95')
        igc_list = ['HFDTE270920']
        current_time = datetime.fromtimestamp(time.time())
        for i in range(20):
            igc_list.append('B{}{}{}A0063100596'.format(current_time.strftime('%H%M%S'), lon, lat))
            current_time = current_time + timedelta(seconds=10)
        print(igc_list)
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        _score_igc(igc_list, wpt_counter)
        score_report = wpt_counter.get_score_report()
        self.assertEqual(1, score_report['total'])
        self.assertEqual('1X_BREAST', score_report['wpt_list'][0]['wpt'])

    def get_score_report_2_pt_land(self, counter_type):
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 54 09.64')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 168 49 11.92')
        igc_list = ['HFDTE270920']
        current_time = datetime.fromtimestamp(time.time())
        for i in range(20):
            igc_list.append('B{}{}{}A0063100596'.format(current_time.strftime('%H%M%S'), lon, lat))
            current_time = current_time + timedelta(seconds=10)
        print(igc_list)
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        _score_igc(igc_list, wpt_counter)
        score_report = wpt_counter.get_score_report()
        self.assertEqual(score_report['total'], 2)
        self.assertEqual(score_report['wpt_list'][0]['wpt'], '2X_BROWP')

    def get_score_report_2_pt_land_within_10m_margin(self, counter_type):
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 54 09.64')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 168 49 11.92')
        igc_list = ['HFDTE270920']
        current_time = datetime.fromtimestamp(time.time())
        igc_list.append('B{}{}{}A0063100596'.format(current_time.strftime('%H%M%S'), lon, lat))
        current_time = current_time + timedelta(minutes=1)
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 54 09.94')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 168 49 11.95')
        igc_list.append('B{}{}{}A0063100596'.format(current_time.strftime('%H%M%S'), lon, lat))
        print(igc_list)
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        _score_igc(igc_list, wpt_counter)
        score_report = wpt_counter.get_score_report()
        self.assertEqual(score_report['total'], 2)
        self.assertEqual(score_report['wpt_list'][0]['wpt'], '2X_BROWP')

    def get_score_report_2_pt_fail_no_land(self, counter_type):
        lon = parascoring.scoring.Utils.deg_wpt_to_deg_igc('S 44 54 09.64')
        lat = parascoring.scoring.Utils.deg_wpt_to_deg_igc('E 168 49 11.92')
        igc_list = ['HFDTE270920']
        current_time = datetime.fromtimestamp(time.time())
        altitude_press = 631
        altitude_gps = 596
        for i in range(20):
            igc_list.append('B{}{}{}A00{}00{}'.format(current_time.strftime('%H%M%S'), lon, lat,
                                                      str(altitude_press), str(altitude_gps)))
            current_time = current_time + timedelta(seconds=10)
            altitude_gps = altitude_gps + 10
            altitude_press = altitude_press + 10
        print(igc_list)
        wpt_counter = counter_type(WPT_DICT, WPT_CONFIG)
        _score_igc(igc_list, wpt_counter)
        score_report = wpt_counter.get_score_report()
        self.assertEqual(score_report['total'], 0)


if __name__ == '__main__':
    unittest.main()
