import submit
from tempfile import NamedTemporaryFile

from backend.models import Submission, db, SpeedRun, get_status_name_from_value

def submit_to_kattis(submission: Submission):
    suffixmap = {
        'Python 3': '.py',
        'C++': '.cpp',
    }
    with NamedTemporaryFile(suffix=suffixmap[submission.language], delete=False) as temp_file:
        temp_file.write(submission.source_code.encode('utf-8'))
        temp_file.flush()
        temp_file.close()

        # Call the submit function from the submit module
        print(f"about to judge {submission.problem_shortname}")
        res = submit.submit(submission.problem_shortname, [temp_file.name])
        if not isinstance(res, tuple):
            speed_run = SpeedRun.query.filter_by().first()
            speed_run.time_till_next_submission_token = int(res)
            db.session.commit()
            print(f"next token in {res} seconds")
            return False
        else:
            speed_run = SpeedRun.query.filter_by().first()
            speed_run.time_till_next_submission_token = -1
            db.session.commit()
            verdict, cpu_time, score = res
    
    if not len(score):
        if verdict == 'Accepted':
            score = 100
        else:
            score = 0
    else:
        score = float(score)

    if not len(cpu_time):
        cpu_time = -1

    submission.status = get_status_name_from_value(verdict)
    submission.run_time = cpu_time
    submission.score = score
    submission.judged = True
    db.session.add(submission)
    db.session.commit()
    return True

if __name__ == "__main__":
    # Example usage
    example_submission = Submission(
        user_id=1,
        language='Python 3',
        problem_shortname='hello',
        source_code='print("Hello, World!")',
        problem_difficulty=1.0
    )
    submit_to_kattis(example_submission)
