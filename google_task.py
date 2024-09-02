import os
import sys
import typing as t
from dotenv import load_dotenv

from collections import defaultdict
from datetime import timezone, datetime as dt

from task.task import GSTaskClient, GTask
from gradescope.gradescope import Gradescope
from gradescope.course import Course
from gradescope.assignment import SubmissionStatus

load_dotenv()

ASSIGNMENT_URL_FMT = 'https://www.gradescope.com/courses/{}/assignments/{}'

if __name__ == "__main__":

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

        # process & transform time
        # NOTE: <https://googleapis.github.io/google-api-python-client/docs/dyn/tasks_v1.tasks.html#insert>
        # > The due date only records date information; the time portion  
        # > of the timestamp is discarded when setting the due date.
        due = dt.strptime(assignment.due_time, '%Y-%m-%d %H:%M:%S %z')
        due = dt(due.year, due.month, due.day, 0, 0, 0, tzinfo=timezone.utc)
        due = due.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        # process status
        if assignment.submission_status == SubmissionStatus.UNSUBMITTED:
            status = 'needsAction'
        else:
            status = 'completed'

        tasks[key] = {
            'title': f'[{student_courses[assignment.cid].shortname}] {assignment.name}',
            'due': due,
            'status': status,
            'notes': ASSIGNMENT_URL_FMT.format(assignment.cid, assignment.aid)
        }

    client.update_tasks(tasks)
