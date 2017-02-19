import datetime
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///database.db')
Base = declarative_base()

class Binary(Base):
    __tablename__ = 'binary'

    id = Column(Integer, primary_key=True)
    hash = Column(String, nullable=False)
    upload_date = Column(DateTime, nullable=False, default=datetime.datetime.now)
    parent = Column(Integer)

    def __repr__(self):
        return 'Binary({}, {}, {})'.format(self.id, self.hash, self.parent)


class Diff(Base):
    __tablename__ = 'diff'

    id = Column(Integer, primary_key=True)
    first = Column(Integer, ForeignKey('binary.id'), nullable=False)
    second = Column(Integer, ForeignKey('binary.id'), nullable=False)
    content = Column(String, nullable=False)

    def __repr__(self):
        return 'Diff({}, {}, {})'.format(self.id, self.first, self.second)


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    binary = Column(Integer, ForeignKey('binary.id'), nullable=False)
    status = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return 'Task({}, {}, {})'.format(self.id, self.binary, Task.STATUS_NAMES[self.status])

    NEW = 0
    IN_PROGRESS = 1
    DONE = 2
    ERRORED = 3

    STATUS_NAMES = ['new', 'in_progress', 'done', 'errored']


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
