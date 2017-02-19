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


def measure_similarity(first, second):
    first_path = UPLOADS + first.hash
    second_path = UPLOADS + second.hash

    diff = diff_files(first_path, second_path)
    diff_lines = len(diff.split('\n'))
    first_lines = len(open(first_path, 'rb').readlines())
    second_lines = len(open(second_path, 'rb').readlines())

    return diff_lines / float(min(first_lines, second_lines)) * 100


def locate_peers(s, binary):
    log.info('Locating peers for {}'.format(binary))

    binaries = s.query(Binary).filter(Binary.id != binary.id).all()

    similarities = {}

    for other in binaries:
        similarity_level = measure_similarity(binary, other)
        similarities[other.id] = similarity_level

    min_index = 10**10
    best_match = (None, None)

    for other in binaries:
        if other.parent is None:
            similarity_index = similarities[other.id] * 2
        else:
            similarity_index = similarities[other.id] + similarities[other.parent]

        if similarity_index < min_index:
            min_index = similarity_index
            best_match = (other.parent, other)

    for other in binaries:
        if any(b.parent == other.id for b in binaries):
            continue

        similatity_index = similarities[other.id] * 2

        if similarity_index < min_index:
            min_index = similarity_index
            best_match = (other, None)

    log.info('Best match is ({}, {}), with similarity index {}'.format(best_match[0], best_match[1], min_index))

    return best_match


def diff_files(first_path, second_path):
    try:
        out = subprocess.check_output(['diff', first_path, second_path])
    except subprocess.CalledProcessError as e:
        out = e.output

    return out


def diff_peers(s, first, second):
    log.info('Diffing binaries {} and {}'.format(first, second))

    prev_path = UPLOADS + first.hash
    next_path = UPLOADS + second.hash

    out = diff_files(prev_path, next_path)

    diff = Diff(first=first.id, second=second.id, content=out)
    s.add(diff)


def handle_new_binary_task():
    s = Session()
    task = s.query(Task).filter(Task.status == Task.NEW).first()
    if not task:
        time.sleep(1)
        return False

    # TODO fix race condition
    task.status = Task.IN_PROGRESS
    s.add(task)
    s.commit()

    log.info('New task found: {}'.format(task))

    try:
        binary = s.query(Binary).get(task.binary)

        log.info('Processing binary {}'.format(binary))

        prev, next = locate_peers(s, binary)

        log.info('Guessing peers for {}: {} and {}'.format(binary, prev, next))

        if prev is None and next is None:
            log.info('No peers for {} found, no work to do'.format(binary))

        if prev is not None:
            diff_peers(s, prev, binary)
            binary.parent = prev.id
            s.add(binary)

        if next is not None:
            diff_peers(s, binary, next)
            next.parent = binary.id
            s.add(next)

        log.info('Task {} succeeded'.format(task))

        task.status = Task.DONE
        s.add(task)
    except:
        log.error('Task {} failed. Error: {}'.format(task, traceback.format_exc()))
        task.status = Task.ERRORED
        s.add(task)
    finally:
        s.commit()

    return True


def main():
    while True:
        any_work = False
        any_work = handle_new_binary_task() or any_work

        if not any_work:
            time.sleep(1)


if __name__ == '__main__':
    main()
