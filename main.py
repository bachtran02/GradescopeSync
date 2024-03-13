import os
import requests
from dotenv import load_dotenv
from datetime import timezone, timedelta, datetime as dt

from gradescope.methods import get_courses, get_assignments

if __name__ == '__main__':
    load_dotenv()

    embeds = []
    pastdue = str()
    todue_list, todue_fields = [], []
    due_today_count = 0
    
    now = dt.now(timezone.utc)

    for course in get_courses():
        
        assignments = get_assignments(course['course_id'])
        filtered = sorted(list(filter(
            lambda x: 
                x['is_submitted'] == False and 
                x['course_term'] == 'Spring 2024' and
                isinstance(x['due_time'], dt),
            assignments)), key=lambda x: x['due_time'])
        
        if not filtered: continue
        
        todue_str = str()
        field_title = course['course_abbrv']
        for assgn in filtered:  # max 8 assignments for each field (more may result in exception)
            
            due_dt = assgn['due_time']
            due = '<t:{}:R>'.format(int(due_dt.timestamp()))
            late_due = '<t:{}:R>'.format(int(late_due.timestamp())) if (late_due := assgn.get('late_due_time')) else '`N/A`'

            if now < due_dt:
                todue_str += '\n[{}]({})\nDue: {} \nLate Due: {}\n'.format(assgn['title'], assgn['url'], due, late_due)
                todue_list.append({'title': assgn['title'], 'url': assgn['url'], 'due': due_dt, 'course': assgn['course_abbrv']})
                if now + timedelta(days=1) > due_dt:
                    due_today_count += 1
            else:
                pastdue += '- [{}]({}) - {} {}\n'.format(
                    assgn['title'], assgn['url'], assgn['course_abbrv'], due)

        if todue_str:
            todue_fields.append({'name': field_title, 'value': todue_str, 'inline': True})

    todue_list = sorted(todue_list, key=lambda x: x['due'])
    todue_desc = '## Summary\n- Total: **{}**\n- Due Today: **{}**\n'.format(len(todue_list), due_today_count)
    if todue_list and (nextdue := todue_list[0]):
        todue_desc += '- Next due: **[{}]({}) ({}) <t:{}:R>**'.format(
            nextdue['title'], nextdue['url'], nextdue['course'], int(nextdue['due'].timestamp()))

    embeds.append({
        'title': '⚠️ Missing Submission',
        'type': 'rich',
        'color': 0xFF3131,
        'description': pastdue,
    })

    embeds.append({
        'title': '🔔 Daily Homework Reminder',
        'type': 'rich',
        'color': 0x90EE90,
        'fields': todue_fields,
        'description': todue_desc,
    })

    req = requests.post(
        url=os.getenv('WEBHOOK_URL'),
        json={
            'username': 'Gradescope',
            'avatar_url': '',
            'embeds': embeds
        })

    if req.status_code != 204:  # normal status code
        req.raise_for_status()