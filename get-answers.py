import apscheduler.schedulers.blocking
import fort
import logging
import os
import requests
import signal
import sys

log = logging.getLogger('rfpio_api.get_answers')

class Database(fort.PostgresDatabase):
    def add_answer(self, params: dict):
        sql = '''
            insert into rfpio_answers (
                id, company_id, question, tags, used_count, content_score, star_rating, updated_date, updated_by,
                status, last_used_date, reviewed, needs_review, review_flag, review_status
            ) values (
                %(id)s, %(company_id)s, %(question)s, %(tags)s, %(used_count)s, %(content_score)s, %(star_rating)s,
                %(updated_date)s, %(updated_by)s, %(status)s, %(last_used_date)s, %(reviewed)s, %(needs_review)s,
                %(review_flag)s, %(review_status)s
            ) on conflict (id) do update set
                company_id = %(company_id)s, question = %(question)s, tags = %(tags)s, used_count = %(used_count)s,
                content_score = %(content_score)s, star_rating = %(star_rating)s, updated_date = %(updated_date)s,
                updated_by = %(updated_by)s, status = %(status)s, last_used_date = %(last_used_date)s,
                reviewed = %(reviewed)s, needs_review = %(needs_review)s, review_flag = %(review_flag)s,
                review_status = %(review_status)s
        '''
        self.u(sql, params)


def get_answers(s: requests.Session):
    url = 'https://app.rfpio.com/rfpserver/ext/v1/answer-lib/search'
    json = {
        'limit': 50,
        'metadata': True
    }
    cursor = None
    while True:
        response = s.post(url, json=json)
        response.raise_for_status()
        payload = response.json()
        yield from payload.get('results', {})
        new_cursor = payload.get('nextCursorMark')
        if new_cursor == cursor:
            log.info('Duplicate cursor, quitting...')
            break
        cursor = new_cursor
        if cursor:
            log.info(f'Cursor is now {cursor}')
            json.update({
                'cursor': cursor
            })
        else:
            break

def main_job():
    db = Database(os.getenv('DB'), maxconn=3)
    token = os.getenv('RFPIO_TOKEN')
    s = requests.Session()
    s.headers.update({
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    count = 0
    announce = 0
    for answer in get_answers(s):
        answer_id = answer.get('id')
        log.debug(f'Found answer {answer_id}')
        db.add_answer({
            'id': answer_id,
            'company_id': answer.get('companyId'),
            'question': answer.get('question'),
            'tags': ' / '.join(answer.get('tags', [])),
            'used_count': answer.get('numUsed'),
            'content_score': answer.get('contentScore'),
            'star_rating': answer.get('starRating'),
            'updated_date': answer.get('updateDate'),
            'updated_by': answer.get('updateBy'),
            'status': answer.get('status'),
            'last_used_date': answer.get('lastUsedDate'),
            'reviewed': answer.get('reviewed'),
            'needs_review': answer.get('needReview'),
            'review_flag': answer.get('reviewFlag'),
            'review_status': answer.get('reviewStatus')
        })
        count += 1
        announce += 1
        if announce > 99:
            log.info(f'Found {count} answers so far')
            announce = 0
    log.info(f'Found {count} total')

def main():
    log_format = os.getenv('LOG_FORMAT', '%(levelname)s [%(name)s] %(message)s')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(format=log_format, level='DEBUG', stream=sys.stdout)
    version = os.getenv('APP_VERSION', 'unknown')
    log.debug(f'rfpio_api.get_answers {version}')
    if not log_level == 'DEBUG':
        log.debug(f'Setting log level to {log_level}')
    logging.getLogger().setLevel(log_level)

    if os.getenv('RUN_AND_EXIT', False):
        main_job()
        return

    scheduler = apscheduler.schedulers.blocking.BlockingScheduler()
    # default run interval is 24 hours
    scheduler.add_job(main_job, 'interval', minutes=int(os.getenv('SYNC_INTERVAL', 60 * 24)))
    scheduler.add_job(main_job)
    scheduler.start()

def handle_sigterm(_signal, _frame):
    sys.exit()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_sigterm)
    main()
