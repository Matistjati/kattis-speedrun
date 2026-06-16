import csv
import os

from flask import Blueprint, render_template

from backend.models import Submission, Status

shortest_unsolved = Blueprint('shortest_unsolved', __name__, template_folder='../../frontend/templates')

# CSV of every Kattis problem pre-sorted ascending by statement length.
# Columns: rank, shortname, url, length_chars, words, difficulty, name
_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'kattis_problems_by_length.csv')


def _excluded_shortnames():
    """Shortnames to hide: problems already Accepted, plus those with a
    submission still waiting in the queue (unjudged)."""
    rows = (
        Submission.query
        .with_entities(Submission.problem_shortname)
        .filter(
            (Submission.status == Status.ACCEPTED) | (Submission.judged == False)
        )
        .distinct()
        .all()
    )
    return {shortname for (shortname,) in rows}


@shortest_unsolved.route('/shortest-unsolved', methods=['GET'])
def show():
    excluded = _excluded_shortnames()
    problems = []
    with open(_CSV_PATH, newline='', encoding='utf-8') as f:
        # CSV is already sorted ascending by length, so the first 20 unsolved
        # rows are the 20 shortest unsolved problems.
        for row in csv.DictReader(f):
            if row['shortname'] in excluded:
                continue
            problems.append({
                'shortname': row['shortname'],
                'name': row['name'],
                'url': row['url'],
                'length_chars': int(row['length_chars']),
                'difficulty': row['difficulty'],
            })
            if len(problems) >= 20:
                break
    return render_template('shortest_unsolved.html', problems=problems)
