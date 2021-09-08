import json
import os
import stacks.collect_traffic_stack.collect_traffic_lambda.app as traffic_keeper

mapping = {
    'pickle-file': 'some-org',
}

os.environ.setdefault('TRAFFIC_TABLE', 'github_traffic_table')

if __name__ == '__main__':
    for file in os.listdir(".."):
        if file.endswith(".db"):
            repo = file.split(".db", 1)[0]
            if repo in mapping:
                print('Working on: ', repo)
                with open(file, encoding='utf-8-sig') as json_file:
                    traffic = json.load(json_file)
                    for timestamp in traffic:
                        traffic[timestamp] = json.loads(traffic[timestamp])

                    traffic_keeper.load_traffic_in_dynamodb(
                        traffic_keeper.repo_key(mapping[repo], repo),
                        mapping[repo],
                        traffic
                    )
            else:
                print('No mapping found for ', repo)
