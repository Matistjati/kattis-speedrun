from backend.models import SubmissionQueue, User, Submission, Status
from backend.extensions import socketio

def get_queue_emission_data():    
    queue = SubmissionQueue()

    data = {
        "pending": [],
        "judged": []
    }
    for submission in queue.queue:
        sub = {
            "problem_shortname": submission.problem_shortname,
            "language": submission.language,
            "user_name": User.query.get(submission.user_id).username,
            "submitted_at": submission.time.isoformat(),
            "problem_difficulty": submission.problem_difficulty,
        }
        data["pending"].append(sub)

    judged_submissions = Submission.query.filter(Submission.status != Status.WAITING).order_by(Submission.time.desc()).limit(10).all()
    print(f"Judged submissions: {judged_submissions=}")
    for submission in judged_submissions:
        sub = {
            "problem_shortname": submission.problem_shortname,
            "language": submission.language,
            "user_name": User.query.get(submission.user_id).username,
            "submitted_at": submission.time.isoformat(),
            "problem_difficulty": submission.problem_difficulty,
            "verdict": submission.status.value,
            "run_time": submission.run_time,
            "score": submission.score,
        }
        data["judged"].append(sub)

    data["pending"].sort(key=lambda x: x["problem_difficulty"], reverse=True)
    return data

def emit_update_queue():
    print("Sending queue update")
    print(socketio.server.manager.rooms)
    socketio.emit('queue_data', get_queue_emission_data())
