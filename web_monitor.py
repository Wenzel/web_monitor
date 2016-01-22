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

import docopt
import requests
import yaml
import flask

LOG_LEVEL = logging.INFO
LOG_FILE = "./web_monitor.log"
VERSION = 0.1
CONFIG_PATH = "./web_monitor.yaml"

last_check = None
app = flask.Flask(__name__)
mutex = threading.Lock()


@app.route('/')
def show_last_check():
    global last_check
    mutex.acquire()
    # make copy of last_check
    check = copy.deepcopy(last_check)
    mutex.release()
    return flask.render_template('show_last_check.html', check=check)

class Site(threading.Thread):

    TIMEOUT = 30

    def __init__(self, id, config_site):
        super().__init__()
        self.id = id
        self.url = config_site['url']
        self.content = config_site['content']
        self.full_match = config_site['full_match']
        self.status = {}
        self.status['config_site'] = config_site

    def run(self):
        # assume it's up
        self.status['up'] = True
        self.status['error'] = None
        self.status['code'] = None
        self.status['elapsed'] = None
        try:
            start = datetime.datetime.now()
            r = requests.get(self.url, timeout=Site.TIMEOUT)
            # force to download all content
            r.content
            end = datetime.datetime.now()
            self.status['code'] = r.status_code
            self.status['elapsed'] = end - start
            match_func = None
            if self.full_match:
                match_func = re.match
            else:
                match_func = re.search
            if match_func(r'{}'.format(self.content), r.text):
                self.status['match'] = True
            else:
                self.status['match'] = False
        except requests.exceptions.RequestException as e:
            exception = e.__class__.__name__
            self.status['up'] = False
            self.status['error'] = exception



class Monitor(threading.Thread):

    def __init__(self, config):
        super().__init__()
        self.interval = config['interval']
        self.sites = config['sites']

    def run(self):
        global last_check
        while True:
            check = {}
            # get current datetime
            check['date'] = datetime.datetime.now()
            # create new thread objects
            sites = [Site(id, config_site) for (id, config_site) in self.sites.items()]
            # start thread
            [s.start() for s in sites]
            # wait for requests
            [s.join() for s in sites]
            # get status
            check['sites'] = [s.status for s in sites]
            # write new entry into log file
            logging.info(pprint.pformat(check))
            # update last check
            mutex.acquire()
            last_check = check
            mutex.release()
            # wait next check
            time.sleep(self.interval)

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

def read_config():
    yaml_content = ""
    with open(CONFIG_PATH, 'r') as f:
        content = f.read()
        yaml_content = yaml.load(content)
    logging.debug(yaml_content)
    return yaml_content

def reconfigure(cmdline):
    config = read_config()
    validate_config(config)
    # overwrite config with cmdline values
    check_interval_cmdline = cmdline['-c']
    if check_interval_cmdline:
        config['check'] = check_interval_cmdline
    # log new config
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
    config = reconfigure(cmdline)
    m = Monitor(config)
    # run Monitor in a new thread
    m.start()
    # run Flask
    return app.run()


if __name__ == '__main__':
    cmdline = docopt.docopt(__doc__, version=VERSION)
    excode = main(cmdline)
    sys.exit(excode)
