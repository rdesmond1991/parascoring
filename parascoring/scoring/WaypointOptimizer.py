from abc import ABC
from collections import defaultdict
from datetime import timedelta

import numpy

from parascoring.scoring.IgcUtils import IGCInfo
from parascoring.scoring.Utils import get_distance_from_lat_lon_in_km, WptType, WptDefinition
from parascoring.scoring.WptOriginal import WptStatus
from collections import OrderedDict


class WptWrapper(ABC):
    wpt: WptDefinition

    def __init__(self, wpt: WptDefinition):
        self.wpt = wpt

    def submit(self, igc_info) -> WptStatus:
        pass

    def reset(self):
        pass

    def get_wpt(self):
        return self.wpt

    def is_finish(self):
        return self.wpt.name == "FINISH"


class TagWaypoint(WptWrapper):
    def __init__(self, wpt: WptDefinition, wpt_config: dict):
        super().__init__(wpt)
        self._wpt_config = wpt_config

    def submit(self, igc_info) -> WptStatus:
        if self._wpt_config['cylinder_km'] >= \
                get_distance_from_lat_lon_in_km(igc_info.latitude, igc_info.longitude,
                                                self.wpt.latitude, self.wpt.longitude):
            return WptStatus.SUCCESS
        return WptStatus.MISSED


class LandWpt(WptWrapper):
    start_igc: IGCInfo

    def __init__(self, wpt: WptDefinition, wpt_config: dict):
        super().__init__(wpt)
        self._wpt_config = wpt_config
        self.reset()

    def submit(self, igc_info) -> WptStatus:
        wpt = self.wpt
        if self._wpt_config['cylinder_km'] >= \
                get_distance_from_lat_lon_in_km(igc_info.latitude, igc_info.longitude,
                                                wpt.latitude, wpt.longitude):
            # If waypoint is active but was not in bounds and altitude is not constant reset start_time.
            if not self.start_igc:
                self.start_igc = igc_info
                return WptStatus.ACTIVE
            alt_variance = self._wpt_config['time_altitude_var_meters']
            alt_gps_condition = \
                numpy.abs(self.start_igc.alt_gps - igc_info.alt_gps) <= alt_variance
            distance = get_distance_from_lat_lon_in_km(igc_info.latitude, igc_info.longitude,
                                                       self.start_igc.latitude, self.start_igc.longitude)
            distance_condition = distance * 1000 < self._wpt_config['distance_variance_meters']
            if self.start_igc and alt_gps_condition and distance_condition:
                if (igc_info.time - self.start_igc.time) >= timedelta(minutes=self._wpt_config['time_landed_min']):
                    return WptStatus.SUCCESS
            else:
                self.start_igc = igc_info
                return WptStatus.ACTIVE

        else:
            self.reset()
        return WptStatus.MISSED

    def reset(self):
        self.start_igc = None


def waypoint_factory(wpt: WptDefinition, wpt_config) -> WptWrapper:
    if wpt.wpt_type is WptType.TOUCH:
        return TagWaypoint(wpt, wpt_config)
    if wpt.wpt_type is WptType.LAND:
        return LandWpt(wpt, wpt_config)
    if wpt.wpt_type is WptType.CAMP:
        return None
    return None


class WaypointOptimizer:
    def __init__(self, wpt_data: dict, wpt_config: dict):
        self.wpt_data = wpt_data
        self.wpt_config = wpt_config
        self.wpts_hit = OrderedDict()
        self.long_wpts = defaultdict(set)
        self.lat_wpts = defaultdict(set)
        self.precision_km = wpt_config['precision_km']
        self.active_waypoints = set()
        self.wpt_keys = defaultdict(list)
        self._create_optimization_table()

    def _create_optimization_table(self):
        # Each decimal place 1.0 == 111km
        for wpt in self.wpt_data.values():
            wrapper = waypoint_factory(wpt, self.wpt_config)
            if not wrapper:
                continue
            precision = numpy.abs(numpy.log10(self.precision_km / 111.0))
            self.precision_decimal_place = int(numpy.ceil(precision))
            precision_decimal_multiple = int(numpy.ceil(self.precision_km/111.0 * (10**self.precision_decimal_place)))
            for i in range(0, precision_decimal_multiple + 1):
                self._add_long_lat(wrapper, i)
                if i > 0:
                    self._add_long_lat(wrapper, -i)
        print('Optimization table complete')

    def _add_long_lat(self, wrapper, i):
        lat = int(numpy.ceil(wrapper.get_wpt().latitude * (10 ** self.precision_decimal_place)) + i)
        long = int(numpy.ceil(wrapper.get_wpt().longitude * (10 ** self.precision_decimal_place)) + i)
        self.long_wpts[long].add(wrapper)
        self.lat_wpts[lat].add(wrapper)
        self.wpt_keys[wrapper].append((long, lat))

    def _remove_wpt(self, wpt_wrapper: WptWrapper):
        list_long_lat = self.wpt_keys[wpt_wrapper]
        for long, lat in list_long_lat:
            self.long_wpts[long].remove(wpt_wrapper)
            self.lat_wpts[lat].remove(wpt_wrapper)

    def set_active(self, wpt):
        self.active_waypoints.add(wpt)

    def check_igc_log(self, igc_info: IGCInfo):
        long = int(numpy.ceil((10**self.precision_decimal_place)
                              * igc_info.longitude))
        near_wpts_long = set()
        if long in self.long_wpts:
            near_wpts_long = self.long_wpts[long]

        lat = int(numpy.ceil((10**self.precision_decimal_place) * igc_info.latitude))
        near_wpts_lat = set()
        if lat in self.lat_wpts:
            near_wpts_lat = self.lat_wpts[lat]

        intersection = near_wpts_lat.intersection(near_wpts_long)
        wpts_assess = intersection.union(self.active_waypoints)
        for wpt in wpts_assess:
            status = wpt.submit(igc_info)
            if status is WptStatus.SUCCESS:
                if wpt in self.active_waypoints:
                    self.active_waypoints.remove(wpt)
                if not wpt.is_finish():
                    self._remove_wpt(wpt)
                else:
                    if wpt.wpt.name in self.wpts_hit:
                        self.wpts_hit.pop(wpt.wpt.name)
                self.wpts_hit[wpt.wpt.name] = ({'wpt_wrapper': wpt, 'igc_info': igc_info})
            elif status is WptStatus.ACTIVE:
                self.active_waypoints.add(wpt)
            elif status is WptStatus.MISSED:
                if wpt in self.active_waypoints:
                    self.active_waypoints.remove(wpt)

    def get_score_report(self) -> dict:
        results = {}
        start_pts = 0
        if 'finish_penalty_pts' in self.wpt_config:
            start_pts = int(self.wpt_config['finish_penalty_pts'])
        total = start_pts
        results['wpt_list'] = []
        results['finish_time'] = None
        wpts_hit = list(self.wpts_hit.values())
        for wpt in wpts_hit:
            total = total + wpt['wpt_wrapper'].wpt.pts
            if wpt['wpt_wrapper'].is_finish():
                if wpt == wpts_hit[-1]:
                    total = total - start_pts
                    results['finish_time'] = wpts_hit[-1]['igc_info'].time.strftime("%m/%d/%Y, %H:%M:%S")
            else:
                if wpt['wpt_wrapper'].wpt.pts != 0:
                    results['wpt_list'].append({'wpt': wpt['wpt_wrapper'].wpt.name,
                                                'time': wpt['igc_info'].time.strftime("%m/%d/%Y, %H:%M:%S")})
        results['total'] = total
        return results
