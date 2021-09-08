import github
import json
import boto3
import os
import logging

from dynamodb_encryption_sdk.encrypted.table import EncryptedTable
from dynamodb_encryption_sdk.material_providers.aws_kms import AwsKmsCryptographicMaterialsProvider
from dynamodb_encryption_sdk.identifiers import CryptoAction
from dynamodb_encryption_sdk.structures import AttributeActions
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    new_analytics = {}
    for record in event["Records"]:
        try:
            repo = json.loads(record['body'])['repo']
            new_analytics[repo] = collect(repo)
        except Exception as e:
            print(e)
            raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "new_analytics": new_analytics
        }),
    }


def collect(repo):
    key = repo
    owner = repo.split('/', 1)[0]
    repo = repo.split('/', 1)[1]
    gh = github.GitHub(access_token=get_token(key))
    validate_repo(gh, owner, repo)

    views_14_days = gh.repos(owner, repo).traffic.views.get()
    clones_14_days = gh.repos(owner, repo).traffic.clones.get()
    logger.info("views github api {}".format(json.dumps(views_14_days)))
    logger.info("clones github api {}".format(json.dumps(clones_14_days)))
    data = merge_clone_and_views_traffic(clones_14_days, views_14_days)
    return load_traffic_in_dynamodb(key, owner, data)


def load_traffic_in_dynamodb(key, owner, new_traffic_data):
    db = load_db()
    found_new_data = False
    for timestamp in new_traffic_data:
        db_item = db.get_item(Key={'repo': key, 'timestamp': timestamp})
        if 'Item' not in db_item:
            db.put_item(
                Item={
                    'repo': key,
                    'timestamp': timestamp,
                    'owner': owner,
                    'traffic': new_traffic_data[timestamp]
                }
            )
            print('added entry for time: {} with traffic: {}'.format(timestamp, json.dumps(new_traffic_data[timestamp])))
            found_new_data = True
        else:
            existing_traffic = db_item['Item']['traffic']
            if existing_traffic['view_uniques'] < new_traffic_data[timestamp]['view_uniques'] \
                    or existing_traffic['clone_uniques'] < new_traffic_data[timestamp]['clone_uniques']:
                db.update_item(
                    Key={
                        'repo': key,
                        'timestamp': timestamp,
                    },
                    UpdateExpression="set traffic=:r",
                    ExpressionAttributeValues={
                        ':r': new_traffic_data[timestamp]
                    },
                    ReturnValues="UPDATED_NEW"
                )
                print('updated entry for time: {} with old traffic: {} to new traffic {}'
                      .format(timestamp, existing_traffic, new_traffic_data[timestamp]))
                found_new_data = True
    return found_new_data


def repo_key(org, repo):
    return '{}/{}'.format(org, repo)


def get_token(item_key):
    try:
        encrypted_table = EncryptedTable(
            table=dynamodb.Table(os.environ.get('TOKEN_TABLE')),
            materials_provider=AwsKmsCryptographicMaterialsProvider(key_id=os.environ.get('KMS_KEY')),
            attribute_actions=AttributeActions(
                default_action=CryptoAction.DO_NOTHING,
                attribute_actions={
                    'token': CryptoAction.ENCRYPT_AND_SIGN
                }
            )
        )
        token = encrypted_table.get_item(Key={'repo': item_key})['Item']['token']
    except ClientError as e:
        raise e
    else:
        return token


def validate_repo(gh, owner, repo):
    try:
        gh.repos(owner, repo).get()
    except Exception as e:
        print('Username/org "' + owner + '" or repo "' + repo + '" not found in GitHub')
        raise e


def merge_clone_and_views_traffic(clones_14_days, views_14_days):
    data = {}
    for view_per_day in views_14_days['views']:
        timestamp = view_per_day['timestamp']
        data[timestamp] = {
            'view_uniques': view_per_day['uniques'],
            'view_count': view_per_day['count'],
            'clone_uniques': 0,
            'clone_count': 0
        }
    for clone_per_day in clones_14_days['clones']:
        timestamp = clone_per_day['timestamp']
        if timestamp not in data:
            data[timestamp] = {
                'view_uniques': 0,
                'view_count': 0
            }
        data[timestamp]['clone_uniques'] = clone_per_day['uniques']
        data[timestamp]['clone_count'] = clone_per_day['count']
    return data


def load_db():
    return dynamodb.Table(os.environ.get('TRAFFIC_TABLE'))
