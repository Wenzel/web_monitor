# Import flask and template operators
from flask import Flask, render_template

# Define the WSGI application object
app = Flask(__name__)

# Configurations
app.config.from_object('config')

# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# welcome
@app.route('/')
def welcome():
    return render_template('welcome.html')

# Import a module / component using its blueprint handler variable (mod_webmonitor)
from app.mod_webmonitor.controller import mod_webmonitor

# Register blueprint(s)
app.register_blueprint(mod_webmonitor)
