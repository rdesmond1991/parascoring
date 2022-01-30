import json
import logging
from contextlib import contextmanager

import boto3 as boto3
import numpy

from parascoring.scoring.IgcUtils import IGCInfo


class SubSampleManager:

    def __init__(self, user_id, competition_id, sample_rate=30):
        self.user_id = user_id
        self.competition_id = competition_id
        self.sample_rate = sample_rate
        self.clear_table()

    def clear_table(self):
        table = boto3.resource('dynamodb').Table('UserTrack')
        table.put_item(
            Item={
                'user_id': self.user_id,
                'competition_id': self.competition_id,
                'tracklogs': []
            }
        )

    @contextmanager
    def use_sampler(self, file_name):
        current = None
        try:
            current = IgcSubsampler(file_name, self.sample_rate)
            yield current
        finally:
            self.upload_sample(current)

    def upload_sample(self, current):
        table = boto3.resource('dynamodb').Table('UserTrack')
        tracklog_info = {'tracklog': current.get_file_name(), 'samples': current.get_samples()}
        result = table.update_item(
            Key={
                'user_id': self.user_id,
                'competition_id': self.competition_id
            },
            UpdateExpression="SET tracklogs = list_append(tracklogs, :i)",
            ExpressionAttributeValues={
                ':i': [json.dumps(tracklog_info)],
            },
            ReturnValues="UPDATED_NEW"
        )


class IgcSubsampler:

    def __init__(self, file_name, sample_rate=5):
        # Throw error if sample rate 0 or less
        self.sample_rate = sample_rate
        self.counter = 0
        self.file_name = file_name
        self.samples = []

    def get_samples(self):
        return self.samples

    def get_file_name(self):
        return self.file_name

    def sample_igc_log(self, igc_info: IGCInfo):
        if not self.counter % self.sample_rate:
            long = numpy.round(igc_info.longitude, 3)
            lat = numpy.round(igc_info.latitude, 3)
            self.samples.append((long, lat))
            self.counter = 0
        self.counter += 1


