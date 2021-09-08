from aws_cdk import (
    aws_kms as _kms,
    aws_sqs as _sqs,
    core as cdk
)


class CommonInfrastructureStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.key = _kms.Key(self, "token_key")
        self.queue = _sqs.Queue(self, "collect_traffic_queue", queue_name="collect_traffic_queue",
                                visibility_timeout=cdk.Duration.minutes(5))
