from queue import PriorityQueue
import time
import threading

from backend.models import get_top_submission, Status, db, SpeedRun, Submission
from backend.model.make_submission import submit_to_kattis
from backend.data_emit.queue_data import emit_update_queue

class EventHandler:
    def __init__(self, app):
        self.app = app

    def run(self):
        last_judged_time = time.time()
        while True:
            try:
                with self.app.app_context():
                    if (sub := get_top_submission()):
                        print(f"Judging submission {sub.id} for problem {sub.problem_shortname} by user {sub.user_id}")
                        sub.status = Status.RUNNING
                        db.session.commit()
                        emit_update_queue()
                        if not submit_to_kattis(submission=sub):
                            sub.status = Status.WAITING
                            db.session.commit()
                        emit_update_queue()
                        last_judged_time = time.time()
                    else:
                        if time.time() - last_judged_time > 60:
                            speed_run = SpeedRun.query.first()
                            speed_run.time_till_next_submission_token = -1
                            db.session.commit()
            except (Exception, SystemExit) as exc:
                # Never let a single bad submission (network error, missing
                # ~/.kattisrc -> submit.py sys.exit, etc.) kill the queue.
                # Reset it to WAITING so it is retried on the next pass.
                print(f"[queue] error while judging: {exc!r}")
                try:
                    with self.app.app_context():
                        if (sub := get_top_submission()) and sub.status == Status.RUNNING:
                            sub.status = Status.WAITING
                            db.session.commit()
                except Exception as cleanup_exc:
                    print(f"[queue] cleanup failed: {cleanup_exc!r}")
            time.sleep(5)
