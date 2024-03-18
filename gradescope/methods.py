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
        'id': '000000',
        'abbrv': 'CS 101',
        'name': 'Hello, world!',
        'term': 'Fall 2017',
        'type': 'student'/'instructor',
    }]
    """

    response = _request(endpoint="account")
    soup = bs4.BeautifulSoup(response.content, features="html.parser")
    
    courses = []

    course_types = soup.find_all('h1', {'class': 'pageHeading'})
    course_lists = soup.find_all('div', {'class': 'courseList'})

    assert len(course_types) == len(course_lists)

    for clist, ctype in zip(course_lists, course_types):
        terms = clist.find_all('div', 'courseList--term')
        tcourses = clist.find_all('div', 'courseList--coursesForTerm')
        
        assert len(terms) == len(tcourses)

        for term, tcourse in zip(terms, tcourses):
            courses.extend(list(map(
                lambda tag: {
                    'id': int(tag.get('href').split("/")[-1]),
                    'abbrv': tag.find('h3', {'class': 'courseBox--shortname'}).text,
                    'name': tag.find('div', {'class': 'courseBox--name'}).text,
                    'term': term.text,
                    'type': ctype.text.split()[0].lower(),
                    # 'assignment_count': int(tag.find('div', {'class': 'courseBox--assignments'}).text.split()[0]),
                }, tcourse.find_all("a", {"class": "courseBox"}))))
    return courses


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
                'url': f'{BASE_URL}/courses/{course_id}/assignments/{assignment_id}',
                'score': score,
                'submission_status': submission_status,
                'is_graded': is_graded,
                'is_submitted': is_submitted,
                'released_time': released_time,
                'due_time': due_time,
                'late_due_time': late_due_time,
            })

    return assignments