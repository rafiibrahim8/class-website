from sqlalchemy import create_engine, func, Integer, String, Column, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from traceback import format_exc
from threading import Lock
import time
import json
import os

import utils

Base = declarative_base()
lock = Lock()


class WebsiteStuffs(Base):
    __tablename__ = 'website_stuffs'

    key = Column(String, primary_key=True)
    value = Column(String) 

class Users(Base):
    __tablename__ = 'users'
    student_id = Column(String, primary_key=True)
    full_name = Column(String)
    password = Column(String)
    logged_in = Column(Boolean, default=False)

class Courses(Base):
    __tablename__ = 'courses'
    course_code = Column(String, primary_key=True)
    course_name = Column(String)
    course_term = Column(String)
    playlist_url = Column(String)

class Videos(Base):
    __tablename__ = 'videos'
    video_id = Column(String, primary_key=True)
    course_code = Column(String)
    date_as_epoch = Column(Integer)
    section = Column(String)
    video_url = Column(String)

class DBMS():
    def __init__(self, database_path='database.sqlite'):
        db_path = 'sqlite:///' + os.path.expanduser(database_path)
        engine = create_engine(db_path, connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        self.dbSession = sessionmaker(engine)()
    
    def __update_courses_time(self):
        epoch = int(time.time())
        self.update_website_stuff('update_time_42', epoch, commit=False)
        self.update_website_stuff('update_time_41', epoch, commit=False)

    def check_login(self, student_id, password):
        user = self.dbSession.query(Users).filter_by(student_id=student_id).first()
        if user is None:
            return False
        return utils.compare_login_password(user.password, password)        
    
    def get_user_object(self, student_id):
        user = self.dbSession.query(Users).filter_by(student_id=student_id).first()
        return utils.get_user_object(student_id, user.logged_in, user.full_name) if user else None

    def change_login_status(self, student_id, status):
        assert status in ['in','out']
        user = self.dbSession.query(Users).filter_by(student_id=student_id).first()
        user.logged_in = True if status=='in' else False
        DBMS.commit_session(self.dbSession)

    def update_user(self, student_id, password, full_name=''):
        user = self.dbSession.query(Users).filter_by(student_id=student_id).first()
        password = utils.mk_hashed_pwd_from_plain(password)
        if user is None:
            self.dbSession.add(Users(student_id=student_id, password=password, full_name=full_name))
        else:
            user.password = password
            if full_name:
                user.full_name = full_name
        DBMS.commit_session(self.dbSession)
    
    def update_course(self, course_code, course_name, course_term, playlist_url):
        course = self.dbSession.query(Courses).filter_by(course_code=course_code).first()
        if course is None:
            self.dbSession.add(Courses(course_code=course_code, course_name=course_name, course_term=course_term, playlist_url=playlist_url))
        else:
            course.course_name = course_name
            course.course_term = course_term
            course.playlist_url = playlist_url
        
        self.__update_courses_time()
        DBMS.commit_session(self.dbSession)
    
    def delete_video(self, video_id, commit=True):
        video = self.dbSession.query(Videos).filter_by(video_id=video_id).first()
        if video is None:
            return False
        self.dbSession.delete(video)
        if commit:
            self.__update_courses_time()
            DBMS.commit_session(self.dbSession)
        return True
    
    def update_video(self, video_id, course_code, date_as_epoch, section, video_url):
        self.delete_video(video_id, commit=False)
        self.dbSession.add(Videos(video_id=video_id, course_code=course_code, date_as_epoch=date_as_epoch, section=section, video_url=video_url))
        self.__update_courses_time()
        DBMS.commit_session(self.dbSession)

    def get_all_courses(self, term):
        courses_list = []
        courses = self.dbSession.query(Courses).filter_by(course_term=term).all()
        return utils.sql_all_to_json(courses, sort_by='course_code')

    def get_all_videos(self, course_code):
        videos = self.dbSession.query(Videos).filter_by(course_code=course_code).all()
        return utils.sql_all_to_json(videos, sort_by='date_as_epoch')

    def update_website_stuff(self, key, value, commit=True):
        stuff = self.dbSession.query(WebsiteStuffs).filter_by(key=key).first()
        if stuff == None:
            self.dbSession.add(WebsiteStuffs(key=key, value=json.dumps(value)))
        else:
            stuff.value = json.dumps(value)
        if commit:
            DBMS.commit_session(self.dbSession)

    def get_website_stuff(self, key):
        stuff = self.dbSession.query(WebsiteStuffs).filter_by(key=key).first()
        return stuff if stuff == None else json.loads(stuff.value)
    
    @staticmethod
    def commit_session(session):
        with lock:
            DBMS._commit_session_impl(session)
            
    @staticmethod
    def _commit_session_impl(session, retry=True):
        try:
            session.commit()
        except:
            if retry:
                session.rollback()
                DBMS._commit_session_impl(session, False)
            else:
                fmt_exec = format_exc()
                print(fmt_exec)
