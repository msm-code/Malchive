from db import Session, Binary, Diff, Task
import time
import logging
import traceback
import subprocess

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

log.info('Logging configured')

UPLOADS = 'upload/'


def main():
    while True:
        s = Session()
        task = s.query(Task).filter(Task.status == Task.NEW).first()
        if not task:
            time.sleep(1)
            continue

        # TODO fix race condition
        task.status = Task.IN_PROGRESS
        s.add(task)
        s.commit()

        log.info('New task found: {}'.format(task.id))

        try:
            first = s.query(Binary).get(task.first)
            second = s.query(Binary).get(task.second)

            log.info('Diffing {} and {}'.format(first.hash, second.hash))

            first_path = UPLOADS + first.hash
            second_path = UPLOADS + second.hash

            try:
                out = subprocess.check_output(['diff', first_path, second_path])
            except subprocess.CalledProcessError as e:
                out = e.output

            log.info('Task {} succeeded'.format(task.id))

            diff = Diff(first=first.id, second=second.id, content=out)
            s.add(diff)

            task.status = Task.DONE
            s.add(task)
        except:
            log.error('Error: ' + traceback.format_exc())
            task.status = Task.ERRORED
            s.add(task)
        finally:
            s.commit()


if __name__ == '__main__':
    main()
