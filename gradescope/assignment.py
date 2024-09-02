import typing as t

from bs4 import BeautifulSoup
from enum import Enum

try:
   from client import Client
except ModuleNotFoundError:
   from .client import Client

class SubmissionStatus(Enum):
    UNSUBMITTED = 0
    SUBMITTED = 1
    GRADED = 2

class Assignment:

    def __init__(self, aid, cid, name, submission_status, released_time, due_time, late_due_time) -> None:
        self.aid = aid
        self.cid = cid
        self.name = name
        self.submission_status = submission_status
        self.released_time = released_time
        self.due_time = due_time
        self.late_due_time = late_due_time
    
    def __repr__(self) -> str:
        return f'<Assignment id={self.aid}>'

class GetAssignmentsResult:
    def __init__(self,
                 course_id: str = None,
                 assignments: t.List[Assignment] = []) -> None:
        self.course_id = course_id
        self.assignments = assignments

class AssignmentClient(Client):

    def get_assignments(self, course_id):
        assignment_resp = self._request('GET', '/courses/' + course_id)
        parsed_assignment_resp = BeautifulSoup(assignment_resp.text, 'html.parser')

        assignment_table = parsed_assignment_resp.find('table', attrs={'id': 'assignments-student-table'})
        assignment_rows = assignment_table.find('tbody')

        assignments = []
        for assignment_row in assignment_rows.findAll('tr', attrs={'role': 'row'}):
            row_items = list(assignment_row.children)

            name = row_items[0].text
            aid = None
            submission_status = None 
            released_time = None
            due_time = None
            late_due_time = None

            if (a := row_items[0].find('a')):
                aid = a.get('href').split('/')[4]
            elif (b := row_items[0].find('button')):
                aid = b.get('data-assignment-id')

            for c in row_items[1].children:
                if cls := c.get('class'):
                    if cls[0] == 'submissionStatus--score':
                        submission_status = SubmissionStatus.GRADED
                    elif cls[0] == 'submissionStatus--text':
                        if c.text == 'Submitted':
                            submission_status = SubmissionStatus.SUBMITTED
                        elif c.text == 'No Submission':
                            submission_status = SubmissionStatus.UNSUBMITTED
            if not submission_status:
                raise Exception('Unknown submission status')

            # some datetime data exists
            if (div := row_items[2].find('div', attrs={'class': 'progressBar--caption'})):
                times = list(div.findAll('time'))
                assert len(times) >= 2
                released_time = times[0].get('datetime')
                due_time = times[1].get('datetime')
                if len(times) == 3:
                    late_due_time = times[2].get('datetime')
            
            assignments.append(
                Assignment(aid, course_id, name, submission_status,
                    released_time, due_time, late_due_time))
        
        return GetAssignmentsResult(
            course_id=course_id,
            assignments=assignments
        )