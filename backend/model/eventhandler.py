from queue import PriorityQueue
import time

from backend.models import SubmissionQueue

class EventHandler:
    def __init__(self, app):
        self.app = app

    def run(self):
        q = SubmissionQueue()
        while True:
            if (sub := q.get_next_submission()):
                 event = self.event_queue.get()
                 self.handle_event(event)
            time.sleep(0.01)
