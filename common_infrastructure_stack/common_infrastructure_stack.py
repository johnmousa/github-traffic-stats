from aws_cdk import core as cdk

from aws_cdk import (
    aws_kms as _kms,
    aws_sqs as _sqs,
    core as cdk
)


class CommonInfrastructureStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.key = _kms.Key(self, "TokenKey")
        self.queue = _sqs.Queue(self, "CollectTrafficQueue")
