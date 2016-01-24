#!/usr/bin/env python3

"""
Usage:
    web_monitor.py [options]

options:
    -c=INTERVAL         Change check interval value
    -h --help           Show this screen.
    --version           Show version.
"""

# standard library
import sys
import logging
import threading
import re
import time
import datetime
import pprint
import copy

# 3rd party
import docopt
import requests
import yaml
import flask
from apscheduler.schedulers.background import BackgroundScheduler
from multiprocessing.pool import ThreadPool

# define globals
import builtins
builtins.last_status = None
builtins.mutex = threading.Lock()

# local imports
from app import app


LOG_LEVEL = logging.DEBUG
LOG_FILE = "./web_monitor.log"
VERSION = 0.1
CONFIG_PATH = "./web_monitor.yaml"
TIMEOUT = 30

def check_website(config_site):
    # assume it's up
    status = {}
    status['config_site'] = config_site
    status['up'] = True
    status['error'] = None
    status['code'] = None
    status['elapsed'] = None
    try:
        start = datetime.datetime.now()
        r = requests.get(config_site['url'], timeout=TIMEOUT)
        # force to download all content
        r.content
        end = datetime.datetime.now()
        status['code'] = r.status_code
        status['elapsed'] = end - start
        # directly transform into seconds
        status['elapsed'].total_seconds()
        match_func = None
        if config_site['full_match']:
            match_func = re.match
        else:
            match_func = re.search
        if match_func(r'{}'.format(config_site['content']), r.text):
            status['match'] = True
        else:
            status['match'] = False
    except requests.exceptions.RequestException as e:
        exception = e.__class__.__name__
        status['up'] = False
        status['error'] = exception
    return status

def monitor(config):
    logging.debug('monitor')
    status = {}
    status['date'] = datetime.datetime.now()
    pool = ThreadPool(4)
    results = pool.map(check_website, [x[1] for x in config['sites'].items()])
    status['sites'] = results
    # log results
    logging.info(pprint.pformat(results))
    # update last status
    __builtins__.mutex.acquire()
    __builtins__.last_status = status
    __builtins__.mutex.release()

def validate_config(config):
    # interval must be present
    if 'interval' not in config:
        logging.critical('[CONFIG] interval value must be defined')
        sys.exit(1)
    # sites must be present
    if 'sites' not in config:
        logging.critical('[CONFIG] a list of sites to be monitored must be defined')
    # each site must have 3 keys
    # url
    # content
    # full_match
    for id in config['sites']:
        keys = ['url', 'content', 'full_match']
        for k in keys:
            if k not in config['sites'][id]:
                logging.critical('[CONFIG] {} invalid : {} missing'.format(id, k))

def read_config_file(config_file):
    yaml_content = ""
    with open(CONFIG_PATH, 'r') as f:
        content = f.read()
        yaml_content = yaml.load(content)
    return yaml_content

def create_config(cmdline, config_file):
    config = read_config_file(config_file)
    logging.debug("config from file :")
    logging.debug(config)
    validate_config(config)
    # overwrite config with cmdline values
    check_interval_cmdline = cmdline['-c']
    if check_interval_cmdline:
        config['interval'] = int(check_interval_cmdline)
    # log new config
    logging.debug("config after cmdline :")
    logging.debug(config)
    return config

def init_logger():
    logger = logging.getLogger()
    # log on stdout
    logger.addHandler(logging.StreamHandler())
    # log on LOG_FILE
    file_handler = logging.FileHandler(LOG_FILE)
    logger.addHandler(file_handler)
    logger.setLevel(LOG_LEVEL)
    # disable logging output from requests
    logging.getLogger("requests").setLevel(logging.WARNING)

def main(cmdline):
    init_logger()
    logging.debug(cmdline)
    # generate config
    config = create_config(cmdline, CONFIG_PATH)
    # schedule background
    sched = BackgroundScheduler()
    sched.add_job(monitor, 'interval', seconds=config['interval'], args=[config])
    sched.start()
    # run Flask
    return app.run(host='127.0.0.1', port=8080)

if __name__ == '__main__':
    cmdline = docopt.docopt(__doc__, version=VERSION)
    excode = main(cmdline)
    sys.exit(excode)
