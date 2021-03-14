import json
import os
import boto3 as boto3
import uuid

import parascoring.scoring.Utils
from parascoring.scoring import scorer as s
import logging
from botocore.exceptions import ClientError

from parascoring.scoring.WaypointOptimizer import WaypointOptimizer

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _return_https(status_code, message):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({'message': message})
    }


def get_record_by_user(competition_id, user_id, dynamo=None):
    if not dynamo:
        dynamo = boto3.resource('dynamodb').Table('SampleTable')
    response = dynamo.get_item(Key={"competition_name": competition_id, "person_id": user_id})
    if 'Item' in response:
        return response['Item']
    return None


class ActiveContextManager(object):
    def __init__(self, competition_id, user_id, table):
        self.competition_id = competition_id
        self.user_id = user_id
        self.table = table

    def __enter__(self):
        logger.info('Locking record')
        response = self.table.update_item(
            Key={"competition_name": self.competition_id, "person_id": self.user_id},
            UpdateExpression="set compute_active=:r",
            ExpressionAttributeValues={
                ':r': True
            },
            ReturnValues="UPDATED_NEW"
        )
        logger.info('Locked response')
        logger.info(response)
        return True

    def __exit__(self, type, value, traceback):
        logger.info('Unlocking record')
        response = self.table.update_item(
            Key={"competition_name": self.competition_id, "person_id": self.user_id},
            UpdateExpression="set compute_active=:r",
            ExpressionAttributeValues={
                ':r': False
            },
            ReturnValues="UPDATED_NEW"
        )
        logger.info('Unlocked response')
        logger.info(response)
        return True


class BusinessHandler:
    def __init__(self, event):
        self._event = event
        self.competition_id = None
        self.user_id = None
        self.table = boto3.resource('dynamodb').Table('SampleTable')

    def get_record(self):
        record = get_record_by_user(self.competition_id, self.user_id, self.table)
        if not record:
            record = {
                'competition_name': self.competition_id,
                'person_id': self.user_id,
                'compute_active': False,
                'stats': {
                    'total': 0,
                    'waypoints': [],
                    'finish_time': None,
                    'meta_info': None,
                    'tracklogs': [],
                }
            }
            response = self.table.put_item(
                Item=record
            )
        return record

    def validate_event_handler(self, event):
        if 'compid' in event['pathParameters']:
            self.competition_id = event['pathParameters']['compid']
        else:
            return _return_https(400, "No Competition_Id Present")
        if 'userid' in event['queryStringParameters']:
            self.user_id = event['queryStringParameters']['userid']
        else:
            return _return_https(400, "No User_id Present")
        return None

    @staticmethod
    def _has_tracks_changed(record, tracklogs) -> bool:
        s = set([item['Key'] for item in tracklogs])
        if len(record['stats']['tracklogs']) != len(s):
            return True
        for item in record['stats']['tracklogs']:
            if item['Key'] not in s:
                return True
        return False

    def handle_event(self):
        invalid = self.validate_event_handler(self._event)
        if invalid:
            return invalid
        record = self.get_record()
        if record['compute_active']:
            return _return_https(200, "Still computing score")
        # Use with here
        with ActiveContextManager(self.competition_id, self.user_id, self.table) as c:
            s3_client = boto3.client('s3')
            key_dir = 'public/' + self.competition_id + '/' + self.user_id + '/'
            bucket = os.environ['STORAGE_S34FF28839_BUCKETNAME']
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Delimiter='/',
                Prefix=key_dir,
            )
            logger.info('response')
            logger.info(response)
            if response['KeyCount'] == 0:
                return _return_https(400, "No uploaded tracks")
            tracks = response['Contents']
            logger.info(response['Contents'])
            isChanged = self._has_tracks_changed(record, tracks)

            # Download all files
            igc_files = []
            for track in tracks:
                key = track['Key']
                tmpkey = key.replace('/', '')
                download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
                igc_files.append(download_path)
                s3_client.download_file(bucket, key, download_path)
            logger.info('Using tracks' + str([track['Key'] for track in tracks]))
            # Get Competition Waypoints
            wpt_key = 'public/' + self.competition_id + '/competition.wpt'
            tmpkey = wpt_key.replace('/', '')
            wpt_file_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
            s3_client.download_file(bucket, wpt_key, wpt_file_path)

            # Get Competition Config
            wpt_config = 'public/' + self.competition_id + '/competition.json'
            tmpkey = wpt_config.replace('/', '')
            wpt_config_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
            s3_client.download_file(bucket, wpt_config, wpt_config_path)
            with open(wpt_config_path) as f:
                wpt_config_dict = json.load(f)
            wpt_dict = parascoring.scoring.Utils.parse_wpt_file(wpt_file_path)
            logger.info('Waypoint file parsed')
            score = s.score_igcs_optimized(igc_files, wpt_dict, wpt_config_dict)
            meta = {}
            if 'night_checkpoint' in self._event['queryStringParameters']:
                meta = {'night_checkpoint': self._event['queryStringParameters']['night_checkpoint'] == 'true'}
            if 'night_checkpoint' in meta and meta['night_checkpoint']:
                score['total'] = score['total'] + 5
            score['tracklogs'] = [{'Key': track['Key']} for track in tracks]
            if not self.update_stat_record(score, meta):
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Headers': '*',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': {'message': 'Unable to update stat'}
                }
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': {'message': 'Success', 'record': json.dumps(score)}
            }

    def update_stat_record(self, score, meta):
        logger.info('Updating stat record')
        try:
            response = self.table.update_item(
                Key={"competition_name": self.competition_id, "person_id": self.user_id},
                UpdateExpression=
                "set stats.score=:t, stats.tracklogs=:r, stats.waypoints=:w, stats.finish_time=:f, stats.meta_info=:i",
                ExpressionAttributeValues={
                    ':t': score['total'],
                    ':r': score['tracklogs'],
                    ':w': score['wpt_list'],
                    ':f': score['finish_time'],
                    ':i': meta
                },
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            return None
        logger.info(response)
        return response


def handler(event, context):
    """

    :param event:
    :param context:
    :return:
    """
    business_handler = BusinessHandler(event)
    return business_handler.handle_event()



