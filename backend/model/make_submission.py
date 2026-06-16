import submit
import os
import json
import re
import tempfile
from tempfile import NamedTemporaryFile

from backend.models import Submission, db, SpeedRun, get_status_name_from_value

SUFFIX_MAP = {
    'Python 3': '.py',
    'C++': '.cpp',
    'Rust': '.rs',
}


def write_submission_files(submission: Submission):
    """Materialise a submission to files on disk for Kattis.

    Supports two storage formats in ``source_code``:
      * a JSON list ``[{"name": ..., "content": ...}, ...]`` for one or more
        uploaded files (filenames preserved so Kattis can detect the main file
        and the language), and
      * a plain source blob from the code textarea (single file, named by the
        selected language's suffix).

    Returns the list of file paths to submit.
    """
    parsed = None
    try:
        parsed = json.loads(submission.source_code)
    except (ValueError, TypeError):
        parsed = None

    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and 'name' in parsed[0]:
        tmpdir = tempfile.mkdtemp(prefix='kattis-sub-')
        paths = []
        for entry in parsed:
            name = os.path.basename(entry.get('name') or 'file')
            path = os.path.join(tmpdir, name)
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(entry.get('content', ''))
            paths.append(path)
        return paths

    suffix = SUFFIX_MAP.get(submission.language, '.txt')
    with NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(submission.source_code.encode('utf-8'))
        temp_file.flush()
    return [temp_file.name]


def submit_to_kattis(submission: Submission):
    files = write_submission_files(submission)

    # Call the submit function from the submit module
    print(f"about to judge {submission.problem_shortname}")
    res = submit.submit(submission.problem_shortname, files)
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
        verdict, cpu_time, score, kattis_submission_id = res
        submission.submission_id = kattis_submission_id

    if not len(score):
        if verdict == 'Accepted':
            score = 100
        else:
            score = 0
    else:
        score = float(score)

    # cpu_time can be a plain number ("0.05"), a TLE marker ("> 1.00" with a
    # non-breaking space), or empty; pull out the numeric part, else default -1.
    cpu_match = re.search(r'[\d.]+', cpu_time) if isinstance(cpu_time, str) else None
    cpu_time = float(cpu_match.group()) if cpu_match else -1

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
