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


def add_tasks(s, binary):
    log.info('Adding task for new binary {}'.format(binary))
    task = Task(binary=binary.id)
    s.add(task)
    s.commit()


def upload_binary(data, name):
    hash = hashlib.sha256(data).hexdigest()
    log.info('Uploading binary {}'.format(hash))

    s = Session()
    if not s.query(Binary).filter(Binary.hash == hash).first():
        log.info('Uploading new binary {}'.format(hash))

        open(UPLOADS + hash, 'wb').write(data)
        binary = Binary(hash=hash, name=name)
        s.add(binary)
        s.commit()

        add_tasks(s, binary)
    else:
        log.info('Binary {} was already uploaded'.format(hash))
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
        upload_binary(data, file.filename)

        return redirect(url_for('upload'))

    s = Session()
    binaries = s.query(Binary).all()
    diffs = s.query(Diff).all()
    tasks = s.query(Task).all()

    return render_template('upload.html', user='darkness', binaries=binaries, diffs=diffs, tasks=tasks)

app.run()
