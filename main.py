import os
import requests
from dotenv import load_dotenv
from datetime import datetime as dt

from gradescope.methods import get_courses, get_assignments

assignment_types = ['is_submitted']

if __name__ == '__main__':
    
    load_dotenv()

    embeds = []
    todue_fields, pastdue_fields = [], []
    now = dt.now().timestamp()  # Pactific Time

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
        
        to_due, past_due = '', ''
        field_title = course['course_abbrv']
        for assgn in filtered:  # max 8 assignments for each field (more may result in exception)
            
            due_ts = int(assgn['due_time'].timestamp())
            due = '<t:{}:R>'.format(due_ts) if assgn['due_time'] else '`N/A`'
            late_due = '<t:{}:R>'.format(int(assgn['late_due_time'].timestamp())) if assgn['late_due_time'] else '`N/A`'

            if now < due_ts:
                to_due += '\n' + '[{}]({})\nDue: {} \nLate Due: {}'.format(
                    assgn['title'], assgn['course_url'], due, late_due) + '\n'
            else:
                past_due += '\n' + '[{}]({})\nDue: {} \nLate Due: {}'.format(
                    assgn['title'], assgn['course_url'], due, late_due) + '\n'
                
        todue_fields.append({'name': field_title, 'value': to_due, 'inline': True})
        pastdue_fields.append({'name': field_title, 'value': past_due, 'inline': True})
    
    embeds.append({
        'title': 'Daily Reminder',
        'type': 'rich',
        'color': 0xFF3131,
        'fields': pastdue_fields,
        'description': f'**Type**: `No Submission`, `Past Due`',
    })
    embeds.append({
        'title': 'Daily Reminder',
        'type': 'rich',
        'color': 0x90EE90,
        'fields': todue_fields,
        'description': f'**Type**: `No Submission`, `To Due`',
    })

    req = requests.post(
        url=os.getenv('WEBHOOK_URL'),
        json={
            'username': 'Gradescope',
            'avatar_url': '',
            'embeds': embeds
        })
