# web_monitor

# requirements

- `Python 3.4`
- `virtualenv 3`
- `pip`

# setup

    virtualenv-3.4 venv
    source venv/bin/activate
    pip install -r requirements.txt

# run

    ./web_monitor.py

Then go to `http://127.0.0.1:5000/`

# design

## Read a list of web pages and content from a configuration file

The configuration file `web_monitor.yaml` is parsed at application startup.
it contains the following data

    interval: 10
    sites:
        id1:
            url: 'https://www.f-secure.com/'
            content: 'f-secure'
            full_match: false

- `interval` : number of seconds between 2 requests on a website
- `sites`: hash describing the list of websites to be watched
- `id1` : an short identifier for a given website
- `url` : website's url to be tested
- `content` : website's content that should be matched
- `full_match` : boolean which will be used by the regex engine to switch between
    `re.search` (partial match) or `re.match` (full match)

## Periodically make an HTTP request to each site

the class `Monitor` is a dedicated `thread` and has to role to monitor
each website listed in the configuration file and update their status

The period is simply implemted in the `run` method :

    def run(self)
        while True:
            # make requests
            time.sleep(interval_value)

## Verifies that the page content received from the server matches the content requirements

The following code checks that a webpage content received matches the content
given in the configuration file :

        if self.full_match:
            match_func = re.match
        else:
            match_func = re.search
        if match_func(r'{}'.format(self.content), r.text):
            self.status['match'] = True
        else:
            self.status['match'] = False

## Measures the time it took for the web server to complete the whole request

The following is responsible for measuring the time required to received
the HTTP response :

        start = datetime.datetime.now()
        r = requests.get(self.url, timeout=Site.TIMEOUT)
        # force to download all content
        r.content
        end = datetime.datetime.now()
        self.status['code'] = r.status_code
        self.status['elapsed'] = end - start

## Writes a log file that shows the progress of the periodic checks

The log file is handled with the standard python module `logging`.
Here we configure the logger output on both `stdout` and `web_monitor.log` :

    def init_logger():
        logger = logging.getLogger()
        # log on stdout
        logger.addHandler(logging.StreamHandler())
        # log on LOG_FILE
        file_handler = logging.FileHandler(LOG_FILE)
        logger.addHandler(file_handler)
        logger.setLevel(LOG_LEVEL)

And there we log the new website reported status into the log output, using
`pprint` to have a more readable format :

    # write new entry into log file
    logging.info(pprint.pformat(check))

## Implement a single-page HTTP server interface

We used `Flask` to build this web-server, since it's efficient and remains
very simple to understand :

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

Here we can notice that we have to use a `deepcopy` of the last status
global variable to ensure that while we are updating the view, we are not
referencing the variale that might be updated inside the Monitor.
We also use a Mutex to protect the `deepcopy`.

## The checking period must be configurable via a command-line option

The module `docopt` has been used to easily define new command line parameters.
Here the `-c=INTERVAL` swicth is defined :

    """
    Usage:
        web_monitor.py [options]

    options:
        -c=INTERVAL         Change check interval value
        -h --help           Show this screen.
        --version           Show version.
    """

The configuration is then overwrite after it has been read :

    # overwrite config with cmdline values
    check_interval_cmdline = cmdline['-c']
    if check_interval_cmdline:
        config['check'] = check_interval_cmdline

