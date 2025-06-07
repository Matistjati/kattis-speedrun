from flask import Blueprint, url_for, render_template, redirect, request, flash
from flask_login import LoginManager, login_user, login_required, current_user
from werkzeug.security import check_password_hash

from backend.models import db, User

discord = Blueprint('discord', __name__, template_folder='../../frontend/templates')

@discord.route('/discord', methods=['GET', 'POST'])
@login_required
def show():
    if request.method == 'POST':
        discord_id = request.form['discord_id']

        current_user.discord_id = discord_id
        db.session.commit()

        flash(f"Set id to {discord_id}", "success")
        return render_template('discord.html')
    else:
        return render_template('discord.html')
