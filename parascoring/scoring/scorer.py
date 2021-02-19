import re
from dataclasses import dataclass
from enum import Enum
from typing import List

import numpy
from datetime import datetime, timedelta


class WptType(Enum):
    LAND = 1
    CAMP = 2
    TOUCH = 3
    NONE = 4


@dataclass
class WptDefinition:
    name: str
    longitude: float
    latitude: float
    msl: int
    wpt_type: WptType
    pts: int


@dataclass
class IGCInfo:
    """
    <time> <lat> <long> <alt>
    e.g. B,110135,5206343N,00006198W,A,00587,00558
    B: record type is a basic tracklog record
    110135: <time> tracklog entry was recorded at 11:01:35 i.e. just after 11am
    5206343N: <lat> i.e. 52 degrees 06.343 minutes North
    00006198W: <long> i.e. 000 degrees 06.198 minutes West
    A: <alt valid flag> confirming this record has a valid altitude value
    00587: <altitude from pressure sensor>
    00558: <altitude from GPS>
    """
    time: datetime
    longitude: float
    latitude: float
    alt_pressure: int
    alt_gps: int
    valid: bool


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
            results['wpt_list'].append({'wpt': wpt['wpt'].name, 'time': wpt['igc_info'].time})
        results['total'] = total
        return results


DATE_PATTERN = re.compile("([0-9]{2})([0-9]{2})([0-9]{2})")
BASIC_IGC_LINE = re.compile("^B([0-9]{2})([0-9]{2})([0-9]{2})(.{8})(.{9})([AV])([0-9]{5})([0-9]{5})")
LAT_RE = re.compile("([0-9]{3})([0-9]{2})([0-9]{3})([A-Z])")
LONG_RE = re.compile("([0-9]{2})([0-9]{2})([0-9]{3})([A-Z])")


class IGCParser:

    def __init__(self):
        self._date = None
        self._start_datetime = None
        pass

    def parse_igc_line(self, line: str):
        line = line.strip('\n')
        if not line:
            return None
        if line.startswith('HFDTE'):
            day, month, year = DATE_PATTERN.search(line).groups()
            self._date = datetime(year=2000+int(year), month=int(month), day=int(day))
            return None
        igc_line = parse_igc_basic_line(line, self._date)
        if self._start_datetime is None and igc_line is not None:
            self._start_datetime = igc_line.time
        return igc_line


class IGCFileParser(IGCParser):

    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name

    def get_datetime(self):
        if self._start_datetime:
            return self._start_datetime

        with open(self.file_name, "r") as f:
            for line in f:
                self.parse_igc_line(line)
                if self._start_datetime:
                    break
        return self._start_datetime


def parse_igc_basic_line(line: str, date: datetime):
    if not line or not line.startswith('B'):
        return None
    m = BASIC_IGC_LINE.search(line)
    try:
        time_hours, time_min, time_sec, lon, lat, valid, alt_pressure, alt_gps = m.groups()
    except AttributeError:
        print(line)
        return None

    lat_groups = LAT_RE.match(lat)
    lat_decimal = deg_to_dec(lat_groups[4], int(lat_groups[1]),
                              float(lat_groups[2] + '.' + lat_groups[3]), 0)

    long_groups = LONG_RE.match(lon)
    long_decimal = deg_to_dec(long_groups[4], int(long_groups[1]),
                              float(long_groups[2] + '.' + long_groups[3]), 0)
    return IGCInfo(date + timedelta(hours=int(time_hours), minutes=int(time_min), seconds=int(time_sec)),
                   long_decimal, lat_decimal, int(alt_pressure), int(alt_gps), valid == 'A')


def parse_wpt_file(wpt_file: str):
    wpt_file_data = {}
    with open(wpt_file, "r") as f:
        for x in f:
            line = x.strip('\n')
            if not line or line.startswith('$'):
                continue
            parsed_wpt = line.split('    ')
            lat_msl = parsed_wpt[2].split('  ')
            lat, msl = lat_msl[0:2]
            name_split = parsed_wpt[0].split('_')
            pts = 0
            wpt_type = WptType.TOUCH
            if len(name_split) > 1:
                prefix = name_split[0]
                pts = int(prefix[0])
                if len(prefix) > 1:
                    if prefix[1] == 'X':
                        wpt_type = WptType.LAND
                    if prefix[1] == 'S':
                        wpt_type = WptType.CAMP
            wpt = WptDefinition(parsed_wpt[0].strip(' '), deg_to_dec_wpt(parsed_wpt[1].strip(' ')), deg_to_dec_wpt(lat),
                                int(msl.strip(' ')), wpt_type, pts)
            wpt_file_data[wpt.name] = wpt
    return wpt_file_data


def deg_to_dec_wpt(degrees: str):
    direction, d, m, s = degrees.split(' ')
    return deg_to_dec(direction, int(d), float(m), float(s))


def deg_to_dec(direction: str, degrees, minutes, seconds):
    direction_sign = 1
    if direction == 'S' or direction == 'W':
        direction_sign = -1
    return direction_sign * (degrees + minutes / 60.0 + seconds / 3600)


def deg_wpt_to_deg_igc(degrees: str):
    direction, d, m, s = degrees.split(' ')
    combo = str(int((int(m)+(float(s)/60.0))*10E2))
    return '{}{}{}'.format(str(d), combo, direction)


def dec_to_igc_deg(dec, opt_type: str):
    sign = dec > 0
    if opt_type == 'lon':
        direction_sign = 'N' if sign else 'S'
    if opt_type == 'lat':
        direction_sign = 'E' if sign else 'W'
    else:
        raise Exception('No direction sign')
    dec = numpy.fabs(dec)
    minutes = (dec - int(dec)) * 60
    return str(int((int(dec) + minutes)*10E4)) + direction_sign


def get_distance_from_lat_lon_in_km(lat1, lon1, lat2, lon2):
    radius = 6371  # Radius of the earth in km
    d_lat = deg2rad(lat2-lat1)  # deg2rad below
    d_lon = deg2rad(lon2-lon1)
    a = numpy.sin(d_lat/2) * numpy.sin(d_lat/2) + numpy.cos(deg2rad(lat1)) * numpy.cos(deg2rad(lat2)) \
        * numpy.sin(d_lon/2) * numpy.sin(d_lon/2)
    c = 2 * numpy.arctan2(numpy.sqrt(a), numpy.sqrt(1-a))
    return radius * c  # Distance in km


def deg2rad(deg):
    return deg * (numpy.pi/180)


def order_igc_files(igc_list: List[str]) -> List[str]:
    ordered_igc_files = []
    for file in igc_list:
        igc_parser = IGCFileParser(file)
        inserted = False
        for i in range(len(ordered_igc_files)):
            if igc_parser.get_datetime() < ordered_igc_files[i].get_datetime():
                ordered_igc_files.insert(i, igc_parser)
                inserted = True
                break
        if len(ordered_igc_files) == 0 or not inserted:
            ordered_igc_files.append(igc_parser)
    return [parser.file_name for parser in ordered_igc_files]


def score_igcs(igc_list: List[str], wpt_file: dict, wpt_config: dict):
    igc_list = order_igc_files(igc_list)
    wpt_counter = WaypointCounter(wpt_file, wpt_config)
    for file in igc_list:
        score_igc(file, wpt_counter)
    return wpt_counter.get_score_report()


def score_igc(igc: str, wpt_counter):
    """
    Take an igc file, a wpt file, and wpt, definitions and receive a score report

    :param igc:
    :param wpt_counter
    :return:
    """
    with open(igc, "r") as f:
        _score_igc(f, wpt_counter)


def _score_igc(igc, wpt_counter):
    igc_parser = IGCParser()
    for x in igc:
        igc_info = igc_parser.parse_igc_line(x)
        if not igc_info:
            continue
        wpt_counter.check_igc_log(igc_info)

