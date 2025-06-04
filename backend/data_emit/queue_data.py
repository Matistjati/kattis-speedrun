from backend.models import SubmissionQueue, User, Submission, Status

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
    for submission in judged_submissions:
        sub = {
            "problem_shortname": submission.problem_shortname,
            "language": submission.language,
            "user_name": User.query.get(submission.user_id).username,
            "submitted_at": submission.time.isoformat(),
            "problem_difficulty": submission.problem_difficulty,
            "verdict": submission.status,
        }
        data["judged"].append(sub)

    data["pending"].sort(key=lambda x: x["problem_difficulty"], reverse=True)
    return data
