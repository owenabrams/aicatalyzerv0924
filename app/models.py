# app/models.py
from . import db  # Import the `db` instance from the app package in app/__init__.py

from datetime import datetime

from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import JSON

# app/models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # Create the SQLAlchemy object here

class QuestionNew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), unique=True, nullable=False)
    topic = db.Column(db.String(500), nullable=True)
    context = db.Column(db.String(500), nullable=True)
    links = db.relationship('LinkNew', secondary='question_link', backref='questions', lazy='dynamic')
    videos = db.relationship('VideoNew', secondary='question_video', backref='questions', lazy='dynamic')
    pictures = db.relationship('PictureNew', secondary='question_picture', backref='questions', lazy='dynamic')
    documents = db.relationship('DocumentNew', secondary='question_document', backref='questions', lazy='dynamic')
    answers = db.relationship('AnswerNew', backref='question', lazy=True)

class AnswerNew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, unique=True, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question_new.id'), nullable=False)
    links = db.relationship('LinkNew', secondary='answer_link', backref='answers', lazy='dynamic')
    videos = db.relationship('VideoNew', secondary='answer_video', backref='answers', lazy='dynamic')
    pictures = db.relationship('PictureNew', secondary='answer_picture', backref='answers', lazy='dynamic')
    documents = db.relationship('DocumentNew', secondary='answer_document', backref='answers', lazy='dynamic')

class LinkNew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    topic = db.Column(db.String(500), nullable=True)
    context = db.Column(db.String(500), nullable=True)

class VideoNew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    topic = db.Column(db.String(500), nullable=True)
    context = db.Column(db.String(500), nullable=True)

class PictureNew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    topic = db.Column(db.String(500), nullable=True)
    context = db.Column(db.String(500), nullable=True)

class DocumentNew(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    topic = db.Column(db.String(500), nullable=True)
    context = db.Column(db.String(500), nullable=True)

class TrainingData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500), nullable=True)
    video = db.Column(db.String(500), nullable=True)
    picture = db.Column(db.String(500), nullable=True)
    document = db.Column(db.String(500), nullable=True)
    context = db.Column(db.String(500), nullable=True)
    topic = db.Column(db.String(500), nullable=True)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(500), nullable=False)
    context = db.Column(MutableList.as_mutable(JSON), nullable=True)
    last_question = db.Column(db.String(500), nullable=True)
    last_answer = db.Column(db.String(500), nullable=True)
    last_link = db.Column(db.String(500), nullable=True)
    last_video = db.Column(db.String(500), nullable=True)
    last_picture = db.Column(db.String(500), nullable=True)
    last_document = db.Column(db.String(500), nullable=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(500), nullable=False)
    user_name = db.Column(db.String(500), nullable=False)
    role = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.String(500), nullable=True)

class VideoMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_path = db.Column(db.String(500), nullable=False)
    subtitle_path = db.Column(db.String(500), nullable=True)
    title = db.Column(db.String(500), nullable=False)
    topic = db.Column(db.String(500), nullable=True)
    duration = db.Column(db.String(50), nullable=True)
    resolution = db.Column(db.String(50), nullable=True)
    format = db.Column(db.String(50), nullable=True)

#class Transcription(db.Model):
 #   id = db.Column(db.Integer, primary_key=True)
  #  youtube_url = db.Column(db.String, nullable=False)
   # transcription = db.Column(db.Text, nullable=False)
    #created_at = db.Column(db.DateTime, default=datetime.utcnow)

#class Transcription(db.Model):
 #   id = db.Column(db.Integer, primary_key=True)
  #  youtube_url = db.Column(db.String, nullable=True)
   # transcription = db.Column(db.Text, nullable=False)
    #created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Transcription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    context = db.Column(db.String(500), nullable=True)
    transcription = db.Column(db.Text, nullable=False)
    media_type = db.Column(db.String(50), nullable=False)
    youtube_url = db.Column(db.String(255), nullable=True)
    pdf_file = db.Column(db.String(255), nullable=True)
    image_file = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Transcription {self.id}>'





# Association tables for many-to-many relationships
question_link_association = db.Table('question_link',
    db.Column('question_id', db.Integer, db.ForeignKey('question_new.id'), primary_key=True),
    db.Column('link_id', db.Integer, db.ForeignKey('link_new.id'), primary_key=True)
)

question_video_association = db.Table('question_video',
    db.Column('question_id', db.Integer, db.ForeignKey('question_new.id'), primary_key=True),
    db.Column('video_id', db.Integer, db.ForeignKey('video_new.id'), primary_key=True)
)

question_picture_association = db.Table('question_picture',
    db.Column('question_id', db.Integer, db.ForeignKey('question_new.id'), primary_key=True),
    db.Column('picture_id', db.Integer, db.ForeignKey('picture_new.id'), primary_key=True)
)

question_document_association = db.Table('question_document',
    db.Column('question_id', db.Integer, db.ForeignKey('question_new.id'), primary_key=True),
    db.Column('document_id', db.Integer, db.ForeignKey('document_new.id'), primary_key=True)
)

answer_link_association = db.Table('answer_link',
    db.Column('answer_id', db.Integer, db.ForeignKey('answer_new.id'), primary_key=True),
    db.Column('link_id', db.Integer, db.ForeignKey('link_new.id'), primary_key=True)
)

answer_video_association = db.Table('answer_video',
    db.Column('answer_id', db.Integer, db.ForeignKey('answer_new.id'), primary_key=True),
    db.Column('video_id', db.Integer, db.ForeignKey('video_new.id'), primary_key=True)
)

answer_picture_association = db.Table('answer_picture',
    db.Column('answer_id', db.Integer, db.ForeignKey('answer_new.id'), primary_key=True),
    db.Column('picture_id', db.Integer, db.ForeignKey('picture_new.id'), primary_key=True)
)

answer_document_association = db.Table('answer_document',
    db.Column('answer_id', db.Integer, db.ForeignKey('answer_new.id'), primary_key=True),
    db.Column('document_id', db.Integer, db.ForeignKey('document_new.id'), primary_key=True)
)
