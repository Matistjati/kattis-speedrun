from flask import Blueprint, render_template
from flask_login import LoginManager, login_required, current_user

from backend.models import db, User

submission_queue = Blueprint('submission_queue', __name__, template_folder='../../frontend/templates')
login_manager = LoginManager()
login_manager.init_app(submission_queue)

@submission_queue.route('/queue', methods=['GET'])
def show():
    return render_template('queue.html')
