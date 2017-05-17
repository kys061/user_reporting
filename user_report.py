#!/usr/bin/python2.7
# Copyright (C) 2016 Saisei Networks Inc. All rights reserved.
import sys
from datetime import timedelta
from datetime import datetime, date
import time
import re
import requests
#
# local auxiliary modules
#
from parse_args import parse_args
from saisei_api import query, query_get_all, query_hpm

try:
    from tqdm import tqdm
except:
    print("tqdm package is not installed. \
          Install with command: \"pip install tqdm\"")
    exit()
try:
    import xlsxwriter
except:
    print("xlsxwriter package is not installed. \
          Install with command: \"pip install xlsxwriter\"")
    exit()
try:
    from xlsxwriter.utility import xl_rowcol_to_cell
except:
    print("xlsxwriter package is not installed. \
          Install with command: \"pip install xlsxwriter\"")
    exit()
try:
    import pandas as pd
except:
    print("pandas package is not installed. \
          Install with command: \"pip install pandas\"")
    exit()

################################################################################
REST_PROTO = 'http'
REST_SERVER = 'localhost'
REST_PORT = '5000'
REST_SYS_NAME = 'stm'  # change you hostname
REST_BASIC_PATH = r'/rest/' + REST_SYS_NAME + '/configurations/running/'
REST_USER_PATH = r''
USER = 'admin'
PASS = 'admin'

#FROM_TIME = r'00:00:00'
#UNTIL_TIME = r'23:59:59'

FROM_TIME = r'15:00:00'
UNTIL_TIME = r'14:59:59'
################################################################################
# 0-1000  -> 0-999
# 1000-2000 -> 1000-1999
# 2000-3000 -> 2000-2999
################################################################################

# pandas v0.14.1
pd.core.format.header_style = None

try:
    args = parse_args()
    args.parse()
except ValueError, exc:
    print(exc)
    sys.exit(1)

today = date.today()
tomorrow = today + timedelta(days=1)
yesterday = today + timedelta(days=-1)
day_before_yesterday = today + timedelta(days=-2)

if args.start:
    if len(args.start) == 8:
        try:
            args_start = datetime.strptime(args.start, "%Y%m%d")
        except ValueError:
            print(r'Wrong data Format, Pleas check date format : (YYYYMMDD)')
            exit(1)
        else:
            args_before_start = args_start + timedelta(days=-1)
            FROM = args_before_start.strftime('%Y%m%d')
    else:
        print(r'Wrong data Format, Pleas check date format : (YYYYMMDD)')
        exit(1)
#    FROM = args.start
else:
    FROM = day_before_yesterday.strftime('%Y%m%d')
#    FROM = yesterday.strftime('%Y%m%d')
if args.end:
    if len(args.end) == 8:
        try:
            args_end = datetime.strptime(args.end, "%Y%m%d")
            delta = args_end - args_start
            if delta.days < 0:
                print(r'end_date can be after start_date!!')
                exit(1)

        except ValueError:
            print(r'Wrong data Format, Pleas check date format : (YYYYMMDD)')
            exit(1)
        else:
            UNTIL = args.end
    else:
        print(r'Wrong data Format, Pleas check date format : (YYYYMMDD)')
        exit(1)
else:
    UNTIL = yesterday.strftime('%Y%m%d')


'''
utc : datetime type data.
'''


def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset


'''
_history : json data from rest api
_select_attr : attribute trying to extract
_chart_type : ['pie', 'line']
_data_type : ['vol', 'rate']
_search_type :
    ['user_by_rate', 'user_by_vol',
    'app_for_user_by_rate', 'app_for_user_by_rate']
_path_type : ['upload', 'download']
_username : only if app for users by rate or volume.
'''


def make_his_df(_history, _select_attr, _chart_type=None, _data_type=None,
                _search_type=None, _path_type=None, _username=None):
    # type: (object, object, object, object, object, object, object) -> object
    _users = []
    _apps = []
    _history_from = []
    _history_until = []
    _history_time = []
    _history_amount = []

    for _his in _history:
        if (_chart_type == 'pie'):
            if (_search_type == 'user_by_rate' or
                    _search_type == 'user_by_vol'):
                _users.append(_his['name'])
                _history_from.append(_his['from'])
                _history_until.append(_his['until'])

            if (_search_type == 'app_for_user_by_rate' or
                    _search_type == 'app_for_user_by_vol'):
                _users.append(_username)
                _apps.append(_his['name'])
                _history_from.append(_his['from'])
                _history_until.append(_his['until'])

        if (_chart_type == 'line'):
            for history in _his[_select_attr]:
                if (datetime.fromtimestamp(
                        history[0] * 0.001).strftime('%Y%m%d') == UNTIL):
                    _users.append(_his['name'])
                    _history_from.append(_his['from'])
                    _history_until.append(_his['until'])
                    _history_time.append(datetime.fromtimestamp(
                        history[0] * 0.001))
                    _history_amount.append(history[1])

        if (_chart_type == 'pie' and _data_type == 'rate'):
            _history_amount.append(str(_his[_select_attr]) + ' kbit/sec')

        if (_chart_type == 'pie' and _data_type == 'vol'):
            _history_amount.append(str(_his[_select_attr]) + ' Byte')

    if (_history_amount == []):
        return list()

    if (_path_type is 'download'):
        if (_chart_type == 'line' and _data_type == 'rate'):
            l_history = list(zip(_users,
                                 _history_from,
                                 _history_until,
                                 _history_time,
                                 _history_amount))
            if (_search_type == 'user_by_rate'):
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'from',
                                                   'until',
                                                   'history_time',
                                                   _select_attr,
                                                   ])
        if (_chart_type == 'line' and _data_type == 'vol'):
            l_history = list(zip(_users,
                                 _history_from,
                                 _history_until,
                                 _history_time,
                                 _history_amount))
            if (_search_type == 'user_by_vol'):
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'from',
                                                   'until',
                                                   'history_time',
                                                   _select_attr,
                                                   ])
        if (_chart_type == 'pie' and _data_type == 'vol'):
            if (_search_type == 'user_by_vol'):
                l_history = list(zip(_users,
                                     _history_from,
                                     _history_until,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'from',
                                                   'until',
                                                   _select_attr,
                                                   ])
            if (_search_type == 'app_for_user_by_vol'):
                l_history = list(zip(_users,
                                     _apps,
                                     _history_from,
                                     _history_until,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'app_name',
                                                   'from',
                                                   'until',
                                                   _select_attr,
                                                   ])

        if (_chart_type == 'pie' and _data_type == 'rate'):
            if (_search_type == 'user_by_rate'):
                l_history = list(zip(_users,
                                     _history_from,
                                     _history_until,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'from',
                                                   'until',
                                                   _select_attr,
                                                   ])
            if (_search_type == 'app_for_user_by_rate'):
                l_history = list(zip(_users,
                                     _apps,
                                     _history_from,
                                     _history_until,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'app_name',
                                                   'from',
                                                   'until',
                                                   _select_attr,
                                                   ])
    elif (_path_type is 'upload'):
        if (_chart_type == 'line' and _data_type == 'rate'):
            if (_search_type == 'user_by_rate'):
                l_history = list(zip(_users,
                                     _history_from,
                                     _history_until,
                                     _history_time,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'from',
                                                   'until',
                                                   'history_time',
                                                   _select_attr,
                                                   ])
        if (_chart_type == 'line' and _data_type == 'vol'):
            if (_search_type == 'user_by_vol'):
                l_history = list(zip(_users,
                                     _history_from,
                                     _history_until,
                                     _history_time,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'from',
                                                   'until',
                                                   'history_time',
                                                   _select_attr
                                                   ])
        if (_chart_type == 'pie' and _data_type == 'vol'):
            if (_search_type == 'user_by_vol'):
                l_history = list(zip(_users,
                                     _history_from,
                                     _history_until,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'from',
                                                   'until',
                                                   _select_attr,
                                                   ])
            if (_search_type == 'app_for_user_by_vol'):
                l_history = list(zip(_users,
                                     _apps,
                                     _history_from,
                                     _history_until,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'app_name',
                                                   'from',
                                                   'until',
                                                   _select_attr,
                                                   ])

        if (_chart_type == 'pie' and _data_type == 'rate'):
            if (_search_type == 'user_by_rate'):
                l_history = list(zip(_users,
                                     _history_from,
                                     _history_until,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'from',
                                                   'until',
                                                   _select_attr,
                                                   ])
            if (_search_type == 'app_for_user_by_rate'):
                l_history = list(zip(_users,
                                     _apps,
                                     _history_from,
                                     _history_until,
                                     _history_amount))
                df_history = pd.DataFrame(data=l_history,
                                          columns=['username',
                                                   'app_name',
                                                   'from',
                                                   'until',
                                                   _select_attr,
                                                   ])
    else:
        pass

    return df_history


'''
_select_att
_from
_until
_class_type : users, geolocations, applications
_path_type : download, upload
_chart_type : pie, line - there is no pie chart for each user, app, geolocation
_plural : True, False : if it is true, users and it is false, user.
_history_type : True, False
operation : positive_derivative is each data at that history time,
            raw is accumulated data at that history time
'''


def get_url(_select_att, _user, _from, _until,
            _class_type=None, _path_type=None, _chart_type=None, _plural=False,
            _history_type=True):
    if (_class_type is 'users'):
        if (_path_type is 'download' and _chart_type is 'pie'):
            rest_url = REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
                REST_BASIC_PATH + r'users/?select=' + _select_att +\
                r'&order=%3C' + _select_att + r'&limit=5&total=post&with=' +\
                _select_att + r'%3E%3D0.01&from=' + FROM_TIME + r'_' + _from +\
                r'&until=' + UNTIL_TIME + r'_' + _until
#            print(rest_url)
            return rest_url
        if (_path_type is 'download' and _chart_type == 'line'):
            if (_plural is True):
                rest_url = REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
                    REST_BASIC_PATH + r'users/?select=' + _select_att +\
                    r'&from=00%3A00%3A00_' + _from + r'&until=14%3A59%3A00_' +\
                    _until + r'&operation=raw&history_points=true' +\
                    r'&token=' + REST_BASIC_PATH + r'users%2F&with=' +\
                    _select_att + r'%3E%3D0.01&limit=5&order=%3C' + _select_att
#                print(rest_url)
                return rest_url
            else:
                rest_url = REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
                    REST_BASIC_PATH + r'users/' + _user + r'?select=' +\
                    _select_att + r'&from=' + FROM_TIME + r'_' + _from +\
                    r'&operation=positive_derivative' +\
                    r'&history_points=true' + r'&token=' + REST_BASIC_PATH +\
                    r'users/' + _user + r'&until=' + UNTIL_TIME + r'_' + _until
                rest_url = REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
                    REST_BASIC_PATH + r'users/' + _user + r'?select=' +\
                    _select_att + r'&from=' + FROM_TIME + r'_' + _from +\
                    r'&until=' + UNTIL_TIME + r'_' + _until +\
                    r'&operation=positive_derivative' + r'&history_points=true'
#                print(rest_url)
                return rest_url

        if (_path_type is 'upload' and _chart_type is 'pie'):
            rest_url = REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
                REST_BASIC_PATH + r'users/?select=' + _select_att +\
                r'&order=%3C' + _select_att + r'&limit=5&total=post&with=' +\
                _select_att + r'%3E%3D0.01&from=' + FROM_TIME + r'_' + _from +\
                r'&until=' + UNTIL_TIME + r'_' + _until
#            print(rest_url)
            return rest_url
        if (_path_type is 'upload' and _chart_type == 'line'):
            if (_plural is True):
                rest_url = REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
                    REST_BASIC_PATH + r'users/?select=' + _select_att +\
                    r'&from=' + FROM_TIME + _from + r'&until=' + UNTIL_TIME +\
                    r'_' + _until + r'&operation=raw&history_points=true' +\
                    r'&token=' + REST_BASIC_PATH + r'users%2F&with=' +\
                    _select_att + r'%3E%3D0.01&limit=5&order=%3C' + _select_att
#                print(rest_url)
                return rest_url
            else:
                rest_url = REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
                    REST_BASIC_PATH + r'users/' + _user + r'?select=' +\
                    _select_att + r'&from=' + FROM_TIME + r'_' + _from +\
                    r'&until=' + UNTIL_TIME + r'_' + _until +\
                    r'&operation=positive_derivative' +\
                    r'&history_points=true' + r'&token=' + REST_BASIC_PATH +\
                    r'users/' + _user

#       User-203.247.208.52?select=dest_byte_count&from=15%3A00%3A00_20170423&operation=positive_derivative&history_points=true&token=%2Frest%2Fstm%2Fconfigurations%2Frunning%2Fusers%2FUser-203.247.208.52&until=14%3A59%3A00_20170424
#                print(rest_url)
                return rest_url


def get_url_by_user(user, _select_att, _from, _until):
    url = REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
        REST_BASIC_PATH + r'users/' + user + r'/applications/?select=' +\
        _select_att + r'&order=%3C' + _select_att +\
        r'&limit=3&total=post&with=' + _select_att + r'%3E%3D0.01&from=' +\
        FROM_TIME + r'_' + _from + '&until=' + UNTIL_TIME + r'_' + _until
#    print(url)
    return url


def get_users_name_url(_start, _limit):
    return REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
        REST_BASIC_PATH + r'users/?token=0&start=' + _start + '&limit=' +\
        _limit + '&select=name'


def get_username(_start=0):
    users = query_get_all(get_users_name_url(str(_start), '500'), USER, PASS)
    # time.sleep(3)
    # if users['collection'] == []:
    #     return
    if users['collection']:
        for username in get_username(_start=_start + 500):
            yield username
        for _user in users['collection']:
            yield _user['name']
    else:
        return

def get_total_user_size(_start=0):
    users = query_get_all(get_users_name_url(str(_start), '10'), USER, PASS)
    return users['size']

def get_host_policy_url(_host):
    return REST_PROTO + '://' + REST_SERVER + ':' + REST_PORT +\
        REST_BASIC_PATH + r'fibs/fib0/hosts/' + _host +\
        r'?select=policy&level=full&format=human'


'''
workbook : pandas excel workbook
writer : pandas excel writer
sheetname : sheetname
sheettitle : sheettitle
merge_col : title columns range trying to widen
merge_range : title columns range trying to merge
img_range : image columns range trying to merge
'''


def make_xl_title(workbook, writer, sheetname=None, sheettitle=None,
                  merge_col=None, merge_range=None, img_range=None):
    worksheet = writer.sheets[sheetname]
    # Increase the cell size of the merged cells to highlight the formatting.
    worksheet.set_column(merge_col, 12)
    worksheet.set_row(1, 30)
    worksheet.set_row(2, 30)
#    white = workbook.add_format({'color': 'white'})
    # Create a format to use in the merged range.
    merge_format = workbook.add_format({
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': 'red',
        'font_color': 'white'})
    worksheet.merge_range(img_range, '')
    worksheet.insert_image(img_range, 'saisei_logo1.png')
    # Merge 3 cells over two rows.
    worksheet.merge_range(merge_range, sheettitle, merge_format)
    # worksheet.write_rich_string('B2', white, sheettitle, merge_format)


def check_http_status(returned):
    if isinstance(returned, requests.models.Response):
        if returned['status'] == 400 or returned['status'] == 404:
            print('http status {} Error : {}'.format(
                returned['status'], returned['message']))
            exit(1)
        elif returned['status'] == 200:
            return True
        else:
            print('http status {} Error : '.format(
                returned['status'], returned['message']))
            exit(1)
    if isinstance(returned, list):
        if returned[0]['status'] == 400 or returned[0]['status'] == 404:
            print('http status {} Error : {}'.format(
                returned[0]['status']))
            exit(1)
        elif returned[0]['status'] == 200:
            return True
        else:
            print('http status {} Error : '.format(
                returned[0]['status']))
            exit(1)



'''
_user : users from get_username container.
'''


def make_his_df_for_user(_user):
    _username = []
    _from = []
    _until = []
    _hpm = []
    _dn_vol = []
    _up_vol = []
    _avg_dn_speed = []
    _avg_up_speed = []
    _max_dn_speed = []
    _max_up_speed = []
    _dn_top1_app = []
    _dn_top2_app = []
    _dn_top3_app = []
    _up_top1_app = []
    _up_top2_app = []
    _up_top3_app = []

    # download volume, rate, top_app_by_rate
    # user_by_vol
    users_download_line_vol_history = query(get_url('dest_byte_count',
                                                    _user,
                                                    FROM,
                                                    UNTIL,
                                                    _class_type='users',
                                                    _path_type='download',
                                                    _chart_type='line',
                                                    _plural=False,
                                                    _history_type=True),
                                            USER,
                                            PASS)
    if (check_http_status(users_download_line_vol_history)):
        if users_download_line_vol_history[0]['_history_dest_byte_count'] == []:
            _dn_vol.append(r'None')
            _max_dn_speed.append(r'None')
            _avg_dn_speed.append(r'None')
        else:
            df_users_download_line_vol_history = make_his_df(
                users_download_line_vol_history,
                '_history_dest_byte_count',
                _chart_type='line',
                _data_type='vol',
                _search_type='user_by_vol',
                _path_type='download'
            )
            if isinstance(df_users_download_line_vol_history, list):
                _dn_vol.append(r'None')
                _avg_dn_speed.append(r'None')
            else:
                _dn_vol.append(str(df_users_download_line_vol_history[
                    '_history_dest_byte_count'].sum()) + ' Byte')
                _avg_dn_speed.append(str(round(df_users_download_line_vol_history[
                        '_history_dest_byte_count'].sum()*8 / (86400*1.0), 3)) + r' bit/sec')

    # user_by_rate
    users_download_line_rate_history = query(get_url('dest_smoothed_rate',
                                                     _user,
                                                     FROM,
                                                     UNTIL,
                                                     _class_type='users',
                                                     _path_type='download',
                                                     _chart_type='line',
                                                     _plural=False,
                                                     _history_type=True),
                                             USER,
                                             PASS)
    if users_download_line_rate_history[0]['_history_dest_smoothed_rate'] == []:
        _max_dn_speed.append(r'None')
    else:
        df_users_download_line_rate_history = make_his_df(
            users_download_line_rate_history,
            '_history_dest_smoothed_rate',
            _chart_type='line',
            _data_type='rate',
            _search_type='user_by_rate',
            _path_type='download')
        if isinstance(df_users_download_line_rate_history, list):
            _max_dn_speed.append(r'None')
        else:
            _max_dn_speed.append(str(df_users_download_line_rate_history[
                '_history_dest_smoothed_rate'].max()) + ' bit/sec')

    # top_app_by_rate
    top_app_for_user_by_download_rate_history = query(get_url_by_user(users_download_line_vol_history[0]['name'],
                                                                      'dest_smoothed_rate',
                                                                      FROM,
                                                                      UNTIL),
                                                      USER,
                                                      PASS)

    if top_app_for_user_by_download_rate_history == []:
        _dn_top1_app.append(r'None')
        _dn_top2_app.append(r'None')
        _dn_top3_app.append(r'None')
    else:
        df_top_app_for_user_by_download_rate_history = make_his_df(
            top_app_for_user_by_download_rate_history,
            'dest_smoothed_rate',
            _chart_type='pie',
            _data_type='rate',
            _search_type='app_for_user_by_rate',
            _path_type='download',
            _username=users_download_line_vol_history[0]['name'])

        if isinstance(df_top_app_for_user_by_download_rate_history, list):
            _dn_top1_app.append(r'None')
            _dn_top2_app.append(r'None')
            _dn_top3_app.append(r'None')
        else:
            if (len(df_top_app_for_user_by_download_rate_history['app_name']) == 0):
                _dn_top1_app.append(r'None')
                _dn_top2_app.append(r'None')
                _dn_top3_app.append(r'None')
            if (len(df_top_app_for_user_by_download_rate_history['app_name']) == 1):
                _dn_top2_app.append(r'None')
                _dn_top3_app.append(r'None')
            if (len(df_top_app_for_user_by_download_rate_history['app_name']) == 2):
                _dn_top3_app.append(r'None')

            for i, top_app in enumerate(
                    df_top_app_for_user_by_download_rate_history['app_name']):
                if i + 1 == 1:
                    if top_app:
                        _dn_top1_app.append(top_app)
                    else:
                        _dn_top1_app.append(r'None')
                elif i + 1 == 2:
                    if top_app:
                        _dn_top2_app.append(top_app)
                    else:
                        _dn_top2_app.append(r'None')
                else:
                    if top_app:
                        _dn_top3_app.append(top_app)
                    else:
                        _dn_top3_app.append(r'None')

    # upload volume, rate, top_app_by_rate
    # user_by_vol
    users_upload_line_vol_history = query(get_url('source_byte_count',
                                                  _user,
                                                  FROM,
                                                  UNTIL,
                                                  _class_type='users',
                                                  _path_type='upload',
                                                  _chart_type='line',
                                                  _plural=False,
                                                  _history_type=True),
                                          USER,
                                          PASS)

    if users_upload_line_vol_history[0]['_history_source_byte_count'] == []:
        _up_vol.append(r'None')
        _avg_up_speed.append(r'None')
    else:
        df_users_upload_line_vol_history = make_his_df(
            users_upload_line_vol_history,
            '_history_source_byte_count',
            _chart_type='line',
            _data_type='vol',
            _search_type='user_by_vol',
            _path_type='upload')

        if isinstance(df_users_upload_line_vol_history, list):
            _up_vol.append(r'None')
            _avg_up_speed.append(r'None')
        else:
            _up_vol.append(str(df_users_upload_line_vol_history[
                '_history_source_byte_count'].sum()) + ' Byte')
            _avg_up_speed.append(str(round(df_users_upload_line_vol_history[
                '_history_source_byte_count'].sum()*8 / (86400*1.0), 3)) +
                r' bit/sec')

    # user_by_rate
    users_upload_line_rate_history = query(get_url('source_smoothed_rate',
                                                   _user,
                                                   FROM,
                                                   UNTIL,
                                                   _class_type='users',
                                                   _path_type='upload',
                                                   _chart_type='line',
                                                   _plural=False,
                                                   _history_type=True),
                                           USER,
                                           PASS)

    if users_upload_line_rate_history[0]['_history_source_smoothed_rate'] == []:
        _max_up_speed.append(r'None')
    else:
        df_users_upload_line_rate_history = make_his_df(
            users_upload_line_rate_history,
            '_history_source_smoothed_rate',
            _chart_type='line',
            _data_type='rate',
            _search_type='user_by_rate',
            _path_type='upload')
        if isinstance(df_users_upload_line_rate_history, list):
            _max_up_speed.append(r'None')
        else:
            _max_up_speed.append(str(df_users_upload_line_rate_history[
                '_history_source_smoothed_rate'].max()) + ' bit/sec')

    # top_app_by_rate
    top_app_for_user_by_upload_rate_history = query(
        get_url_by_user(users_upload_line_vol_history[0]['name'],
                        'source_smoothed_rate',
                        FROM,
                        UNTIL),
        USER, PASS)

    if top_app_for_user_by_upload_rate_history == []:
        _up_top1_app.append(r'None')
        _up_top2_app.append(r'None')
        _up_top3_app.append(r'None')
    else:
        df_top_app_for_user_by_upload_rate_history = make_his_df(
            top_app_for_user_by_upload_rate_history,
            'source_smoothed_rate',
            _chart_type='pie',
            _data_type='rate',
            _search_type='app_for_user_by_rate',
            _path_type='download',
            _username=users_upload_line_vol_history[0]['name'])

        if isinstance(df_top_app_for_user_by_upload_rate_history, list):
            _up_top1_app.append(r'None')
            _up_top2_app.append(r'None')
            _up_top3_app.append(r'None')
        else:
            if len(df_top_app_for_user_by_upload_rate_history['app_name']) == 0:
                _up_top1_app.append(r'None')
                _up_top2_app.append(r'None')
                _up_top3_app.append(r'None')
            if len(df_top_app_for_user_by_upload_rate_history['app_name']) == 1:
                _up_top2_app.append(r'None')
                _up_top3_app.append(r'None')
            if len(df_top_app_for_user_by_upload_rate_history['app_name']) == 2:
                _up_top3_app.append(r'None')

            for i, top_app in enumerate(df_top_app_for_user_by_upload_rate_history['app_name']):
                if i + 1 == 1:
                    if top_app:
                        _up_top1_app.append(top_app)
                    else:
                        _up_top1_app.append(r'None')
                elif i + 1 == 2:
                    if top_app:
                        _up_top2_app.append(top_app)
                    else:
                        _up_top2_app.append(r'None')
                else:
                    if top_app:
                        _up_top3_app.append(top_app)
                    else:
                        _up_top3_app.append(r'None')

    _username.append(_user)
    _from.append(str(utc2local(datetime.strptime(
        users_download_line_vol_history[0]['from'],
        "%Y-%m-%dT%H:%M:%S"))))
    _until.append(str(utc2local(datetime.strptime(
        users_download_line_vol_history[0]['until'],
        "%Y-%m-%dT%H:%M:%S"))))

    m = re.search(r'[0-9]+.[0-9]+.[0-9]+.[0-9]+', _user)
    _host = _user[m.start():m.end()]
    _host_policy = query_hpm(get_host_policy_url(_host), USER, PASS)
    if _host_policy == 404 or _host_policy == 400:
        _hpm.append(r'<none>')
    else:
        if _host_policy[0]['policy']:
            if isinstance(_host_policy[0]['policy'], dict):
                _hpm.append(_host_policy[0]['policy']['link']['name'])
            else:
                _hpm.append(_host_policy[0]['policy'])

    l_new_history = list(zip(_username,
                             _from, _until,
                             _hpm,
                             _dn_vol, _up_vol,
                             _avg_dn_speed, _avg_up_speed,
                             _max_dn_speed, _max_up_speed,
                             _dn_top1_app, _up_top1_app,
                             _dn_top2_app, _up_top2_app,
                             _dn_top3_app, _up_top3_app))
    df_new_history = pd.DataFrame(data=l_new_history,
                                  columns=['username',
                                           'from', 'until',
                                           '_hpm',
                                           '_dn_vol', '_up_vol',
                                           '_avg_dn_speed', '_avg_up_speed',
                                           '_max_dn_speed', '_max_up_speed',
                                           '_dn_top1_app', '_up_top1_app',
                                           '_dn_top2_app', '_up_top2_app',
                                           '_dn_top3_app', '_up_top3_app',
                                           ])
    return df_new_history


def check_gen(_usernames):
    try:
        next(_usernames)
    except StopIteration:
        print("There is no Users, check user is exist!")
    else:
        return True



def main():
    start_time = time.time()
    if args.start or args.end:
        xl_file_name = 'User_report_' + args.start + '_' + args.end + '.xlsx'
    else:
        xl_file_name = 'User_report_' + UNTIL + '_' + UNTIL + '.xlsx'

    writer = pd.ExcelWriter(xl_file_name, engine='xlsxwriter')
    #writer = pd.ExcelWriter('Day_Summary.xlsx', engine='xlsxwriter')
    workbook = writer.book

    us_start_row = 3
    us_start_col = 2

#    attrs = [
#        'dest_byte_count',
#        'source_byte_count',
#        'dest_smoothed_rate',
#        'source_smoothed_rate',
#    ]

    usernames = get_username(_start=0)
    chk_usernames = get_username(_start=0)
#    make_his_df_for_user('User-203.250.130.6')
    if check_gen(chk_usernames):
        try:
            for i, username in tqdm(enumerate(usernames), ascii=True, ncols=80, total=int(get_total_user_size(_start=0)), desc='user_reporting'):
#                if i < 500:
                try:
                    df_user_data = make_his_df_for_user(username)
                except Exception as e:
                    print('make_his_df_for_user : {}, {}'.format(username, e))
#                else:
#                    print("{0} Making {1}'s DF Traffic Data - elapsed time:{2:.3f} #################################".format(str(i+1), username, time.time() - start_for_time))

                try:
                    if i == 0:
                        df_user_data.to_excel(writer,
                                                sheet_name='User Traffic Data',
                                                startrow=us_start_row,
                                                startcol=us_start_col,
                                                index=False,
                                                header=True)
                        us_start_row += 2
                    else:
                        df_user_data.to_excel(writer,
                                                sheet_name='User Traffic Data',
                                                startrow=us_start_row,
                                                startcol=us_start_col,
                                                index=False,
                                                header=False)
                        us_start_row += 1
                except Exception as e:
                    print('error making excel files : {}, {}'.format(
                        username, e))
#                else:
        except KeyboardInterrupt:
            print ("\r\nThe script is terminated by user interrupt!")
            print ("Bye!!")
            exit(1)
        except Exception as e:
            print('error for loop : {}'.format(e))
            exit(1)
        else:
            make_xl_title(workbook,
                        writer,
                        sheetname='User Traffic Data',
                        sheettitle='REPORT - USER TRAFFIC ANALYZE',
                        merge_col=r'F:N',
                        merge_range=r'F1:N2',
                        img_range=r'C1:D2')
            writer.save()
            print('Report is created successfully! - Total Elapsed Time:{0:.3f}'.format(time.time() - start_time))
#                    return
            time.sleep(0.3)
    else:
        make_xl_title(workbook,
                    writer,
                    sheetname='User Traffic Data',
                    sheettitle='REPORT - USER TRAFFIC ANALYZE',
                    merge_col=r'F:N',
                    merge_range=r'F1:N2',
                    img_range=r'C1:D2')
        writer.save()
        print('there is no users! - Total Elapsed Time:{0:.3f}'.format(time.time() - start_time))

if __name__ == '__main__':
    main()
