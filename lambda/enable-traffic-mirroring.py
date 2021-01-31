# MIT License

# Copyright (c) 2020-2021 Chris Farris (https://www.chrisfarris.com)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import boto3
from botocore.exceptions import ClientError
import json
import os

import logging
logger = logging.getLogger()
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', default='INFO')))
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

TAG_KEY=os.getenv('TAG_KEY', default='WireShark')

def handler(event, context):
    logger.debug("Received event: " + json.dumps(event, sort_keys=True))

    ec2_client = boto3.client('ec2')

    mirror_sessions = ec2_client.describe_traffic_mirror_sessions()['TrafficMirrorSessions']
    enabled_enis = []
    max_session_id = 0
    for s in mirror_sessions:
        enabled_enis.append(s['NetworkInterfaceId'])
        if s['SessionNumber'] > max_session_id:
            max_session_id = s['SessionNumber']

    response = ec2_client.describe_instances(
        Filters=[
            {'Name': 'instance-state-name', 'Values': ['running']},
        ],
        MaxResults=1000  # I should never need to paginate.
    )

    for r in response['Reservations']:
        for i in r['Instances']:
            if not i['InstanceType'].startswith("t3"):
                logger.debug(f"Instance {i['InstanceId']} is not a t3 and does not support Traffic Mirroring")
                continue

            for tag in i['Tags']:
                if tag['Key'] == TAG_KEY:
                    # See if a mirror session is setup
                    for eni in i['NetworkInterfaces']:
                        if eni['NetworkInterfaceId'] not in enabled_enis:
                            logger.info(f"ENI {eni['NetworkInterfaceId']} on Instance {i['InstanceId']} needs Mirroring Enabled")
                            max_session_id += 1
                            enable_traffic_mirroring(ec2_client, eni['NetworkInterfaceId'], i['InstanceId'], max_session_id)
                        else:
                            logger.debug(f"ENI {eni['NetworkInterfaceId']} on Instance {i['InstanceId']} is already Enabled")

def enable_traffic_mirroring(ec2_client, eni, instance_id, session_id):

    response = ec2_client.create_traffic_mirror_session(
        NetworkInterfaceId=eni,
        TrafficMirrorTargetId=os.environ['TARGET_ID'],
        TrafficMirrorFilterId=os.environ['FILTER_ID'],
        SessionNumber=session_id,
        Description=f"Enabled by Lambda for {instance_id}"
    )

## END OF FUNCTION ##


if __name__ == '__main__':


    # Logging idea stolen from: https://docs.python.org/3/howto/logging.html#configuring-logging
    # create console handler and set level to debug
    ch = logging.StreamHandler()

    logger.setLevel(logging.DEBUG)

    # create formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    try:
        handler(None, None)
    except KeyboardInterrupt:
        exit(1)
