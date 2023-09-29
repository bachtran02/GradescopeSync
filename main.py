import os
import requests
from dotenv import load_dotenv

from methods import get_courses, get_assignments

assignment_types = ['is_submitted']

if __name__ == '__main__':
    
    load_dotenv()

    embeds = []
    fields = []
    for course in get_courses():
        
        assignments = get_assignments(course['course_id'])
        filtered = sorted(list(filter(
            lambda x: x['is_submitted'] == False,
            assignments)), key=lambda x: x['due_time'])
        
        if not filtered:
            continue
        
        field_title = course['course_abbrv']
        field_value = ''
        for assgn in filtered:
            field_value += '\n' + '[{}]({})\nDue: <t:{}:R> \nLate Due: <t:{}:R>'.format(
                assgn['title'], assgn['course_url'], 
                int(assgn['due_time'].timestamp()),
                int(assgn['late_due_time'].timestamp())
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
