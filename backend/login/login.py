from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import LoginManager, login_user

from backend.models import db, User

login = Blueprint('login', __name__, template_folder='../../frontend/templates')
login_manager = LoginManager()
login_manager.init_app(login)

@login.route('/login', methods=['GET', 'POST'])
def show():
    if request.method == 'POST':
        username = request.form['username']

        if not username:
            flash("Please enter a username", "error")
            return redirect(url_for('login.show'))

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for('submission_queue.show'))
    else:
        return render_template('login.html')
