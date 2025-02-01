import requests
from bs4 import BeautifulSoup
from enum import Enum
from datetime import datetime

try:
   from course import Course, CourseClient
   from assignment import Assignment, AssignmentClient
except ModuleNotFoundError:
   from .course import Course, CourseClient
   from .assignment import Assignment, AssignmentClient

class ConnState(Enum):
    INIT = 0
    LOGGED_IN = 1

def _ensure_login(func):
    """
    Decorator to ensure valid credentials before calling the methods.
    """
    def login_wrapper(self, *args, **kwargs):
        if self.state != ConnState.LOGGED_IN:
            if not self.login():
                raise Exception('Invalid Gradescope credentials')
        return func(self, *args, **kwargs) 

    return login_wrapper

class Gradescope():
    BASE_URL = 'https://www.gradescope.com'
    
    def __init__(self, username, password) -> None:

        self.username = username
        self.password = password

        self.session = requests.Session()
        self.state = ConnState.INIT
        self.account = None

    def login(self) -> bool:
        '''
        Login to gradescope using email and password.
        Note that the future commands depend on account privilages.
        '''
        init_resp = self.session.get(self.BASE_URL)
        parsed_init_resp = BeautifulSoup(init_resp.text, 'html.parser')
        for form in parsed_init_resp.find_all('form'):
            if form.get("action") == "/login":
                for inp in form.find_all('input'):
                    if inp.get('name') == "authenticity_token":
                        auth_token = inp.get('value')

        login_data = {
            "utf8": "✓",
            "session[email]": self.username,
            "session[password]": self.password,
            "session[remember_me]": 0,
            "commit": "Log In",
            "session[remember_me_sso]": 0,
            "authenticity_token": auth_token,
        }
        login_resp = self.session.post("https://www.gradescope.com/login", params=login_data)
        if len(login_resp.history) != 0:
            if login_resp.history[0].status_code == requests.codes.found:
                self.state = ConnState.LOGGED_IN
                return True
        else:
            return False
    
    @_ensure_login
    def get_courses(self):
        with CourseClient(self.session) as client:
            return client.get_courses()

    @_ensure_login
    def get_assignments(self, course_id: str):
        with AssignmentClient(self.session) as client:
            return client.get_assignments(course_id)
    
    @staticmethod
    def to_datetime_object(datetime_str: str) -> datetime:
        # Gradescope datetime string should be in this format: YYYY-MM-DD HH:MM:SS z
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S %z")