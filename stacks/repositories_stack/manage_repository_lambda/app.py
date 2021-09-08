import json
import boto3
import os

from dynamodb_encryption_sdk.encrypted.table import EncryptedTable
from dynamodb_encryption_sdk.material_providers.aws_kms import AwsKmsCryptographicMaterialsProvider
from dynamodb_encryption_sdk.identifiers import CryptoAction
from dynamodb_encryption_sdk.structures import AttributeActions

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    try:
        owner = event['owner']
        repo = event['repo']
        token = event['token']
        dynamodb_table = dynamodb.Table(os.environ.get('TABLE_NAME'))
        encrypted_table = EncryptedTable(
            table=dynamodb_table,
            materials_provider=AwsKmsCryptographicMaterialsProvider(key_id=os.environ.get('KMS_KEY')),
            attribute_actions=AttributeActions(
                default_action=CryptoAction.DO_NOTHING,
                attribute_actions={
                    'token': CryptoAction.ENCRYPT_AND_SIGN
                }
            )
        )

        operation = 'PUT' if 'verb' not in event or event['verb'] is None else event['verb']

        if operation == 'PUT':
            create_repository(encrypted_table, owner, repo, token)
        elif operation == 'DELETE':
            remove_repository(dynamodb_table, owner, repo)

    except Exception as e:
        print(e)
        raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "repo": repo_key(owner, repo),
        }),
    }


def create_repository(table, owner, repo, token):
    table.put_item(Item={
        'repo': repo_key(owner, repo),
        'token': token,
    })


def repo_key(owner, repo):
    return '{}/{}'.format(owner, repo)


def remove_repository(table, org, repo):
    table.delete_item(Key={'repo': repo_key(org, repo)})
