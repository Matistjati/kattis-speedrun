import secrets
from datetime import datetime, timedelta
import threading

from flask import Flask, request, jsonify, make_response, redirect, url_for, render_template
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy

from backend.extensions import socketio
from backend.model import eventhandler
import os
from backend.models import db, User, SpeedRun
from backend.login.login import login
from backend.login.logout import logout
from backend.model.submission_queue import submission_queue
from backend.model.submit_route import submit_bp
from backend.model.shortest_unsolved import shortest_unsolved
from backend.data_emit.queue_data import emit_update_queue


def load_secret_key(app):
    """Return a SECRET_KEY that is stable across restarts so that active
    sessions survive a server reload (otherwise every reload logs everyone
    out). Prefers the SECRET_KEY env var, then a persisted file in the
    instance folder, generating one on first run."""
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key

    os.makedirs(app.instance_path, exist_ok=True)
    key_path = os.path.join(app.instance_path, 'secret_key')
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            return f.read().strip()

    key = secrets.token_hex(32)
    with open(key_path, 'w') as f:
        f.write(key)
    return key


def create_app():
    app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend/templates")

    q = eventhandler.EventHandler(app)
    app.queue = q

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    db.init_app(app)
    app.config['SECRET_KEY'] = load_secret_key(app)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    global login_manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'login.show'
    login_manager.init_app(app)
    socketio.init_app(app)

    for blueprint in [login, submission_queue, submit_bp, shortest_unsolved, logout]:
        app.register_blueprint(blueprint)

    @app.cli.command('init_db')
    def init_db():
        with app.app_context():
            db.create_all()

        db.session.add(SpeedRun())

        #add_user
        db.session.commit()

    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug/db')
def debug_db():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    # Convert SQLAlchemy inspection results to serializable formats
    tables = inspector.get_table_names()
    
    user_columns = None
    if 'user' in tables:
        user_columns = []
        for column in inspector.get_columns('user'):
            # Convert each column info to a dictionary with serializable values
            column_info = {
                'name': column['name'],
                'type': str(column['type']),  # Convert type to string
                'nullable': column['nullable'],
                'default': str(column['default']) if column['default'] is not None else None,
                'autoincrement': column.get('autoincrement', False)
            }
            user_columns.append(column_info)
    
    return jsonify({
        'tables': tables,
        'user_columns': user_columns
    })

@socketio.on('connect')
def on_connect():
    print('Client connected')

@socketio.on('get_queue_data')
def get_queue_data():
    emit_update_queue()



def start_judging_thread():
    print("[main] Starting queue runner")
    queue_runner = threading.Thread(target=app.queue.run, daemon=True)
    queue_runner.start()

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_judging_thread()

    app.run(
        host='0.0.0.0',
        port=5000,
        #ssl_context=('cert.pem', 'key.pem'),
        debug=True
    )
