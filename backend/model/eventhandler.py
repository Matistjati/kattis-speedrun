from queue import PriorityQueue
import time
import threading

from backend.models import get_top_submission, Status, db, SpeedRun, Submission, User
from backend.model.make_submission import submit_to_kattis
from backend.data_emit.queue_data import emit_update_queue
from backend.model.notify_user import ping_user

class EventHandler:
    def __init__(self, app):
        self.app = app

    def run(self):
        last_judged_time = time.time()
        while True:
            with self.app.app_context():
                if (sub := get_top_submission()):
                    print(f"Judging submission {sub.id} for problem {sub.problem_shortname} by user {sub.user_id}")
                    sub.status = Status.RUNNING
                    db.session.commit()
                    emit_update_queue()
                    if not submit_to_kattis(submission=sub):
                        sub.status = Status.WAITING
                        db.session.commit()
                    else:
                        sub = Submission.query.get(sub.id)
                        user: User = User.query.get(sub.user_id)
                        if user.discord_id:
                            ping_user(user.discord_id, sub.problem_shortname, sub.status.value)
                    emit_update_queue()
                    last_judged_time = time.time()
                else:
                    if time.time() - last_judged_time > 60:
                        speed_run = SpeedRun.query.first()
                        speed_run.time_till_next_submission_token = -1
                        db.session.commit()
            time.sleep(5)
