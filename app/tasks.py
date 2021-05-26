import time
from rq import get_current_job
from app import db
from app.models import Task


def example(id, seconds):
    print(f'Tasks.py, seconds = {seconds}')
    print(f'id = {id}')
    job = get_current_job()
    print('starting!!')
    for i in range(seconds+1):
        progress = 100.0 * i / seconds
        job.meta['progress'] = progress
        job.save_meta()
        time.sleep(1)
        _set_task_progress(progress)
    job.save_meta()
    print('Task completed')


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})

        if progress >= 100:
            task.complete = True
            print('task is done')
        db.session.commit()