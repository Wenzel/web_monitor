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
it contains the following sample data :

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

The function `monitor` has the role to check that every website
is available and matches the required content, by calling the
`check_website` function.

It imports `multiprocessing` module to use the `ThreadPool` class,
so that we can effiently execute multiple checks in parallel.

The results are printed on the log output, using `pformat` to prettify them.

A `mutex` is used to ensure that when we update the global variable `last_status`,
it won't be read by the Flask view code at the same time.

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
very simple to understand.

Our architecture is splitted into modules :

    app/
        mod_webmonitor/
            controller.py
            [view.py]
            [model.py]
        static/
        templates/
            webmonitor/
                show.html


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

The configuration is then overwritten after it has been read :

    # overwrite config with cmdline values
    check_interval_cmdline = cmdline['-c']
    if check_interval_cmdline:
        config['check'] = check_interval_cmdline

## The log file must contain the checked URLs, their status and the response times

The following format is printed in the log file :

    {'date': datetime.datetime(2016, 1, 22, 2, 7, 7, 953550),
     'sites': [{'code': 200,
                'config_site': {'content': 'f-secure',
                                'full_match': False,
                                'url': 'https://www.f-secure.com/'},
                'elapsed': datetime.timedelta(0, 2, 445137),
                'error': None,
                'match': True,
                'up': True}]}

- `date` : contains the `datetime` just before we began to check websites availability.
- `sites` : contains the status report for each website
- `code` : corresponding HTTP status code
- `config_site` :  a hash describe the website configuration
- `elasped` the delta between the moment where we started the requested, and the moment when we received the full answer
- `error` : an error describing a problem at application level that might have happened during the test (`SSLErrorè, `TimeoutError`, `ConnectionError`, ...)
- `match` : if the content received and the string describing the content in the configuration file have matched
- `up` : if the website has given a response, and therefore is up
