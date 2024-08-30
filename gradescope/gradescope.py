import requests
from bs4 import BeautifulSoup
from enum import Enum

try:
   from account import GSAccount
except ModuleNotFoundError:
   from .account import GSAccount

class ConnState(Enum):
    INIT = 0
    LOGGED_IN = 1

def _ensure_login(func):
    """
    Decorator to ensure valid token before calling the methods.
    """
    def login_wrapper(self, *args, **kwargs):
        if self.state != ConnState.LOGGED_IN:
            self.login()
        return func(self, *args, **kwargs)

    return login_wrapper

class Gradescope():
    BASE_URL = 'https://www.gradescope.com'
    
    def __init__(self, email, pswd) -> None:

        self.email = email
        self.password = pswd

        self.session = requests.Session()
        self.state = ConnState.INIT
        self.account = None

    def login(self):
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
            "session[email]": self.email,
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
                self.account = GSAccount(self.email)
                return True
        else:
            return False
    
    def get_courses(self):

        pass
    

    """
        def get_account(self):
        '''
        Gets and parses account data after login. Note will return false if we are not in a logged in state, but 
        this is subject to change.
        '''
        if self.state != ConnState.LOGGED_IN:
            return False # Should raise exception
        # Get account page and parse it using bs4
        account_resp = self.session.get("https://www.gradescope.com/account")
        parsed_account_resp = BeautifulSoup(account_resp.text, 'html.parser')

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

        student_courses = parsed_account_resp.find('h1', class_ ='pageHeading', string = "Your Courses").next_sibling
        for course in student_courses.find_all('a', class_ = 'courseBox'):
            shortname = course.find('h3', class_ = 'courseBox--shortname').text
            name = course.find('div', class_ = 'courseBox--name').text
            cid = course.get("href").split("/")[-1]
            year = None
            
            for tag in course.parent.previous_siblings:
                cls = tag.get("class")
                if len(cls) and cls[0] == "courseList--term":
                    year = tag.body
                    break
            # if year is None:
            #     return False # Should probably raise an exception.
            self.account.add_class(cid, name, shortname, year)
    
    """

    """
    def _lazy_load_assignments(self):
        '''
        Load the assignment dictionary from assignments. This is done lazily to avoid slowdown caused by getting
        all the assignments for all classes. Also makes us less vulnerable to blocking.
        '''
        assignment_resp = self.session.get('https://www.gradescope.com/courses/'+self.cid)
        parsed_assignment_resp = BeautifulSoup(assignment_resp.text, 'html.parser')

        assignment_table = parsed_assignment_resp.find('table', attrs={'id': 'assignments-student-table'})
        assignment_rows = assignment_table.find('tbody')
        # print(assignment_rows)

        assignment_table = []
        for assignment_row in assignment_rows.findAll('tr', attrs={'role': 'row'}):
            row = assignment_row.descendants
            for item in row:
                print(item)
            # print(assignment_row)
            # row = []
            # for td in assignment_row.findAll('td'):
            #     row.append(td)
            # print(type(assignment_row))
            # print(assignment_row.find_parent())
            # assignment_table.append(assignment_row)
        
    
    """