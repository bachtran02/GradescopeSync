import os
import requests
from dotenv import load_dotenv
from datetime import datetime as dt

from gradescope.methods import get_courses, get_assignments

assignment_types = ['is_submitted']

if __name__ == '__main__':
    
    load_dotenv()

    embeds = []
    fields = []
    for course in get_courses():
        
        assignments = get_assignments(course['course_id'])
        filtered = sorted(list(filter(
            lambda x: 
                x['is_submitted'] == False and 
                x['course_term'] == 'Spring 2024' and
                isinstance(x['due_time'], dt),
            assignments)), key=lambda x: x['due_time'])
        
        if not filtered:
            continue
        
        field_title = course['course_abbrv']
        field_value = ''
        for assgn in filtered:
            due = '<t:{}:R>'.format(int(assgn['due_time'].timestamp())) if assgn['due_time'] else 'N/A'
            late_due = '<t:{}:R>'.format(int(assgn['late_due_time'].timestamp())) if assgn['late_due_time'] else '`N/A`'
            field_value += '\n' + '[{}]({})\nDue: {} \nLate Due: {}'.format(
                assgn['title'], assgn['course_url'], due, late_due
            ) + '\n'
        fields.append({'name': field_title, 'value': field_value, 'inline': True})
        
    embeds.append({
        'title': 'Daily Reminder',
        'type': 'rich',
        'color': 0x90EE90,
        'fields': fields,
        'description': f'**Type**: `No Submission`',
    })

    req = requests.post(
        url=os.getenv('WEBHOOK_URL'),
        json={
            'username': 'Gradescope',
            'avatar_url': '',
            'embeds': embeds
        })
