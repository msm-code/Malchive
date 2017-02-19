from flask import Flask, render_template, request, redirect, url_for
from db import Session, Binary, Diff, Task
import hashlib
import logging

app = Flask(__name__)
app.debug = True

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

log.info('Logging configured')

UPLOADS = 'upload/'


def add_task(s, first, second):
    log.info('diffing {} and {}'.format(first.hash, second.hash))
    if s.query(Task).filter(
            (Task.first == first.id and Task.second == second.id) or 
            (Task.first == second.id and Task.second == first.id)).first():
        log.info('diff of {} and {} was already generated, returning'.format(first.hash, second.hash))
        return

    log.info('new diff of {} and {} adding task'.format(first.hash, second.hash))
    task = Task(first=first.id, second=second.id)
    s.add(task)
    s.commit()


def generate_diffs(s, binary):
    # TODO: should approximate binary age, insert in timeline, and diff with previous/next
    # TODO: or should it?

    previous_binary = s.query(Binary).filter(Binary.id < binary.id).order_by(Binary.id.desc()).first()
    if previous_binary is None:
        log.info('no previous binary for diffing with {}'.format(binary.hash))
        return

    add_task(s, previous_binary, binary)


def upload_binary(data):
    hash = hashlib.sha256(data).hexdigest()
    log.info('uploading binary {}'.format(hash))

    s = Session()
    if not s.query(Binary).filter(Binary.hash == hash).first():
        log.info('uploading new binary {}'.format(hash))

        open(UPLOADS + hash, 'wb').write(data)
        binary = Binary(hash=hash)
        s.add(binary)
        s.commit()

        generate_diffs(s, binary)
    else:
        log.info('binary {} was already uploaded'.format(hash))
        pass

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        data = file.read()
        upload_binary(data)

        return redirect(url_for('upload'))

    s = Session()
    binaries = s.query(Binary).all()
    diffs = s.query(Diff).all()
    tasks = s.query(Task).all()
    return render_template('upload.html', user='darkness', binaries=binaries, diffs=diffs, tasks=tasks)

app.run()
