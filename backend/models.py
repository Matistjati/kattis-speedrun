from datetime import datetime
from enum import Enum
import threading
import secrets

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class SpeedRun(db.Model):
    __tablename__ = 'speedrun'
    id            = db.Column(db.Integer, primary_key=True)
    time_till_next_submission_token = db.Column(db.Integer, default=60, nullable=False)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(120), unique=True, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        self.token = secrets.token_urlsafe(32)
        return self.token


class Status(Enum):
    WAITING = "Waiting"
    RUNNING = "Running"
    ERROR = "Error"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    JUDGE_ERROR = "Judge Error"
    COMPILE_ERROR = "Compile Error"
    RUN_TIME_ERROR = "Run Time Error"
    MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"
    OUTPUT_LIMIT_EXCEEDED = "Output Limit Exceeded"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    ILLEGAL_FUNCTION = "Illegal Function"
    WRONG_ANSWER = "Wrong Answer"


def get_status_name_from_value(value: str) -> str:
    for status in Status:
        if status.value == value:
            return status.name
    raise ValueError(f"No matching enum member for value: {value}")

class Submission(db.Model):
    __tablename__ = 'submission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    language = db.Column(db.String(32), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    problem_shortname = db.Column(db.String(64), nullable=False)
    submission_id = db.Column(db.Integer)
    message = db.Column(db.String(256))
    problem_difficulty = db.Column(db.Float, nullable=False)
    source_code = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(Status), default=Status.WAITING, nullable=False)
    run_time = db.Column(db.Float)
    score = db.Column(db.Float)
    judged = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref='submissions')
    
    def __repr__(self):
        return f'<Submission {self.id} by {self.user_id} for {self.problem_shortname}>'


def get_top_submission():
    return Submission.query.filter_by(judged=False)\
                                     .order_by(Submission.problem_difficulty.desc())\
                                     .first()
