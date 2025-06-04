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

    user = db.relationship('User', backref='submissions')
    
    def __repr__(self):
        return f'<Submission {self.id} by {self.user_id} for {self.problem_shortname}>'


class SubmissionQueue:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SubmissionQueue, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.queue = []
        self._refresh_queue()
        self._initialized = True

    def _refresh_queue(self):
        """Load waiting submissions from database ordered by difficulty"""
        self.queue = Submission.query.filter_by(status=Status.WAITING)\
                                     .order_by(Submission.problem_difficulty.desc())\
                                     .all()

    def get_next_submission(self):
        """Get the highest difficulty waiting submission"""
        if not self.queue:
            self._refresh_queue()
            if not self.queue:
                return None
        return self.queue.pop(0)

    def update_verdict(self, submission_id, verdict):
        """Update a submission's verdict and refresh queue if needed"""
        submission = Submission.query.get(submission_id)
        if submission:
            submission.verdict = verdict
            db.session.commit()
            if verdict != Status.WAITING:
                self._refresh_queue()

    def add_submission(self, **kwargs):
        """Add a new submission to the database and queue"""
        submission = Submission(**kwargs)
        db.session.add(submission)
        db.session.commit()
        if submission.status == Status.WAITING:
            self._insert_ordered(submission)

    def _insert_ordered(self, submission):
        """Insert a submission into the queue maintaining difficulty order"""
        for i, existing in enumerate(self.queue):
            if existing.problem_difficulty < submission.problem_difficulty:
                self.queue.insert(i, submission)
                return
        self.queue.append(submission)
