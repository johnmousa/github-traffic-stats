import json
import boto3
import os
import uuid

dynamodb = boto3.resource('dynamodb')
sqs = boto3.resource('sqs')


def lambda_handler(event, context):
    try:
        events = scan_and_queue_collection_events()
    except Exception as e:
        print(e)
        raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "signaled_for_traffic_collection": events
        }),
    }


def scan_and_queue_collection_events():
    scan_kwargs = {}
    table = dynamodb.Table(os.environ.get('TABLE_NAME'))
    collected_so_far = 0
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        repositories = response.get('Items', [])
        queue_repositories(repositories)
        collected_so_far = collected_so_far + len(repositories)
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None
    return collected_so_far


def queue_repositories(repositories):
    queue = sqs.get_queue_by_name(QueueName=os.environ.get('SQS_QUEUE'))
    queue.send_messages(
        Entries=[
            {
                'Id': repository['repo'].replace('/', '0'),
                'MessageBody': json.dumps(
                    {
                        'repo': repository['repo']
                    }
                )
            }
            for repository in repositories
        ])
