import os
import requests
from dotenv import load_dotenv
from datetime import timezone, timedelta, datetime as dt
import typing as t

from gradescope.course import Course
from gradescope.gradescope import Gradescope
from gradescope.assignment import Assignment, SubmissionStatus as SubStatus

GRADESCOPE_BASE_URL = 'https://www.gradescope.com'

load_dotenv()

if __name__ == '__main__':

    embeds = []

    gs = Gradescope(
        username=os.getenv('USERNAME'),
        password=os.getenv('PASSWORD'))
    
    student_courses: t.List[Course] = gs.get_courses().student_courses

    # get Spring 25 courses
    sp25_courses = list(filter(
        lambda course: course.term == 'Spring' and course.year == '2025',
            student_courses.values()))
    
    # non-past due assignments, submitted vs unsubmitted
    # past due assignments

    past_due = ''
    todue_list, todue_fields = [], []
    due_count, due_today_count = 0, 0
    nextdue_assign, nextdue_url, nextdue_crs, nextdue_dt = None, None, None, None

    for course in sp25_courses:
        res = gs.get_assignments(course.cid)
        assignments = res.assignments
        assignments_with_dt = []
        
        for assgn in assignments:
            due_datetime, late_due_datetime = None, None

            if assgn.due_time:
                due_datetime = gs.to_datetime_object(assgn.due_time)
            if assgn.late_due_time:
                late_due_datetime = gs.to_datetime_object(assgn.late_due_time)
        
            assignments_with_dt.append((assgn, due_datetime, late_due_datetime))

        # sort assignments by due deadline
        sorted_assignments = sorted(assignments_with_dt, key=lambda x: x[1])

        now = dt.now(timezone.utc)
        todue_str = ''

        for assgn_with_dt in sorted_assignments:

            assgn: Assignment = assgn_with_dt[0]
            due_dt, late_due_dt = assgn_with_dt[1:]

            assgn_url = '{}/courses/{}/assignments/{}'.format(
                GRADESCOPE_BASE_URL, course.cid, assgn.aid)

            if due_dt:
                due = '<t:{}:R>'.format(int(due_dt.timestamp()))
            else:
                due = '`N/A`'

            if late_due_dt:
                late_due = '<t:{}:R>'.format(int(late_due_dt.timestamp()))
            else:
                late_due = '`N/A`'

            # timezone aware or nah
            if now < due_dt:   # undue assignments

                # find next due assignment across all courses
                if nextdue_assign is None or due_dt < nextdue_dt:
                    nextdue_assign = assgn.name
                    nextdue_url = assgn_url
                    nextdue_crs = course.shortname
                    nextdue_dt = due_dt

                if assgn.submission_status == SubStatus.UNSUBMITTED:
                    submission_emoji = '🟡' 
                else:
                    submission_emoji = '✅'

                todue_str += '\n{} [{}]({})\nDue: {} \nLate Due: {}\n'.format(
                    submission_emoji, assgn.name, assgn_url, due, late_due)
                
                if now + timedelta(days=1) > due_dt:
                    due_today_count += 1
                due_count += 1
                
            else:
                # past due assignments
                if assgn.submission_status == SubStatus.UNSUBMITTED:
                    past_due += '- [{}]({}) - {} {}\n'.format(
                        assgn.name, assgn_url, course.shortname, due_dt)

        if todue_str:
            todue_fields.append({'name': course.shortname, 'value': todue_str, 'inline': True})

    todue_desc = '## Summary\n- Total: **{}**\n- Due Today: **{}**\n'.format(due_count, due_today_count)
    if nextdue_assign:
        todue_desc += '- Next due: **[{}]({}) ({}) <t:{}:R>**'.format(
            nextdue_assign, nextdue_url, nextdue_crs, int(nextdue_dt.timestamp()))
        
    embeds.append({
        'title': 'Missing Submission',
        'type': 'rich',
        'color': 0xFF3131,
        'description': past_due,
    })

    embeds.append({
        'title': 'Homework Reminder',
        'type': 'rich',
        'color': 0x90EE90,
        'fields': todue_fields,
        'description': todue_desc,
    })

    req = requests.post(
        url=os.getenv('WEBHOOK_URL'),
        json={
            'username': 'Gradescope',
            'avatar_url': '',
            'embeds': embeds
        })
    
    if req.status_code != 204:  # normal status code
        req.raise_for_status()