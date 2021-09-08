from aws_cdk import core as cdk

from aws_cdk import (
    aws_lambda as _lambda,
    aws_events as _events,
    aws_events_targets as _events_targets,
    aws_dynamodb as _dynamodb,
    aws_kms as _kms,
    aws_sqs as _sqs,
    core as cdk
)


class RepositoriesStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str,
                 token_key: _kms.Key, collection_queue: _sqs.Queue, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create dynamo table
        self.repositories_table = _dynamodb.Table(
            self, "github_repositories_table",
            table_name="github_repositories_table",
            partition_key=_dynamodb.Attribute(
                name="repo",
                type=_dynamodb.AttributeType.STRING
            )
        )

        manage_repository_lambda = _lambda.Function(
            scope=self,
            id="manage-repository-lambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            function_name="manage-repository-lambda-function",
            description="Lambda function to add a github repository to the configuration",
            code=_lambda.Code.from_asset("repositories_stack/manage_repository_lambda"),
            handler="app.lambda_handler",
            timeout=cdk.Duration.minutes(1)
        )

        manage_repository_lambda.add_environment("TABLE_NAME", self.repositories_table.table_name)
        manage_repository_lambda.add_environment("KMS_KEY", token_key.key_id)
        token_key.grant_encrypt(manage_repository_lambda)
        self.repositories_table.grant_write_data(manage_repository_lambda)
        self.repositories_table.grant(manage_repository_lambda, "dynamodb:DescribeTable")

        scan_repositories_lambda = _lambda.Function(
            scope=self,
            id="scan-repositories-lambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            function_name="scan-repositories-lambda-function",
            description="Lambda function to scan all repositories and inform collection queue",
            code=_lambda.Code.from_asset("repositories_stack/scan_repositories_lambda"),
            handler="app.lambda_handler",
            timeout=cdk.Duration.minutes(5)
        )

        scan_repositories_lambda.add_environment("TABLE_NAME", self.repositories_table.table_name)
        scan_repositories_lambda.add_environment("SQS_QUEUE", collection_queue.queue_name)

        self.repositories_table.grant_read_data(scan_repositories_lambda)
        collection_queue.grant_send_messages(scan_repositories_lambda)

        _events.Rule(
            scope=self,
            id='scan-repositories-for-traffic',
            rule_name='scan-repositories-for-traffic-rule',
            targets=[_events_targets.LambdaFunction(handler=scan_repositories_lambda)],
            schedule=_events.Schedule.rate(cdk.Duration.days(1))
        )
