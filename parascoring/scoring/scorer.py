import logging
from typing import List

from parascoring.scoring.IgcUtils import IGCParser, order_igc_files
from parascoring.scoring.WaypointOptimizer import WaypointOptimizer
from parascoring.scoring.WptOriginal import WaypointCounter

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def score_igcs(igc_list: List[str], wpt_file: dict, wpt_config: dict):
    return _score_igcs(igc_list, WaypointCounter(wpt_file, wpt_config))


def score_igcs_optimized(igc_list: List[str], wpt_file: dict, wpt_config: dict):
    return _score_igcs(igc_list, WaypointOptimizer(wpt_file, wpt_config))


def _score_igcs(igc_list: List[str], wpt_counter):
    igc_list = order_igc_files(igc_list)
    for file in igc_list:
        logger.info('Using file: ' + file)
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

