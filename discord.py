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

    # get Spring 25 courses
    sp25_courses = list(filter(
        lambda course: course.term == 'Spring' and course.year == '2025',
            student_courses.values()))

    for course in sp25_courses:
        if course.cid == '960168':
            res = gs.get_assignments(course.cid)
            assignments = res.assignments

            sort_by_deadline_fn = lambda x: gs.to_datetime_object(x.due_time)
            # sort assignments by deadline
            sorted_assignments = sorted(assignments, key=sort_by_deadline_fn)
        
            for assgn in sorted_assignments:
                print(assgn.due_time)

    # print(sp25_courses)
    
    # for course in student_courses.get('708063'):
    #     res = gs.get_assignments(course.cid)
    #     print(res)
    #     filtered = sorted(list(filter(
    #         lambda x: 
    #             x. 
                
    #         res)), key=lambda x: x['due_time'])

    # assignments = gs.get_assignments('708063').assignments
    # filtered = sorted(
    #     list(filter(
    #         lambda x:
    #             x.submission_status == SubStatus.UNSUBMITTED and
    #             x.due_time, assignments)),
    #     key=lambda x: x.due_time)

    # for assgn in filtered:
    #     print(assgn.due_time)