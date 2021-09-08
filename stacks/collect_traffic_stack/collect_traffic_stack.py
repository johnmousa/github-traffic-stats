from aws_cdk import core as cdk

from aws_cdk import (
    aws_lambda as _lambda,
    aws_lambda_event_sources as _event_sources,
    aws_kms as _kms,
    aws_dynamodb as _dynamodb,
    aws_sqs as _sqs,
    core as cdk
)


class CollectTrafficStack(cdk.Stack):
    def __init__(
            self, scope: cdk.Construct, construct_id: str,
            token_key: _kms.Key, token_table: _dynamodb.Table,
            collection_queue: _sqs.Queue, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create dynamo table
        traffic_table = _dynamodb.Table(
            self, "github_traffic_table",
            table_name="github_traffic_table",
            partition_key=_dynamodb.Attribute(
                name="repo",
                type=_dynamodb.AttributeType.STRING
            ),
            sort_key=_dynamodb.Attribute(
                name="timestamp",
                type=_dynamodb.AttributeType.STRING
            ),
        )

        collect_traffic_lambda = _lambda.Function(
            scope=self,
            id="collect-traffic-lambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            function_name="collect-traffic-lambda-function",
            description="Lambda function to collect github traffic for a given repo",
            code=_lambda.Code.from_asset("collect_traffic_stack/collect_traffic_lambda"),
            handler="app.lambda_handler",
            events=[_event_sources.SqsEventSource(collection_queue)],
            timeout=cdk.Duration.minutes(5)
        )

        collect_traffic_lambda.add_environment("KMS_KEY", token_key.key_id)
        collect_traffic_lambda.add_environment("TRAFFIC_TABLE", traffic_table.table_name)
        collect_traffic_lambda.add_environment("TOKEN_TABLE", token_table.table_name)
        traffic_table.grant_read_write_data(collect_traffic_lambda)
        token_key.grant_decrypt(collect_traffic_lambda)
        token_table.grant_read_data(collect_traffic_lambda)
        token_table.grant(collect_traffic_lambda, "dynamodb:DescribeTable")
        collection_queue.grant_consume_messages(collect_traffic_lambda)

