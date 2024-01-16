import bs4
import typing as t
from datetime import datetime as dt

from gradescope.auth import _request

BASE_URL = 'https://www.gradescope.com'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S %z'

def get_courses() -> t.Dict:
    """Return list of courses on account

    >>> get_courses()
    [{
        'course_id': '000000',
        'course_abbrv': 'CS 101',
        'course_name': 'Hello, world!'
    }]
    """

    response = _request(endpoint="account")
    soup = bs4.BeautifulSoup(response.content, features="html.parser")
    return list(filter(lambda s: s, map(
        lambda tag: {
            'course_id': int(tag.get('href').split("/")[-1]),
            'course_abbrv': tag.find_all('h3', {'class': 'courseBox--shortname'})[0].text,
            'course_name': tag.find_all('div', {'class': 'courseBox--name'})[0].text,
        }, soup.find_all("a", {"class": "courseBox"}))))


def get_assignments(course_id: int) -> t.Dict:

    result = _request(endpoint='courses/{}'.format(course_id))
    soup = bs4.BeautifulSoup(result.content.decode(), features="html.parser")

    course_abbrv = soup.find('h1', {'class': 'courseHeader--title'}).text
    course_term = soup.find('h2', {'class': 'courseHeader--term'}).text

    assignment_table = soup.find('table', {'id': 'assignments-student-table'})
    anchors = assignment_table.find_all('tr')[1:] # exclude first row

    assignments = []
    for anchor in anchors:

        assignment_title, assignment_id = None, None
        is_duplicate = False
 
        if button := anchor.find('th').find('button'):
            assignment_title = button.get('data-assignment-title')
            assignment_id = int(button.get('data-assignment-id'))
            
        elif a := anchor.find('th').find('a'):
            assignment_title = a.text
            assignment_id = int(a.get('href').split('/')[4])

        else:
            th = anchor.find('th')
            assignment_title = th.text

        is_submitted, is_graded, submission_status, score = None, None, None, None
        sub_tag = anchor.find('td', {'class': 'submissionStatus'})
        if sub_tag.find('div'):
            _status = ('submissionStatus--score', 'submissionStatus--text')
            sub_div = list(
                filter(lambda x: x.get('class') and x.get('class')[0] in _status,
                       sub_tag.find_all('div')))[0]
            class_name = sub_div.get('class')[0]
            if class_name == 'submissionStatus--score':
                is_graded, submission_status, score = True, 'Graded', sub_div.text
            if class_name == 'submissionStatus--text':
                is_graded, submission_status, score = False, sub_div.text, ''
            is_submitted = False if submission_status == 'No Submission' else True

        released_time, due_time, late_due_time = None, None, None
        time_tags = anchor.find_all('time')
        for time_tag in time_tags:
            if time_tag.get('class')[0] == 'submissionTimeChart--dueDate':
                if time_tag.get('aria-label').startswith('Due'):
                    due_time = dt.strptime(time_tag.get('datetime'), TIME_FORMAT)
                elif time_tag.get('aria-label').startswith('Late'):
                    late_due_time = dt.strptime(time_tag.get('datetime'), TIME_FORMAT)
            elif time_tag.get('class')[0] == 'submissionTimeChart--releaseDate':
                released_time = dt.strptime(time_tag.get('datetime'), TIME_FORMAT)

        for assignment in assignments:
            if assignment_id == assignment['id'] and assignment_title == assignment['title']:
                is_duplicate = True
                break

        if not is_duplicate:
            assignments.append({
                'course_id': course_id,
                'course_abbrv': course_abbrv,
                'course_term': course_term,
                'course_url': f'{BASE_URL}/courses/{course_id}',
                'id': assignment_id,
                'title': assignment_title,
                'score': score,
                'submission_status': submission_status,
                'is_graded': is_graded,
                'is_submitted': is_submitted,
                'released_time': released_time,
                'due_time': due_time,
                'late_due_time': late_due_time,
            })

    return assignments