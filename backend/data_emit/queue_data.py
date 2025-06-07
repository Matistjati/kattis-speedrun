from backend.models import User, Submission, Status, SpeedRun, db
from backend.extensions import socketio
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

def get_queue_emission_data():
    data = {
        "pending": [],
        "judged": []
    }
    queued_submissions = Submission.query.filter(Submission.judged==False).order_by(Submission.problem_difficulty).limit(10).all()

    for submission in queued_submissions:
        sub = {
            "problem_shortname": submission.problem_shortname,
            "language": submission.language,
            "user_name": User.query.get(submission.user_id).username,
            "submitted_at": submission.time.strftime("%d. %H:%M:%S"),
            "problem_difficulty": submission.problem_difficulty,
            "status": submission.status.value,
        }
        data["pending"].append(sub)

    judged_submissions = Submission.query.filter(Submission.judged==True).order_by(Submission.time.desc()).limit(10).all()
    for submission in judged_submissions:
        sub = {
            "problem_shortname": submission.problem_shortname,
            "language": submission.language,
            "user_name": User.query.get(submission.user_id).username,
            "submitted_at": submission.time.strftime("%d. %H:%M:%S"),
            "problem_difficulty": submission.problem_difficulty,
            "verdict": submission.status.value,
            "run_time": submission.run_time,
            "score": submission.score,
        }
        data["judged"].append(sub)

    data["pending"].sort(key=lambda x: x["problem_difficulty"], reverse=True)
    data["token_refresh"] = SpeedRun.query.first().time_till_next_submission_token


    submission_with_ranks = (
        db.session.query(
            Submission.id,
            Submission.user_id,
            Submission.problem_shortname,
            Submission.problem_difficulty,
            Submission.score,
            func.row_number()
            .over(
                partition_by=(Submission.user_id, Submission.problem_shortname),
                order_by=Submission.score.desc()
            )
            .label('rnk')
        )
    ).subquery()

    top_submissions = (
        db.session.query(
            submission_with_ranks.c.user_id,
            ((submission_with_ranks.c.score / 100.0) * submission_with_ranks.c.problem_difficulty).label("weighted_score")
        )
        .filter(submission_with_ranks.c.rnk == 1)
        .subquery()
    )

    user_total_scores = (
        db.session.query(
            top_submissions.c.user_id,
            func.sum(top_submissions.c.weighted_score).label("total_score")
        )
        .group_by(top_submissions.c.user_id)
        .all()
    )

    data["user_scores"] = [(User.query.get(user_id).username, total_score or 0) for user_id, total_score in user_total_scores]
    print(data["user_scores"])
    data["user_scores"].sort(key=lambda x: x[1], reverse=True)

    return data

def emit_update_queue():
    socketio.emit('queue_data', get_queue_emission_data())
