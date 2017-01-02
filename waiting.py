#!/usr/bin/env python
import signal
import sys
import argparse
import logging
import os
import requests
import time
import pytz
from dateutil import parser
from datetime import datetime, timedelta

import json
from termcolor import colored

utc = pytz.UTC

# Script config
BASE_URL = 'https://review-api.udacity.com/api/v1'
CERTS_URL = '{}/me/certifications.json'.format(BASE_URL)
ME_URL = '{}/me'.format(BASE_URL)
ME_REQUEST_URL = '{}/me/submission_requests.json'.format(BASE_URL)
CREATE_REQUEST_URL = '{}/submission_requests.json'.format(BASE_URL)
DELETE_URL_TMPL = '{}/submission_requests/{}.json'
GET_REQUEST_URL_TMPL = '{}/submission_requests/{}.json'
PUT_REQUEST_URL_TMPL = '{}/submission_requests/{}.json'
REFRESH_URL_TMPL = '{}/submission_requests/{}/refresh.json'
ASSIGNED_COUNT_URL = '{}/me/submissions/assigned_count.json'.format(BASE_URL)
ASSIGNED_URL = '{}/me/submissions/assigned.json'.format(BASE_URL)

REVIEW_URL = 'https://review.udacity.com/#!/submissions/{sid}'
REQUESTS_PER_SECOND = 1 # Please leave this alone.

WAIT_URL = '{}/submission_requests/{}/waits.json'


# Get a list of contacts
project = {}


logging.basicConfig(format='|%(asctime)s| %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

headers = None

def request_reviews(token):
    global headers
    headers = {'Authorization': token, 'Content-Length': '0'}
    
    me_req_resp = requests.get(ME_REQUEST_URL, headers=headers)
    current_request = me_req_resp.json()[0] if me_req_resp.status_code == 200 and len(me_req_resp.json()) > 0 else None
    
    if current_request is None:
        print("Run the grading assigner first")
        return
    else:
        certs_resp = requests.get(CERTS_URL, headers=headers)
        certs_resp.raise_for_status()
        certs = certs_resp.json()
        
        project_ids = [cert['project']['id'] for cert in certs if cert['status'] == 'certified']
        project_names = [cert['project']['name'] for cert in certs if cert['status'] == 'certified']
        project_prices = [cert['project']['price'] for cert in certs if cert['status'] == 'certified']

        for p in range(0,len(project_ids)):
            project[project_ids[p]] = project_names[p].split(":")[0] + ": $" + project_prices[p]

        
        # print(current_request['id'])
        url = WAIT_URL.format(BASE_URL, current_request['id'])
        get_req_respo = requests.get(url, headers=headers)
        wait_request = get_req_respo.json() if get_req_respo.status_code == 200 and len(get_req_respo.json()) > 0 else None
    
    old_wait_request = wait_request
    
    while True:
        if current_request is None:
            print("Run the grading assigner first")
            return
        else:
            
            current_request = me_req_resp.json()[0] if me_req_resp.status_code == 200 and len(me_req_resp.json()) > 0 else None            
            if current_request is None:
                print("Run the grading assigner first")
                return            
            # print(current_request['id'])
            url = WAIT_URL.format(BASE_URL, current_request['id'])
            get_req_respo = requests.get(url, headers=headers)
            wait_request = get_req_respo.json() if get_req_respo.status_code == 200 and len(get_req_respo.json()) > 0 else None
            os.system('clear')                                         
            for i in range(0,len(wait_request)):
                position = wait_request[i]["position"]
                project_id = wait_request[i]["project_id"]
                
                if (len(old_wait_request) > 0 and (position != old_wait_request[i]["position"])):
                    # print(colored(str(position),attrs = ['bold','blink']) + " : " + colored(project[project_id],attrs=['bold','blink']))
                    print(colored(str(position),attrs = ['bold']) + " : " + colored(project[project_id],attrs=['bold']) + "(" + str(old_wait_request[i]["position"] - position) +")")
                else:
                    print(str(position) + " : " + project[project_id])    
                
            time.sleep(5.0)


if __name__ == "__main__":
    cmd_parser = argparse.ArgumentParser(description =
	"Find where you stand in the queue"
    )
    cmd_parser.add_argument('--auth-token', '-T', dest='token',
	metavar='TOKEN', type=str,
	action='store', default=os.environ.get('UDACITY_AUTH_TOKEN'),
	help="""
	    Your Udacity auth token. To obtain, login to review.udacity.com, open the Javascript console, and copy the output of `JSON.parse(localStorage.currentUser).token`.  This can also be stored in the environment variable UDACITY_AUTH_TOKEN.
	"""
    )
    cmd_parser.add_argument('--debug', '-d', action='store_true', help='Turn on debug statements.')
    args = cmd_parser.parse_args()

    if not args.token:
        cmd_parser.print_help()
        cmd_parser.exit()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    request_reviews(args.token)

