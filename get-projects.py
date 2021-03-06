import apscheduler.schedulers.blocking
import fort
import logging
import os
import requests
import sys

from typing import Dict

log = logging.getLogger('rfpio_api.get_projects')

class Database(fort.PostgresDatabase):
    def add_record(self, params):
        sql = '''
            insert into rfpio_projects (
                project_id, project_name, client_name, status, project_type, stage, stage_comments,
                sf_opportunity_stage, project_value, created_date, due_date, completed_date, last_updated_date,
                project_owner, additional_primary_contacts, num_of_people, requester_email, signed_nda, region,
                sf_account_id, sf_opportunity_id, software_location, test_project_field, education_services_needed,
                list_of_products, ips_or_services_needed, num_sections, num_questions, num_not_answered,
                num_answer_library_used, num_manual, archived_date, project_owner_name, internal_id, company_id
            ) values (
                %(project_id)s, %(project_name)s, %(client_name)s, %(status)s, %(project_type)s, %(stage)s,
                %(stage_comments)s, %(sf_opportunity_stage)s, %(project_value)s, %(created_date)s, %(due_date)s,
                %(completed_date)s, %(last_updated_date)s, %(project_owner)s, %(additional_primary_contacts)s,
                %(num_of_people)s, %(requester_email)s, %(signed_nda)s, %(region)s, %(sf_account_id)s,
                %(sf_opportunity_id)s, %(software_location)s, %(test_project_field)s, %(education_services_needed)s,
                %(list_of_products)s, %(ips_or_services_needed)s, %(num_sections)s, %(num_questions)s,
                %(num_not_answered)s, %(num_answer_library_used)s, %(num_manual)s, %(archived_date)s,
                %(project_owner_name)s, %(internal_id)s, %(company_id)s
            ) on conflict (project_id) do update set
                project_name = %(project_name)s, client_name = %(client_name)s, status = %(status)s,
                project_type = %(project_type)s, stage = %(stage)s, stage_comments = %(stage_comments)s,
                sf_opportunity_stage = %(sf_opportunity_stage)s, project_value = %(project_value)s,
                created_date = %(created_date)s, due_date = %(due_date)s, completed_date = %(completed_date)s,
                last_updated_date = %(last_updated_date)s, project_owner = %(project_owner)s,
                additional_primary_contacts = %(additional_primary_contacts)s, num_of_people = %(num_of_people)s,
                requester_email = %(requester_email)s, signed_nda = %(signed_nda)s, region = %(region)s,
                sf_account_id = %(sf_account_id)s, sf_opportunity_id = %(sf_opportunity_id)s,
                software_location = %(software_location)s, test_project_field = %(test_project_field)s,
                education_services_needed = %(education_services_needed)s, list_of_products = %(list_of_products)s,
                ips_or_services_needed = %(ips_or_services_needed)s, num_sections = %(num_sections)s,
                num_questions = %(num_questions)s, num_not_answered = %(num_not_answered)s,
                num_answer_library_used = %(num_answer_library_used)s, num_manual = %(num_manual)s,
                archived_date = %(archived_date)s, project_owner_name = %(project_owner_name)s,
                internal_id = %(internal_id)s, company_id = %(company_id)s
        '''
        self.u(sql, params)


def save_projects(projects, user_list=None):
    if user_list is None:
        user_list = {}
    db = Database(os.getenv('DB'), minconn=3)
    for p in projects:
        p_products = p.get('customFields', {}).get('listofproducts', [])
        if not isinstance(p_products, list):
            p_products = [p_products]
        pd = {
            'project_id': p.get('customFields', {}).get('project_id'),
            'project_name': p.get('name'),
            'client_name': p.get('issuerName'),
            'status': p.get('status', '').replace('_', ' ').title(),
            'project_type': p.get('rfpType'),
            'stage': p.get('projectStage', {}).get('stage'),
            'stage_comments': p.get('projectStage', {}).get('comments'),
            'sf_opportunity_stage': ', '.join(p.get('category', [])),
            'project_value': p.get('dealSize', 0),
            'created_date': p.get('createdDate', '')[:10],
            'due_date': p.get('dueDate', '')[:10],
            'completed_date': p.get('respondedDate', '')[:10],
            'last_updated_date': p.get('lastUpdateTs', '')[:10],
            'archived_date': p.get('archivedDate', '')[:10],
            'project_owner': p.get('ownedBy'),
            'project_owner_name': user_list.get(p.get('ownedBy')),
            'additional_primary_contacts': ', '.join(p.get('additionalContacts', [])),
            'num_of_people': len(p.get('teamMembers', [])),
            'requester_email': p.get('customFields', {}).get('useremailaddress'),
            'signed_nda': ', '.join(p.get('customFields', {}).get('nda', [])),
            'region': ', '.join(p.get('customFields', {}).get('regionprojectlevel', [])),
            'sf_account_id': p.get('customFields', {}).get('accountid'),
            'sf_opportunity_id': p.get('customFields', {}).get('opportunityid'),
            'software_location': p.get('customFields', {}).get('locationofsoftware'),
            'test_project_field': p.get('customFields', {}).get('test_project_field'),
            'education_services_needed': p.get('customFields', {}).get('infatraining'),
            'list_of_products': ', '.join(p_products),
            'ips_or_services_needed': p.get('customFields', {}).get('services_needed'),
            'num_sections': p.get('sectionCount', 0),
            'num_questions': p.get('totalQuestionCount', 0),
            'num_not_answered': p.get('totalQuestionCount', 0) - p.get('totalAnsweredCount', 0),
            'num_answer_library_used': p.get('totalAnsweredUsingAL', 0),
            'num_manual': p.get('totalAnsweredCount', 0) - p.get('totalAnsweredUsingAL', 0),
            'internal_id': p.get('id'),
            'company_id': p.get('companyId')
        }
        if pd.get('archived_date') == '':
            pd.update({'archived_date': None})
        if pd.get('completed_date') == '':
            pd.update({'completed_date': None})
        if pd.get('project_id') is None:
            continue
        db.add_record(pd)


def get_projects(token):
    projects = []
    s = requests.Session()
    count_url = 'https://app.rfpio.com/rfpserver/projects/respond/get-count'
    projects_url = 'https://app.rfpio.com/rfpserver/projects/respond/get-filtered-projects'
    headers = {
        'authorization': f'Bearer {token}'
    }
    count_resp = s.post(count_url, headers=headers, json={})
    if count_resp.status_code == 401:
        log.critical(f'Unauthorized. Is your RFPIO_TOKEN correct? ({token})')
        return projects
    for status, count in count_resp.json().items():
        payload = {
            'status': status,
            'limit': count,
            'query': {'sortBy': 'due_date', 'sortingOrder': 1}
        }
        log.debug(f'Attempt to get {count} projects with status {status}')
        resp = s.post(projects_url, headers=headers, json=payload)
        projects.extend(resp.json()['projects'])
    return projects


def get_users(token) -> Dict:
    users = {}
    s = requests.Session()
    users_url = 'https://app.rfpio.com/rfpserver/load/user-load-details'
    headers = {
        'authorization': f'Bearer {token}'
    }
    users_resp = s.get(users_url, headers=headers)
    users_resp.raise_for_status()
    for u in users_resp.json().get('userVOList').get('users'):
        username = u.get('userName')
        display_name = u.get('displayName')
        users.update({username: display_name})
    return users


def main_job():
    token = os.getenv('RFPIO_TOKEN')
    user_list = get_users(token)
    projects = get_projects(token)
    save_projects(projects, user_list)
    log.info(f'Found {len(projects)} projects')


def main():
    log_format = os.getenv('LOG_FORMAT', '%(levelname)s [%(name)s] %(message)s')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(format=log_format, level='DEBUG', stream=sys.stdout)
    version = os.getenv('APP_VERSION', 'unknown')
    log.debug(f'rfpio_api.get_projects {version}')
    if not log_level == 'DEBUG':
        log.debug(f'Setting log level to {log_level}')
    logging.getLogger().setLevel(log_level)

    scheduler = apscheduler.schedulers.blocking.BlockingScheduler()
    scheduler.add_job(main_job, 'interval', minutes=int(os.getenv('SYNC_INTERVAL', '60')))
    scheduler.add_job(main_job)
    scheduler.start()


if __name__ == '__main__':
    main()
