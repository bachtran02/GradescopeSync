import typing as t
from collections import defaultdict
from bs4 import BeautifulSoup

try:
   from client import Client
except ModuleNotFoundError:
   from .client import Client

class Course:
    
    def __init__(self, cid, name, shortname, term, year):
        self.cid = cid
        self.name = name
        self.shortname = shortname
        self.term = term
        self.year = year

    def __repr__(self) -> str:
        return f'<Course id={self.cid} abbr={self.shortname} term={self.term} {self.year}>'
    
class GetCoursesResult:
    def __init__(self,
                 student_courses: t.Dict[int, Course] = {},
                 instructor_courses: t.Dict[int, Course] = {}) -> None:
        self.student_courses = student_courses
        self.instructor_courses = instructor_courses
    
    def __repr__(self) -> str:
        return (
            f"<GetCoursesResult student={len(self.student_courses)} "
            f"instructor={len(self.instructor_courses)}>"
        )
    
class CourseClient(Client):

    def get_courses(self) -> GetCoursesResult:
        res = self._request('GET', '/account')
        parsed_account_resp = BeautifulSoup(res.text, 'html.parser')

        # Get instructor course data
        '''
        instructor_courses = parsed_account_resp.find('h1', class_ ='pageHeading').next_sibling
        
        for course in instructor_courses.find_all('a', class_ = 'courseBox'):
            shortname = course.find('h3', class_ = 'courseBox--shortname').text
            name = course.find('div', class_ = 'courseBox--name').text
            cid = course.get("href").split("/")[-1]
            year = None
            print(cid, name, shortname)
            for tag in course.parent.previous_siblings:
                if 'courseList--term' in tag.get("class"):
                    year = tag.string
                    break
            if year is None:
                return False # Should probably raise an exception.
            self.account.add_class(cid, name, shortname, year, instructor = True)
        '''

        student_courses = defaultdict(Course)
        student_courses_html = parsed_account_resp.find('h1', class_ ='pageHeading', string = "Course Dashboard").next_sibling
        for course_html in student_courses_html.find_all('a', class_ = 'courseBox'):
            shortname = course_html.find('h3', class_ = 'courseBox--shortname').text
            name = course_html.find('div', class_ = 'courseBox--name').text
            cid = course_html.get("href").split("/")[-1]
            term, year = None, None
            
            for tag in course_html.parent.previous_siblings:
                cls = tag.get("class")
                if len(cls) and cls[0] == "courseList--term":
                    term, year = tag.text.split()
                    break
            student_courses[cid] = Course(cid, name, shortname, term, year)
        
        return GetCoursesResult(
            student_courses=student_courses
        )
