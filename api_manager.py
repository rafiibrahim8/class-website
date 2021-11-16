# Shitty API manager, will be updated later

from traceback import print_exc

class API:
    def __init__(self, dbms):
        self.__dbms = dbms
        self.__func_map = {
            'add_user': self.__add_user,
            'add_course': self.__add_course,
            'add_video': self.__add_video
        }
    
    def __add_user(self, data):
        self.__dbms.update_user(data['student_id'], data['password'], data['full_name'])

    def __add_course(self, data):
        self.__dbms.update_course(data['course_code'], data['course_name'], data['course_term'], data['playlist_url'])
    
    def __add_video(self, data):
        self.__dbms.update_video(data['video_id'], data['course_code'], data['date_as_epoch'], data['section'], data['video_url'])

    def handle_request(self, data):
        func = self.__func_map.get(data['type'])
        try:
            func(data)
            return 'OK', 200
        except:
            print_exc()
            return 'Bad request', 403

