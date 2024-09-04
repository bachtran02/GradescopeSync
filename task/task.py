import re
import os.path
import typing as t
from collections import defaultdict
from datetime import datetime, timezone
import logging as log

from gradescope.assignment import Assignment

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GTask:

    def __init__(
        self,
        completed=None,  # Completion date of the task (as a RFC 3339 timestamp)
        deleted=False,  # Flag indicating whether the task has been deleted
        due=None,  # Due date of the task (as a RFC 3339 timestamp)
        etag=None,  # ETag of the resource
        hidden=False,  # Flag indicating whether the task is hidden
        tid=None,  # Task identifier
        kind="tasks#task",  # Type of the resource, always "tasks#task"
        links=None,  # Collection of links
        notes=None,  # Notes describing the task
        parent=None,  # Parent task identifier
        position=None,  # String indicating the position of the task
        self_link=None,  # URL pointing to this task
        status="needsAction",  # Status of the task
        title=None,  # Title of the task
        updated=None,  # Last modification time of the task
        webview_link=None  # An absolute link to the task in the Google Tasks Web UI
    ) -> None:
        self.completed = completed
        self.deleted = deleted
        self.due = due
        self.etag = etag
        self.hidden = hidden
        self.tid = tid
        self.kind = kind
        self.links = links if links is not None else []
        self.notes = notes
        self.parent = parent
        self.position = position
        self.self_link = self_link
        self.status = status
        self.title = title
        self.updated = updated
        self.webview_link = webview_link

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            tid=data.get('id'),
            title=data.get('title'),
            status=data.get('status'),
            due=data.get('due'),
            notes=data.get('notes')
        )
    
    def to_dict(self):
        return {
            'title': self.title,
            'due': self.due,
            'status': self.status,
            'notes': self.notes
        }
    
    def __repr__(self) -> str:
        return f'<GTask id={self.tid} title="{self.title}">'


class GTasklist:
    def __init__(self, etag=None, lid=None, kind=None, self_link=None, title=None, updated=None) -> None:
        self.etag = etag                # ETag of the resource.
        self.lid = lid                  # Type of the resource. This is always "tasks#taskList".
        self.kind = kind                
        self.self_link = self_link      # URL pointing to this task list. Used to retrieve, update, or delete this task list.
        self.title = title              # Title of the task list. Maximum length allowed: 1024 characters.
        self.updated = updated          # Last modification time of the task list (as a RFC 3339 timestamp).

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            etag=data.get('etag'),
            lid=data.get('id'),
            kind=data.get('kind'),
            self_link=data.get('selfLink'),
            title=data.get('title'),
            updated=data.get('updated')
        )
    
    def to_dict(self):
        return {
            'etag': self.etag,
            'id': self.lid,
            'kind': self.kind,
            'selfLink': self.self_link,
            'title': self.title,
            'updated': self.updated
        }
        

class GSTaskClient:

    NOTES_PATTERN = r"/courses/(\d+)/assignments/(\d+)"
    DEFAULT_TASKLIST_NAME = "gs_tasklist"
    SCOPES = ["https://www.googleapis.com/auth/tasks"]

    def __init__(self, client_secret_file, token_file, tasklist_name = None) -> None:
        self.token_file = token_file
        self.client_secret_file = client_secret_file
        self.tasklist_name = tasklist_name or self.DEFAULT_TASKLIST_NAME

        self.credentials: Credentials = None
        self.service = None
        self.gs_tasklist = None

        self.tasks_cache = defaultdict(GTask)
    
    def authenticate(self):
        
        if os.path.exists(self.token_file):
            self.credentials = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, self.SCOPES)
            
                self.credentials = flow.run_local_server(host='localhost', port=8080, bind_addr=None, open_browser=False)
            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(self.credentials.to_json())
        
        self.service = build("tasks", "v1", credentials=self.credentials)
        log.info('Successfully authenticated.')

    def init_tasklist(self):
        self.gs_tasklist = None
        page_token = None

        while True:
            # Retrieve task lists with the current page token
            tasklists = self.service.tasklists().list(maxResults=100, pageToken=page_token).execute()

            # Check for the task list with the name "gs_tasklist"
            for tasklist in tasklists.get('items', []):
                if tasklist['title'] == self.tasklist_name:
                    self.gs_tasklist = GTasklist.from_dict(tasklist)
                    self.cache_tasks()
                    return

            # Get the next page token, if it exists
            page_token = tasklists.get('nextPageToken')

            # If there are no more pages, exit the loop
            if not page_token:
                break
        
        new_tasklist = self.service.tasklists().insert(body={'title': self.tasklist_name}).execute()
        self.gs_tasklist = GTasklist.from_dict(new_tasklist)

        if not self.gs_tasklist:
            raise Exception('Failed to initiate tasklist')
        log.info('Tasklist initiated.')


    def cache_tasks(self):

        tasks = self.service.tasks().list(
            tasklist=self.gs_tasklist.lid,
            showHidden=True,
            dueMin=datetime.now(timezone.utc).isoformat()
        ).execute()
        
        for item in tasks.get('items'):
            if item['kind'] != 'tasks#task':
                continue

            task = GTask.from_dict(item)

            if task.notes:
                matches = re.findall(self.NOTES_PATTERN, task.notes)
                if matches:
                    course_id, assignment_id = matches[0]
                    self.tasks_cache[course_id+assignment_id] = task
        
        self._log_cached()

    def insert_task(self, key, task_body):
        log.debug(f'Received request to insert task: key={key} task_body={task_body}')

        t = self.service.tasks().insert(
            tasklist=self.gs_tasklist.lid,
            body=task_body,
        ).execute()

        # update cache with added task
        self.tasks_cache[key] = t
        self._log_cached()

    def patch_task(self, key, task_id, task_body):
        log.debug(f'Received request to patch task: key={key} task_body={task_body}')

        t = self.service.tasks().patch(
            tasklist=self.gs_tasklist.lid,
            task=task_id,
            body=task_body,
        ).execute()

        self.tasks_cache[key] = t
        self._log_cached()

    def update_tasks(self, updated_tasks: t.Dict[str, GTask]):

        for key in updated_tasks:
            if key not in self.tasks_cache:
                self.insert_task(key, updated_tasks[key])   # insert task
            elif self.tasks_cache[key].to_dict() != updated_tasks[key]:
                task_id = self.tasks_cache[key].tid
                self.patch_task(key, task_id, updated_tasks[key])   # patch task

    # log cached task
    def _log_cached(self):
        log.debug('Cached tasks:')
        for i, id in enumerate(self.tasks_cache):
            task = self.tasks_cache[id]
            log.debug(f'\ttask {i + 1}: key={id} task_id={task.tid} title={task.title}')