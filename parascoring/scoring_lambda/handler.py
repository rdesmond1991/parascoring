import json

import boto3 as boto3
import uuid
from parascoring.scoring import scorer as s


def _return_error(status_code, message):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': message
    }


def handler(event, context):
    print('received event:')
    print(event)

    s3_client = boto3.client('s3')
    if 'Competition_id' in event:
        competition_id = event['Competition_id']
    else:
        return _return_error(400, "No Competition_Id Present")
    if 'User_id' in event:
        user_id = event['User_id']
    else:
        return _return_error(400, "No User_id Present")

    key_dir = 'public/' + competition_id + '/' + user_id + '/'
    bucket = 'paraglidescoring73ab5d996742454db198920bf37831691934-dev'
    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Delimiter='/',
        Prefix=key_dir,
    )
    print('response')
    print(response)
    if response['KeyCount'] == 0:
        return _return_error(400, "No uploaded tracks")
    tracks = response['Contents']
    print(response['Contents'])

    # Download all files
    igc_files = []
    for track in tracks:
        key = track['Key']
        tmpkey = key.replace('/', '')
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
        igc_files.append(download_path)
        s3_client.download_file(bucket, key, download_path)

    # Get Competition Waypoints
    wpt_key = 'public/' + competition_id + '/competition.wpt'
    tmpkey = wpt_key.replace('/', '')
    wpt_file_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
    s3_client.download_file(bucket, wpt_key, wpt_file_path)

    # Get Competition Config
    wpt_config = 'public/' + competition_id + '/competition.json'
    tmpkey = wpt_config.replace('/', '')
    wpt_config_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
    s3_client.download_file(bucket, wpt_config, wpt_config_path)
    with open(wpt_config_path) as f:
        wpt_config_dict = json.load(f)
    wpt_dict = s.parse_wpt_file(wpt_file_path)
    score = s.score_igcs(igc_files, wpt_dict, wpt_config_dict)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': score
    }

