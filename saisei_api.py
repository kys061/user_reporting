#!/usr/bin/python2.7
# Copyright (C) 2016 Saisei Networks Inc. All rights reserved.

# import pymysql
import logging
import requests
import time

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
