from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from flask_sqlalchemy import SQLAlchemy

from backend.models import db, User

register = Blueprint('register', __name__, template_folder='../../frontend/templates')
login_manager = LoginManager()
login_manager.init_app(register)

@register.route('/register', methods=['GET', 'POST'])
def show():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if username and password and confirm_password:
            if password == confirm_password:
                hashed_password = generate_password_hash(
                    password, method='pbkdf2:sha512')
                try:
                    new_user = User(
                        username=username,
                        password_hash=hashed_password,
                    )

                    db.session.add(new_user)
                    db.session.commit()
                except Exception as e:
                    print(e)
                    flash("Error creating user: username already exists", "error")
                    return redirect(url_for('register.show'))

                flash("Account created successfully!", "success")
                return redirect(url_for('login.show'))
        else:
            flash("Please fill in all fields", "error")
            return redirect(url_for('register.show'))
    else:
        return render_template('register.html')
