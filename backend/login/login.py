from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import LoginManager, login_user
from werkzeug.security import check_password_hash

from backend.models import db, User

login = Blueprint('login', __name__, template_folder='../../frontend/templates')
login_manager = LoginManager()
login_manager.init_app(login)

@login.route('/login', methods=['GET', 'POST'])
def show():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user:
            if check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('submission_queue.show'))
            else:
                flash("Incorrect password", "error")
                return redirect(url_for('login.show'))
        else:
            flash("User not found", "error")
            return redirect(url_for('login.show'))
    else:
        return render_template('login.html')
