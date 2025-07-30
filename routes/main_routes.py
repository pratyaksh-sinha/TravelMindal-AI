from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user

def index():
    """Render the home page."""
    return render_template('index.html')
