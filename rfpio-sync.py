import csv
import logging
import os
import pathlib
import requests
import sys

log = logging.getLogger(__name__)
if __name__ == '__main__':
    log = logging.getLogger('rfpio_sync')


def version():
    dockerfile: pathlib.Path = pathlib.Path(__file__).resolve().parent / 'Dockerfile'
    with dockerfile.open() as f:
        for line in f:
            if 'org.opencontainers.image.version' in line:
                return line.strip().split('=', maxsplit=1)[1]
    return 'unknown'


def save_projects(projects):
    csv_field_names = [
        'project_id', 'project_name', 'client_name', 'status', 'project_type', 'stage', 'stage_comments',
        'sf_opportunity_stage', 'project_value', 'created_date', 'due_date', 'completed_date', 'last_updated_date',
        'project_owner', 'additional_primary_contacts', 'num_of_people', 'requester_email', 'signed_nda', 'region',
        'sf_account_id', 'sf_opportunity_id', 'software_location', 'test_project_field', 'education_services_needed',
        'list_of_products', 'ips_or_services_needed', 'num_sections', 'num_questions', 'num_not_answered',
        'num_answer_library_used', 'num_manual'
    ]
    with open(os.getenv('OUTPUT_FILE'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_field_names)
        writer.writeheader()
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
                'project_owner': p.get('ownedBy'),
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
                'num_manual': p.get('totalAnsweredCount', 0) - p.get('totalAnsweredUsingAL', 0)
            }
            writer.writerow(pd)


def get_projects():
    projects = []
    s = requests.Session()
    count_url = 'https://app.rfpio.com/rfpserver/projects/respond/get-count'
    projects_url = 'https://app.rfpio.com/rfpserver/projects/respond/get-filtered-projects'
    token = os.getenv('RFPIO_TOKEN')
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


def main():
    log_format = os.getenv('LOG_FORMAT', '%(levelname)s [%(name)s] %(message)s')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(format=log_format, level='DEBUG', stream=sys.stdout)
    log.debug(f'rfpio-sync {version()}')
    if not log_level == 'DEBUG':
        log.debug(f'Setting log level to {log_level}')
    logging.getLogger().setLevel(log_level)
    projects = get_projects()
    save_projects(projects)
    log.info(f'Found {len(projects)} projects')


if __name__ == '__main__':
    main()
