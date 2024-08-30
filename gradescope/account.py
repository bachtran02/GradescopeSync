import typing as t

class GSAccount():

    def __init__(self, email) -> None:
        self.email = email
        self.student_courses: t.Dict = {}
        self.instructor_courses: t.Dict = {}
    