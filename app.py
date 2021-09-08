#!/usr/bin/env python3

from aws_cdk import core

from stacks.collect_traffic_stack import CollectTrafficStack
from stacks.common_infrastructure_stack.common_infrastructure_stack import CommonInfrastructureStack
from stacks.repositories_stack import RepositoriesStack

app = core.App()
infrastructure_stack = CommonInfrastructureStack(app, 'git-analytics-common')
repositories_stack = RepositoriesStack(
    app, 'git-analytics-repositories-management', token_key=infrastructure_stack.key,
    collection_queue=infrastructure_stack.queue)
CollectTrafficStack(
    app, 'git-analytics-traffic-analytics',
    token_key=infrastructure_stack.key, token_table=repositories_stack.repositories_table,
    collection_queue=infrastructure_stack.queue)

app.synth()
