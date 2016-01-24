# Import flask dependencies
from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for
import copy

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_webmonitor = Blueprint('web_monitor', __name__, url_prefix='/webmonitor')

import builtins
print(builtins.mutex)
@mod_webmonitor.route('/', methods=['GET'])
def show():
    builtins.mutex.acquire()
    status = copy.deepcopy(builtins.last_status)
    builtins.mutex.release()
    ret = render_template("webmonitor/show.html", status=status)
    return ret
