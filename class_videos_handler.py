import datetime
import time

class CVHandler:
    __date_format = '%B %d, %Y'

    def __init__(self, dbms):
        self.__dbms = dbms
        self.__cache41 = None
        self.__cache41time = 0
        self.__cache42 = None
        self.__cache42time = 0
    
    @staticmethod
    def __mk_playlists(courses):
        playlist = list()
        for i in courses:
            playlist.append({'name': i['course_name'], 'url': i['playlist_url']})
        return playlist
    
    @staticmethod
    def __get_section_names(videos):
        sections = set()
        for i in videos:
            if i.get('section'):
                sections.add(i.get('section'))
        sections = list(sections)
        sections.sort()
        return sections

    @staticmethod
    def __mk_sectionless_video_list(videos):
        v_list = list()
        for v in videos:
            date = datetime.datetime.fromtimestamp(v['date_as_epoch'], datetime.timezone.utc).strftime(CVHandler.__date_format)
            v_list.append({'date': date, 'url': v['video_url']})
        return v_list

    @staticmethod
    def __mk_sectioned_video_list(videos, sections):
        v_list = list()
        for section in sections:
            vdos = filter(lambda x: x['section'] == section, videos)
            v_list.append({'name': section, 'videos': CVHandler.__mk_sectionless_video_list(vdos)})
        return v_list

    @staticmethod
    def __format_video_list(videos):
        sections = CVHandler.__get_section_names(videos)
        if sections:
            return True, CVHandler.__mk_sectioned_video_list(videos, sections)
        return False, CVHandler.__mk_sectionless_video_list(videos)

    def __mk_subject_pairs(self, courses):
        pairs = list()
        p = list()
        for course in courses:
            if course['course_code'].lower().startswith('x'):
                continue
            videos = self.__dbms.get_all_videos(course['course_code'])
            has_section, v_list = self.__format_video_list(videos)
            if has_section:
                p.append({'name': course['course_name'], 'code': course['course_code'], 'sections': v_list})
            else:
                p.append({'name': course['course_name'], 'code': course['course_code'], 'videos': v_list})
            if len(p) == 2:
                pairs.append([ i for i in p])
                p = list()
        if p:
            pairs.append([ i for i in p])
        return pairs

    def get41data(self):
        update_time = self.__dbms.get_website_stuff('update_time_41')
        if update_time and update_time <= self.__cache41time and self.__cache41:
            return self.__cache41
        
        data = {'title': '4-I Videos', 'video42url': '/', 'video41url': '#'}
        courses = self.__dbms.get_all_courses('4-I')
        
        data['playlist'] = {'name': 'playlist41', 'list': self.__mk_playlists(courses)}
        data['subjects'] = self.__mk_subject_pairs(courses)

        self.__cache41 = data
        self.__cache41time = int(time.time())
        
        return data

    def get42data(self):
        update_time = self.__dbms.get_website_stuff('update_time_42')
        if update_time and update_time <= self.__cache42time and self.__cache42:
            return self.__cache42
        
        data = {'title': '4-II Videos', 'video42url': '#', 'video41url': '/41-videos'}
        courses = self.__dbms.get_all_courses('4-II')
        
        data['playlist'] = {'name': 'playlist42', 'list': self.__mk_playlists(courses)}
        data['subjects'] = self.__mk_subject_pairs(courses)

        self.__cache42 = data
        self.__cache42time = int(time.time())
        
        return data
