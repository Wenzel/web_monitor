import threading
# last status for webmonitor
last_status = None

# lock last_status
mutex = threading.Lock()
