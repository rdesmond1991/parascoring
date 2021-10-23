from dataclasses import dataclass
from enum import Enum
from geopy.distance import geodesic
import numpy


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
    combo = int((int(m)+(float(s)/60.0))*10E2)
    if direction == 'E' or direction == 'W':
        combo_str = '{:0>5d}'.format(combo)
    else:
        combo_str = '{:0>5d}'.format(combo)
    return '{}{}{}'.format(str(d), combo_str, direction)


def dec_to_igc_deg(dec, opt_type: str):
    sign = dec > 0
    if opt_type == 'lon':
        direction_sign = 'N' if sign else 'S'
    elif opt_type == 'lat':
        direction_sign = 'E' if sign else 'W'
    else:
        raise Exception('No direction sign')
    dec = numpy.fabs(dec)
    minutes = (dec - int(dec)) * 60
    return str(int((int(dec) + minutes)*10E4)) + direction_sign


def get_distance_from_lat_lon_in_km(lon1, lat1, lon2, lat2):
    # TODO: Fix IGC!
    # print('Lat {}, lon {}, lat {}, lon {}'.format(lat1, lon1, lat2, lon2))
    return geodesic((lat1, lon1), (lat2, lon2)).km  # Distance in km


def deg2rad(deg):
    return deg * (numpy.pi/180)


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