import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from parascoring.scoring.Utils import deg_to_dec


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


DATE_PATTERN = re.compile("([0-9]{2})([0-9]{2})([0-9]{2})")
BASIC_IGC_LINE = re.compile("^B([0-9]{2})([0-9]{2})([0-9]{2})(.{8})(.{9})([AV])([0-9]{5})([0-9]{5})")
LAT_RE = re.compile("([0-9]{3})([0-9]{2})([0-9]{3})([A-Z])")
LONG_RE = re.compile("([0-9]{2})([0-9]{2})([0-9]{3})([A-Z])")

# 'B1103254441910S1697874EA0063100596'
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
