from . import AWSPlugin
import boto3
from boto3.exceptions import Boto3Error
import logging
import os
from pulsenotify.util import async_time_me

log = logging.getLogger(__name__)


class Plugin(AWSPlugin):
    """
    Amazon SNS Plugin for the Pulse Notification system

    The following environment variables must be present for the plugin to function:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - SNS_ARN
    """
    def __init__(self):
        super().__init__()
        self.arn = os.environ['SNS_ARN']

    @async_time_me
    async def notify(self, task_data, exchange_config):
        """Perform the notification (ie email relevant addresses)"""
        message = exchange_config['message']
        if task_data.logs() is not None:
            joined_logs = '\n'.join((l['destination_url'] for l in task_data.log_data()))
            message += "\nThere should be some logs at \n{}".format(joined_logs)

        for attempt in range(5):
            try:
                sns = boto3.resource(self.name,
                                     aws_access_key_id=self.access_key_id,
                                     aws_secret_access_key=self.secret_access_key,
                                     region_name='us-west-2')
                topic = sns.Topic(self.arn)

                topic.publish(Subject=exchange_config['subject'], Message=message)
                log.info('Notified with SNS for %r', task_data)
                return
            except Boto3Error as b3e:
                log.exception('Attempt %s: Boto3Error %s', str(attempt), b3e.message)
        else:
            log.exception('Could not notify %s via SNS for %r', self.arn, task_data)
