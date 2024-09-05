import os
import requests
from dotenv import load_dotenv
from datetime import timezone, timedelta, datetime as dt
import typing as t

from gradescope.course import Course
from gradescope.gradescope import Gradescope
from gradescope.assignment import Assignment, SubmissionStatus as SubStatus


load_dotenv()

if __name__ == '__main__':

    gs = Gradescope(
        username=os.getenv('USERNAME'),
        password=os.getenv('PASSWORD'))
    
    student_courses: t.List[Course] = gs.get_courses().student_courses

    # get Fall 24 courses
    # fa24_courses = list(filter(
    #     lambda course: course.term == "Fall" and course.year == "2024",
    #         student_courses.values()))
    
    # for course in student_courses.get('708063'):
    #     res = gs.get_assignments(course.cid)
    #     print(res)
        # filtered = sorted(list(filter(
        #     lambda x: 
        #         x. 
                
        #     res)), key=lambda x: x['due_time'])

    assignments = gs.get_assignments('708063').assignments
    filtered = sorted(
        list(filter(
            lambda x:
                x.submission_status == SubStatus.UNSUBMITTED and
                x.due_time, assignments)),
        key=lambda x: x.due_time)

    for assgn in filtered:
        print(assgn.due_time)