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

    diff = bare_diff_files(first_path, second_path)
    diff_lines = len(diff.split('\n'))
    first_lines = len(open(first_path, 'rb').readlines())
    second_lines = len(open(second_path, 'rb').readlines())

    log.info('diff_lines={}, first={}, second={}'.format(diff_lines, first_lines, second_lines))

    similarity = diff_lines / float(min(first_lines, second_lines)) * 100

    log.info('Similarity between {} and {} is {}'.format(first, second, similarity))
    return similarity


def locate_peers(s, binary):
    log.info('Locating peers for {}'.format(binary))

    binaries = s.query(Binary).filter((Binary.id != binary.id) & (Binary.processed == True)).all()

    log.info('Found potential peers: {}'.format(binaries))

    if not binaries:
        return (None, None)

    for other in binaries:
        if other.parent is None:
            root = other
        else:
            parent = s.query(Binary).get(other.parent)
            parent_diff = measure_similarity(parent, other)
            bin_to_parent = measure_similarity(binary, parent)
            bin_to_other = measure_similarity(binary, other)

            # triangle inequality with delta
            DELTA = 1.1
            if bin_to_parent + bin_to_other < parent_diff * DELTA:
                return (parent, other)

    leaf = next(bin for bin in binaries if not any(oth.parent == bin.id for oth in binaries))

    bin_to_root = measure_similarity(binary, root)
    bin_to_leaf = measure_similarity(binary, leaf)

    if bin_to_root < bin_to_leaf:
        return (None, root)
    else:
        return (leaf, None)

    log.info('Best match is ({}, {}), with similarity index {}'.format(best_match[0], best_match[1], min_index))

    return best_match

def bare_diff_files(first_path, second_path):
    try:
        return subprocess.check_output(['sdiff', '-s', first_path, second_path])
    except subprocess.CalledProcessError as e:
        return e.output


def diff_files(first_path, second_path):
    try:
        return subprocess.check_output(['diff', first_path, second_path])
    except subprocess.CalledProcessError as e:
        return e.output


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
    # TODO and that second race condition with upload
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
            log.info('No peers for {} found'.format(binary))

        if prev is not None:
            diff_peers(s, prev, binary)
            binary.parent = prev.id

        if next is not None:
            diff_peers(s, binary, next)
            next.parent = binary.id
            s.add(next)

        binary.processed = True
        s.add(binary)

        task.status = Task.DONE
        s.add(task)

        log.info('Task {} succeeded'.format(task))
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
