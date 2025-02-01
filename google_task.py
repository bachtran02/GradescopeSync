import os
import sys
import time
import typing as t
from dotenv import load_dotenv
import logging

from collections import defaultdict
from datetime import timezone, datetime as dt

from task.task import GSTaskClient, GTask
from gradescope.gradescope import Gradescope
from gradescope.course import Course
from gradescope.assignment import Assignment, SubmissionStatus as SubStatus

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout), # Log to stdout
        logging.FileHandler('logs/main.log')
    ]
)

logger = logging.getLogger(__name__)

ASSIGNMENT_URL_FMT = 'https://www.gradescope.com/courses/{}/assignments/{}'

def assignment_to_task(assgn: Assignment, course_shortname: str) -> GTask:

    # process & transform time
    # NOTE: <https://googleapis.github.io/google-api-python-client/docs/dyn/tasks_v1.tasks.html#insert>
    # > The due date only records date information; the time portion  
    # > of the timestamp is discarded when setting the due date.
    due = dt.strptime(assgn.due_time, '%Y-%m-%d %H:%M:%S %z')
    due = dt(due.year, due.month, due.day, 0, 0, 0, tzinfo=timezone.utc)
    due = due.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    return {
        'title': f'[{course_shortname}] {assgn.name}',
        'due': due,
        'status': 'needsAction' if assgn.submission_status == SubStatus.UNSUBMITTED else 'completed',
        'notes': ASSIGNMENT_URL_FMT.format(assgn.cid, assgn.aid)
    }

def main():

    gs = Gradescope(
        username=os.getenv('USERNAME'),
        password=os.getenv('PASSWORD'))
    
    if not gs.login():
        print('failed to log in Gradescope')
        sys.exit(1)
    
    # TODO: handle google task api error
    client = GSTaskClient(
        client_secret_file=os.getenv('CLIENT_SECRET_FILE'),
        token_file=os.getenv('TOKEN_FILE'),
        tasklist_name='gs_deadlines'
    )

    client.authenticate()       # autheticate
    client.init_tasklist()      # initiate tasklist, cache existing tasks

    assignments = []
    student_courses: t.List[Course] = gs.get_courses().student_courses

    # get Fall 24 courses
    fa24_courses = list(filter(
        lambda course: course.term == "Fall" and course.year == "2024",
            student_courses.values()))
    
    for course in fa24_courses:
        res = gs.get_assignments(course.cid)
        assignments.extend(res.assignments)

    # only retain undue assignments
    assignments = list(filter(
        lambda a: dt.now(timezone.utc) < dt.strptime(a.due_time, '%Y-%m-%d %H:%M:%S %z'), 
            assignments))

    # convert course + assignment into task out here
    tasks = defaultdict(GTask)
    for assignment in assignments:
        key = assignment.cid + assignment.aid
        tasks[key] = assignment_to_task(
            assgn=assignment,
            course_shortname=student_courses[assignment.cid].shortname)

    client.update_tasks(tasks)

if __name__ == "__main__":
    while True:
        main()
        logging.info('Sync completed. Next sync cycle in 10 minutes')
        time.sleep(600)