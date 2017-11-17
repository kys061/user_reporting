#!/usr/bin/python2.7
# Copyright (C) 2016 Saisei Networks Inc. All rights reserved.

import logging
import requests
import time
import os
from datetime import timedelta
from argparse import ArgumentParser

################################################################################
REST_PROTO = 'http'
REST_SERVER = 'localhost'
REST_PORT = '5000'
REST_SYS_NAME = os.uname()[1]  # change you hostname
REST_BASIC_PATH = r'/rest/' + REST_SYS_NAME + '/configurations/running/'
REST_USER_PATH = r''
USER = 'admin'
PASS = 'admin'
FILE_PATH = r'/var/log/user_report/'
#FROM_TIME = r'00:00:00'
#UNTIL_TIME = r'23:59:59'

FROM_TIME = r'15:00:00'
UNTIL_TIME = r'14:59:59'
################################################################################
# 0-1000  -> 0-999
# 1000-2000 -> 1000-1999
# 2000-3000 -> 2000-2999
################################################################################

# recorder logger setting
SCRIPT_MON_LOG_FILE = r'/var/log/user_report.log'

logger = logging.getLogger('saisei.user_report')
logger.setLevel(logging.INFO)

handler = logging.FileHandler(SCRIPT_MON_LOG_FILE)
handler.setLevel(logging.INFO)
filter = logging.Filter('saisei.user_report')
formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.addFilter(filter)

logger.addHandler(handler)
logger.addFilter(filter)

ONE_DAY = timedelta(days=1)

class parse_args(object) :

    def __init__(self) :
        self.start = None
        self.end = None
        self.duration = None
        self.period = None
        self.output_file = None
        self.server = None
        self.port = None
        self.user = None
        self.password=None

    def _make_parser(self):
        p = ArgumentParser(usage='[-s|-e] -s is start date, -e is end date, ' + \
                                 'Date can be a like 20170301')
        p.add_argument('-s', '--start', help='eg)start date like 20170301')
        p.add_argument('-e', '--end', help='eg)end date like 20170331')
        self.parser = p

    def parse(self):
        self._make_parser()
        # self.start = sdatetime('now')
        args = self.parser.parse_args()
        self.start = args.start
        self.end = args.end

def to_euckr(msg):
    try:
        # to byte encoding with euc-kr, it means str in python2
        msg_euckr = unicode(msg, 'utf-8').encode('euc-kr')
        # byte str that is encoded change to unicode with euc-kr,
        # it means decode to unicode with euc-kr.
        msg_euckr = unicode(msg_euckr, 'euc-kr')
    except Exception as e:
        logger.error('error in to_euckr : {}'.format(e))
    else:
        return msg_euckr


def whatisthis(s):
    if isinstance(s, str):
        print ("ordinary string")
    elif isinstance(s, unicode):
        print ("unicode string")
    else:
        print ("not a string")


def to_unicode(s):
    if isinstance(s, str):
        value = s.decode('euc-kr')
    else:
        value = s
    return value


def to_str(s):
    if isinstance(s, unicode):
        value = s.encode('euc-kr')
    else:
        value = s
    return value


def query(url, user, password):
    try:
        resp = requests.get(url, auth=(user, password))
    except Exception as err:
        resp = None
        logger.error("### Got exception from requsts.get : {} ###".format(err))
        time.sleep(1)

    if resp:
        data = resp.json()
        if data['collection'] == []:
            return data['collection']
        else:
            data['collection'][0]['status'] = 200
            return data['collection']
    else:
        if resp.status_code == 404 or resp.status_code == 400:
            logger.error("### requests.get returned {} status code ###".format(
                str(resp.status_code)))
            data = resp.json()
            return data
        logger.error("### requests.get returned None ###")
        logger.error("### requests.get retry interval 1 second (1st) ###")
        logger.error("### url: '{}' ###".format(url))
        time.sleep(1)
        resp = requests.get(url, auth=(user, password))

        if resp:
            data = resp.json()
            if data['collection'] == []:
                return data['collection']
            else:
                data['collection'][0]['status'] = 200
                return data['collection']
        else:
            if resp.status_code == 404 or resp.status_code == 400:
                logger.error("### requests.get returned {} status code ###".format(
                    str(resp.status_code)))
                data = resp.json()
                return data
            logger.error("### requests.get returned None ###")
            logger.error("### requests.get retry interval 1 second (1st) ###")
            logger.error("### url: '{}' ###".format(url))
            time.sleep(1)
            resp = requests.get(url, auth=(user, password))

            if resp:
                data = resp.json()
                if data['collection'] == []:
                    return data['collection']
                else:
                    data['collection'][0]['status'] = 200
                    return data['collection']
            else:
                if resp.status_code == 404 or resp.status_code == 400:
                    logger.error("### requests.get returned {} status code ###".format(
                        str(resp.status_code)))
                    data = resp.json()
                    return data
                logger.error("### requests.get returned None script exit ###")
                logger.error("### url: '{}' ###".format(url))
                return None

def query_get_all(url, user, password):
    try:
        resp = requests.get(url, auth=(user, password))
    except Exception as err:
        resp = None
        time.sleep(1)
        logger.error("### Got exception from requsts.get : {} ###".format(err))

    if resp:
        data = resp.json()
        return data
    else:
        logger.error("### requests.get returned None ###")
        logger.error("### requests.get first retry interval 1 second (1st) ###")
        logger.error("### url: '{}' ###".format(url))
        time.sleep(1)
        resp = requests.get(url, auth=(user, password))

        if resp:
            data = resp.json()
            return data
        else:
            logger.error("### First requests.get retry returned None ###")
            logger.error("### Second requests.get retry interval 1 second (1st) ###")
            logger.error("### url: '{}' ###".format(url))
            time.sleep(1)
            resp = requests.get(url, auth=(user, password))

            if resp:
                data = resp.json()
                return data
            else:
                logger.error("### Second requests.get retry returned None script exit ###")
                logger.error("### url: '{}' ###".format(url))
                return None

def query_hpm(url, user, password):
    try:
        resp = requests.get(url, auth=(user, password))
    except Exception as err:
        resp = None
        logger.error("### Got exception from requsts.delete : {} ###".format(err))

    if resp:
        data = resp.json()
        if data['collection'] == []:
            return data['collection']
        else:
            data['collection'][0]['status'] = 200
            return data['collection']
    else:
        if resp.status_code == 404:
            return resp.status_code
        logger.error("### requests.delete returned None ###")
        logger.error("### requests.delete retry interval 1 second (1st) ###")
        logger.error("### url: '{}' ###".format(url))
        time.sleep(1)
        resp = requests.get(url, auth=(user, password))

        if resp:
            data = resp.json()
            if data['collection'] == []:
                return data['collection']
            else:
                data['collection'][0]['status'] = 200
                return data['collection']
        else:
            if resp.status_code == 404:
                return resp.status_code
            logger.error("### requests.delete returned None ###")
            logger.error("### requests.delete retry interval 1 second (1st) ###")
            logger.error("### url: '{}' ###".format(url))
            time.sleep(1)
            resp = requests.get(url, auth=(user, password))

            if resp:
                data = resp.json()
                if data['collection'] == []:
                    return data['collection']
                else:
                    data['collection'][0]['status'] = 200
                    return data['collection']
            else:
                if resp.status_code == 404:
                    return resp.status_code
                logger.error("### requests.delete returned None script exit ###")
                logger.error("### url: '{}' ###".format(url))
                return None
