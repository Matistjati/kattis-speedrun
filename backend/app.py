import secrets
from datetime import datetime, timedelta
import threading

from flask import Flask, request, jsonify, make_response, redirect, url_for, render_template
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy

from backend.model import eventhandler
import os
from backend.models import db, User, SpeedRun
from backend.login.login import login
from backend.login.register import register
from backend.login.logout import logout
from backend.model.submission_queue import submission_queue
from backend.model.submit import submit
from backend.data_emit.queue_data import get_queue_emission_data

socketio = SocketIO()

def create_app():
    app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend/templates")
    app.extensions["socketio"] = socketio

    q = eventhandler.EventHandler(app)
    app.queue = q
    queue_runner = threading.Thread(target=q.run, daemon=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    db.init_app(app)
    app.config['SECRET_KEY'] = secrets.token_hex(32)
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

    for blueprint in [login, register, submission_queue, submit, logout]:
        app.register_blueprint(blueprint)

    @app.cli.command('init_db')
    def init_db():
        with app.app_context():
            db.create_all()

        db.session.add(SpeedRun())

        #add_user
        db.session.commit()

    queue_runner.start()

    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

    if not current_user.is_authenticated:
        print("User not authenticated")
        return False

    print(f"User {current_user.username} connected via Socket.IO")
    join_room(current_user.id)


@socketio.on('get_queue_data')
def get_queue_data():
    if not current_user.is_authenticated:
        print("User not authenticated")
        return False

    print("GIVING QUEUE DATA")
    emit('queue_data', get_queue_emission_data())


if __name__ == '__main__':
    for rule in app.url_map.iter_rules():
        print(rule)
    app.run(
        host='0.0.0.0',
        port=5000,
        #ssl_context=('cert.pem', 'key.pem'),
        debug=True
    )
