from queue import PriorityQueue
import time

from backend.models import SubmissionQueue
from backend.model.make_submission import submit_to_kattis
from backend.data_emit.queue_data import emit_update_queue

class EventHandler:
    def __init__(self, app):
        self.app = app

    def run(self):
        with self.app.app_context():
            q = SubmissionQueue()
        while True:
            with self.app.app_context():
                if (sub := q.get_next_submission()):
                    if not submit_to_kattis(submission=sub):
                        q._refresh_queue() # Add back to queue if submission failed
                    else:
                        with self.app.app_context():
                            emit_update_queue()
            time.sleep(5)
