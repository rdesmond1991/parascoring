from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

import numpy

from parascoring.scoring.Utils import get_distance_from_lat_lon_in_km, WptType, WptDefinition
from parascoring.scoring.IgcUtils import IGCInfo


class WptStatus(Enum):
    MISSED = 1
    SUCCESS = 2
    ACTIVE = 3


class TagWaypoints:
    def __init__(self, wpt_data: dict, wpt_config: dict):
        self._wpt_list = []
        self._wpt_config = wpt_config
        for wpt in wpt_data.values():
            if wpt.wpt_type == WptType.TOUCH:
                self._wpt_list.append(wpt)

    def submit(self, igc_info) -> WptDefinition:
        for wpt in self._wpt_list:
            if self._wpt_config['cylinder_km'] >= \
                    get_distance_from_lat_lon_in_km(igc_info.latitude, igc_info.longitude, wpt.latitude, wpt.longitude):
                self._wpt_list.remove(wpt)
                return wpt
        return None


@dataclass()
class LandActiveWpt:
    start_igc: IGCInfo
    wpt: WptDefinition

    def __init__(self, wpt: WptDefinition):
        self.wpt = wpt
        self.reset()

    def reset(self):
        self.start_igc = None


class LandWaypoints:
    def __init__(self, wpt_data: dict, wpt_config: dict):
        self._wpt_list = []
        self._wpt_config = wpt_config
        for wpt in wpt_data.values():
            if wpt.wpt_type == WptType.LAND:
                self._wpt_list.append(LandActiveWpt(wpt=wpt))

    def submit(self, igc_info) -> WptDefinition:
        wpt_complete = None
        for wpt in self._wpt_list:
            if self._wpt_config['cylinder_km'] >= \
                    get_distance_from_lat_lon_in_km(igc_info.latitude, igc_info.longitude,
                                                    wpt.wpt.latitude, wpt.wpt.longitude):
                # If waypoint is active but was not in bounds and altitude is not constant reset start_time.
                if not wpt.start_igc:
                    wpt.start_igc = igc_info
                    continue
                alt_variance = self._wpt_config['time_altitude_var_meters']
                alt_gps_condition = \
                    numpy.abs(wpt.start_igc.alt_gps - igc_info.alt_gps) <= alt_variance
                distance = get_distance_from_lat_lon_in_km(igc_info.latitude, igc_info.longitude,
                                                           wpt.start_igc.latitude, wpt.start_igc.longitude)
                distance_condition = distance*1000 < self._wpt_config['distance_variance_meters']
                if wpt.start_igc and alt_gps_condition and distance_condition:
                    if (igc_info.time - wpt.start_igc.time) >= timedelta(minutes=self._wpt_config['time_landed_min']):
                        wpt_complete = wpt.wpt
                        self._wpt_list.remove(wpt)
                else:
                    wpt.start_igc = igc_info

            else:
                wpt.reset()
        return wpt_complete


class WaypointCounter:

    def __init__(self, wpt_data: dict, wpt_config: dict):
        self.wpt_data = wpt_data
        self.wpt_config = wpt_config
        self.wpts_hit = []
        self.wpt_trackers = [TagWaypoints(wpt_data, wpt_config), LandWaypoints(wpt_data, wpt_config)]

    def check_igc_log(self, igc_info):
        for tracker in self.wpt_trackers:
            wpt = tracker.submit(igc_info)
            if wpt:
                self.wpts_hit.append({'wpt': wpt, 'igc_info': igc_info})

    def get_score_report(self) -> dict:
        results = {}
        total = 0
        results['wpt_list'] = []
        for wpt in self.wpts_hit:
            total = total + wpt['wpt'].pts
            results['wpt_list'].append({'wpt': wpt['wpt'].name,
                                        'time': wpt['igc_info'].time.strftime("%m/%d/%Y, %H:%M:%S")})
        results['total'] = total
        return results