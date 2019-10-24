#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Amazon Software License (the "License"). You may not   #
#  use this file except in compliance with the License. A copy of the        #
#  License is located at                                                     #
#                                                                            #
#      http://aws.amazon.com/asl/                                            #
#                                                                            #
#  or in the "license" file accompanying this file. This file is distributed #
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,        #
#  express or implied. See the License for the specific language governing   #
#  permissions and limitations under the License.                            #
##############################################################################

import logging
import traceback
import datetime
import boto3
import json
import os
import urllib.request, urllib.error, urllib.parse

send_anonymous_data = str(os.environ.get('SEND_ANONYMOUS_DATA')).upper()

def lambda_handler(event, context):
    try:
        global log_level
        log_level = str(os.environ.get('LOG_LEVEL')).upper()
        if log_level not in [
                                'DEBUG', 'INFO',
                                'WARNING', 'ERROR',
                                'CRITICAL'
                            ]:
            log_level = 'ERROR'
        logging.getLogger().setLevel(log_level)

        client = boto3.client('iot-data', region_name=os.environ['AWS_REGION'])
        cw_client = boto3.client('logs', region_name=os.environ['AWS_REGION'])
        logging.debug("Received Lambda event:", event)

        response = client.publish(
            topic=os.environ['IOT_TOPIC'],
            qos=1,
            payload=json.dumps({"PinpointMessage":event['Message']['smsmessage']['body']}))

        logging.debug("Received response from IoT client: ", response)


        if send_anonymous_data == "YES":
            try:
                sendAnonymousData()
            except Exception as error:
                logging.error('send_anonymous_data error: %s', error)
        else:
            logging.info('Anonymous usage metrics collection disabled.')

        result = {
            'statusCode': '200',
            'body':  {'message': 'success'}
        }
        return json.dumps(result)
    except Exception as error:
        logging.error('lambda_handler error: %s' % (error))
        logging.error('lambda_handler trace: %s' % traceback.format_exc())
        result = {
            'statusCode': '500',
            'body':  {'message': 'error'}
        }
        return json.dumps(result)


# This function sends anonymous usage data, if enabled
def sendAnonymousData():
    logging.debug("Sending Anonymous Data")
    metric_data = {}
    metric_data['MessagesSent'] = 1
    postDict = {}
    postDict['TimeStamp'] = str(datetime.datetime.utcnow().isoformat())
    postDict['Data'] = metric_data
    postDict['Solution'] = os.environ.get('SOLUTION_ID')
    postDict['UUID'] = os.environ.get('SOLUTION_UUID')
    # API Gateway URL to make HTTP POST call
    url = 'https://metrics.awssolutionsbuilder.com/generic'
    data=json.dumps(postDict)
    data_utf8 = data.encode('utf-8')
    logging.debug('sendAnonymousData data: %s', data)
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'content-length': len(data_utf8)
    }
    req = urllib.request.Request(url, data_utf8, headers)
    rsp = urllib.request.urlopen(req)
    rspcode = rsp.getcode()
    content = rsp.read()
    logging.debug("Response from APIGateway: %s, %s", rspcode, content)
