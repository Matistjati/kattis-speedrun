from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import LoginManager, login_required, current_user

from backend.models import db, User, SubmissionQueue
from backend.scraping.get_difficulty import get_difficulty

submit = Blueprint('submit', __name__, template_folder='../../frontend/templates')
login_manager = LoginManager()
login_manager.init_app(submit)

@submit.route('/submit', methods=['GET', 'POST'])
@login_required
def show():
    if request.method == 'POST':
        shortname = request.form.get('shortname')
        language = request.form.get('language')
        code = request.form.get('code')

        if not shortname or not code or not language:
            flash('Shortname, language, and code are required.', 'error')
            return redirect(url_for('submit.show'))

        difficulty = get_difficulty(shortname)
        if difficulty is None:
            flash('Invalid problem shortname.', 'error')
            return redirect(url_for('submit.show'))

        submission = SubmissionQueue().add_submission(
            problem_shortname=shortname,
            language=language,
            source_code=code,
            user_id=current_user.id,
            problem_difficulty=difficulty
        )

        flash('Submission successful!', 'success')
        return redirect(url_for('submit.show'))

    return render_template('submit.html')
