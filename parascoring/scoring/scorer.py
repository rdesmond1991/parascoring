import logging
from typing import List

from parascoring.scoring.IgcSubsampler import IgcSubsampler
from parascoring.scoring.IgcUtils import IGCParser, order_igc_files
from parascoring.scoring.WaypointOptimizer import WaypointOptimizer
from parascoring.scoring.WptOriginal import WaypointCounter

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def score_igcs(igc_list: List[str], wpt_file: dict, wpt_config: dict):
    return _score_igcs(igc_list, WaypointCounter(wpt_file, wpt_config))


def score_igcs_optimized(igc_list: List[str], wpt_file: dict, wpt_config: dict, sub_sample_manager=None):
    return _score_igcs(igc_list, WaypointOptimizer(wpt_file, wpt_config), sub_sample_manager)


def _score_igcs(igc_list: List[str], wpt_counter, sub_sample_manager=None):
    igc_list = order_igc_files(igc_list)
    for file in igc_list:
        logger.info('Using file: ' + file)
        if sub_sample_manager:
            with sub_sample_manager.use_sampler(file) as sub_sampler:
                score_igc(file, wpt_counter, sub_sampler)
        else:
            score_igc(file, wpt_counter, sub_sampler)
    return wpt_counter.get_score_report()


def score_igc(igc: str, wpt_counter, sub_sampler=None):
    """
    Take an igc file, a wpt file, and wpt, definitions and receive a score report

    :param igc:
    :param wpt_counter
    :param sub_sampler
    :return:
    """
    with open(igc, "r") as f:
        _score_igc(f, wpt_counter, sub_sampler)


def _score_igc(igc, wpt_counter, sub_sampler=None):
    igc_parser = IGCParser()
    for x in igc:
        igc_info = igc_parser.parse_igc_line(x)
        if not igc_info:
            continue
        wpt_counter.check_igc_log(igc_info)
        if sub_sampler:
            sub_sampler.sample_igc_log(igc_info)

