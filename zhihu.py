#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""""A parser of zhihu.com with help of bs4 and requests in python3."""

__author__ = '7sDream'

import time
import datetime
import re
import os
import json
import functools
import enum

import requests
from bs4 import BeautifulSoup as _Bs

try:
    __import__('lxml')
    BeautifulSoup = lambda makeup: _Bs(makeup, 'lxml')
except ImportError:
    BeautifulSoup = lambda makeup: _Bs(makeup, 'html.parser')

# Setting
_Zhihu_URL = 'http://www.zhihu.com'
_Login_URL = _Zhihu_URL + '/login/email'
_Captcha_URL_Prefix = _Zhihu_URL + '/captcha.gif?r='
_Get_Profile_Card_URL = 'http://www.zhihu.com/node/MemberProfileCardV2'
_Get_More_Answer_URL = 'http://www.zhihu.com/node/QuestionAnswerListV2'
_Get_More_Followers_URL = 'http://www.zhihu.com/node/ProfileFollowersListV2'
_Get_More_Followees_URL = 'http://www.zhihu.com/node/ProfileFolloweesListV2'
_Cookies_File_Name = 'cookies.json'


# Zhihu Columns API
_Columns_Prefix = 'http://zhuanlan.zhihu.com/'
_Columns_Base_Data = _Columns_Prefix + 'api/columns/{0}'
_Columns_Posts_Data = _Columns_Prefix + 'api/columns/{0}/posts' \
                                        '?limit=10&offset={1}'
_Columns_Post_Data = _Columns_Prefix + 'api/columns/{0}/posts/{1}'

# global var
_session = None
_header = {'X-Requested-With': 'XMLHttpRequest',
           'Referer': 'http://www.zhihu.com',
           'User-Agent': '	Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) '
                         'Gecko/20100101 Firefox/39.0',
           'Host': 'www.zhihu.com'}

_re_question_url = re.compile(r'^http://www\.zhihu\.com/question/\d+/?$')
_re_ans_url = re.compile(
    r'^http://www\.zhihu\.com/question/\d+/answer/\d+/?$')
_re_author_url = re.compile(r'^http://www\.zhihu\.com/people/[^/]+/?$')
_re_collection_url = re.compile(r'^http://www\.zhihu\.com/collection/\d+/?$')
_re_column_url = re.compile(r'^http://zhuanlan\.zhihu\.com/([^/]+)/?$')
_re_post_url = re.compile(r'^http://zhuanlan\.zhihu\.com/([^/]+)/(\d+)/?$')
_re_topic_url = re.compile(r'^http://www\.zhihu\.com/topic/(\d+)/?$')
_re_a2q = re.compile(r'(.*)/a.*')
_re_collection_url_split = re.compile(r'.*(/c.*)')
_re_get_number = re.compile(r'[^\d]*(\d+).*')
_re_del_empty_line = re.compile(r'\n*(.*)\n*')


def _check_soup(attr, soup_type='_make_soup'):
    def real(func):
        @functools.wraps(func)
        def wrapper(self):
            # noinspection PyTypeChecker
            value = getattr(self, attr) if hasattr(self, attr) else None
            if value is None:
                if soup_type == '_make_soup':
                    getattr(self, soup_type)()
                elif self.soup is None:
                    getattr(self, soup_type)()
                value = func(self)
                setattr(self, attr, value)
                return value
            else:
                return value
        return wrapper
    return real


def _save_captcha(url):
    global _session
    r = _session.get(url)
    with open('code.gif', 'wb') as f:
        f.write(r.content)


def _init():
    global _session
    if _session is None:
        _session = requests.session()
        _session.headers.update(_header)
        if os.path.isfile(_Cookies_File_Name):
            with open(_Cookies_File_Name, 'r') as f:
                cookies_dict = json.load(f)
                _session.cookies.update(cookies_dict)
        else:
            print('no cookies file, this may make something wrong.')
            print('if you will run create_cookies or login next, '
                  'please ignore me.')
            _session.post(_Login_URL, data={})
    else:
        raise Exception('call init func two times')


def get_captcha_url():
    """获取验证码网址.

    :return: 验证码网址
    :rtype: str
    """
    return _Captcha_URL_Prefix + str(int(time.time() * 1000))


def login(email='', password='', captcha='', savecookies=True):
    """不使用cookies.json，手动登陆知乎.

    :param str email: 邮箱
    :param str password: 密码
    :param str captcha: 验证码
    :param bool savecookies: 是否要储存cookies文件
    :return: 一个二元素元祖 , 第一个元素代表是否成功（0表示成功），
        如果未成功则第二个元素表示失败原因
    :rtype: (int, dict)
    """
    global _session
    global _header
    data = {'email': email, 'password': password,
            'rememberme': 'y', 'captcha': captcha}
    r = _session.post(_Login_URL, data=data)
    j = r.json()
    c = int(j['r'])
    m = j['msg']
    if c == 0 and savecookies is True:
        with open(_Cookies_File_Name, 'w') as f:
            json.dump(_session.cookies.get_dict(), f)
    return c, m


def create_cookies():
    """创建cookies文件, 请跟随提示操作.

    :return: None
    :rtype: None
    """
    if os.path.isfile(_Cookies_File_Name) is False:
        email = input('email: ')
        password = input('password: ')
        url = get_captcha_url()
        _save_captcha(url)
        print('please check code.gif for captcha')
        captcha = input('captcha: ')
        code, msg = login(email, password, captcha)

        if code == 0:
            print('cookies file created!')
        else:
            print(msg)
        os.remove('code.gif')
    else:
        print('Please delete [' + _Cookies_File_Name + '] first.')


def remove_invalid_char(text):
    """去除字符串中的无效字符，一般用于保存文件时保证文件名的有效性.

    :param str text: 待处理的字符串
    :return: 处理后的字符串
    :rtype: str
    """
    invalid_char_list = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n']
    res = ''
    for char in text:
        if char not in invalid_char_list:
            res += char
    return res


def _parser_author_from_tag(author):
    if author.text == '匿名用户':
        author_name = '匿名用户'
        # noinspection PyTypeChecker
        author_obj = Author(None, author_name, '')
    else:
        author_name = author.contents[3].text
        author_motto = author.strong['title'] \
            if author.strong is not None else ''
        author_url = _Zhihu_URL + author.contents[3]['href']
        photo_url = author.a.img['src'].replace('_s', '_r')
        author_obj = Author(author_url, author_name, author_motto,
                            photo_url=photo_url)
    return author_obj


def _answer_content_process(content):
    del content['class']
    soup = BeautifulSoup(
        '<html><head><meta charset="utf-8"></head><body></body></html>')
    soup.body.append(content)
    no_script_list = soup.find_all("noscript")
    for no_script in no_script_list:
        no_script.extract()
    img_list = soup.find_all(
        "img", class_="origin_image zh-lightbox-thumb lazy")
    for img in img_list:
        new_img = soup.new_tag('img', src=img['data-original'])
        img.replace_with(new_img)
        new_img.insert_after(soup.new_tag('br'))
        if img.previous_sibling is None or img.previous_sibling.name != 'br':
            new_img.insert_before(soup.new_tag('br'))
    useless_list = soup.find_all("i", class_="icon-external")
    for useless in useless_list:
        useless.extract()
    return soup.prettify()


def _text2int(text):
    try:
        return int(text)
    except ValueError:
        if text[-1] == 'K':
            return int(float(text[:-1]) * 1000)
        elif text[-1] == 'W':  # 知乎有没有赞同数用万做单位的回答来着？？先写着吧~
            return int(float(text[:-1]) * 10000)


def _get_path(path, filename, mode, defaultpath, defaultname):
    if path is None:
        path = os.path.join(
            os.getcwd(), remove_invalid_char(defaultpath))
    if filename is None:
        filename = remove_invalid_char(defaultname)
    if os.path.isdir(path) is False:
        os.makedirs(path)
    temp = filename
    i = 0
    while os.path.isfile(os.path.join(path, temp) + '.' + mode):
        i += 1
        temp = filename + str(i)
    return os.path.join(path, temp) + '.' + mode


class Question:

    """问题类，用一个问题的网址来构造对象,其他参数皆为可选."""

    def __init__(self, url, title=None, followers_num=None, answer_num=None):
        """类对象初始化.

        :param str url: 问题地址，形如： http://www.zhihu.com/question/27936038
        :param str title: 可选, 问题标题
        :param int followers_num: 可选，问题关注人数
        :param int answer_num: 可选，问题答案数
        :return: Question对象
        :rtype: Question
        """
        global _session
        if _re_question_url.match(url) is None:
            raise ValueError('URL invalid')
        else:
            if url.endswith('/') is False:
                url += '/'
            self.soup = None
            self.url = url
            self._title = title
            self._answer_num = answer_num
            self._followers_num = followers_num
            self._xsrf = ''

    def _make_soup(self):
        if self.soup is None:
            r = _session.get(self.url)
            self.soup = BeautifulSoup(r.content)
            self._xsrf = self.soup.find(
                'input', attrs={'name': '_xsrf'})['value']

    @property
    @_check_soup('_html')
    def html(self):
        """获取页面HTML源码.

        :return: html源码
        :rtype: str
        """
        return self.soup.prettify()

    @property
    @_check_soup('_title')
    def title(self):
        """获取问题标题.

        :return: title of question
        :rtype: str
        """
        return self.soup.find('h2', class_='zm-item-title') \
            .text.replace('\n', '')

    @property
    @_check_soup('_details')
    def details(self):
        """获取问题详细描述。 **目前实现方法只是直接获取文本，效果不满意……等更新.

        :return: 问题详细描述文本
        :rtype: str
        """
        return self.soup.find("div", id="zh-question-detail").div.text

    @property
    @_check_soup('_answers_num')
    def answer_num(self):
        """获取问题答案数量.

        :return: 答案数量
        :rtype: int
        """
        answer_num_block = self.soup.find('h3', id='zh-question-answer-num')
        # 当0人回答或1回答时，都会找不到 answer_num_block，
        # 通过找答案的赞同数block来判断到底有没有答案。
        # （感谢知乎用户 段晓晨 提出此问题）
        if answer_num_block is None:
            if self.soup.find('span', class_='count') is not None:
                return 1
            else:
                return 0
        return _text2int(answer_num_block['data-num'])

    @property
    @_check_soup('_follower_num')
    def follower_num(self):
        """获取问题关注人数.

        :return: 问题关注人数
        :rtype: int
        """
        follower_num_block = self.soup.find('div', class_='zg-gray-normal')
        # 无人关注时 找不到对应block，直接返回0 （感谢知乎用户 段晓晨 提出此问题）
        if follower_num_block.strong is None:
            return 0
        return _text2int(follower_num_block.strong.text)

    @property
    @_check_soup('_topics')
    def topics(self):
        """获取问题所属话题.

        :return: 问题所属话题列表
        :rtype: list(str)
        """
        topics_list = []
        for topic in self.soup.find_all('a', class_='zm-item-tag'):
            topics_list.append(topic.text.replace('\n', ''))
        return topics_list

    @property
    def answers(self):
        """获取问题的所有答案，返回可迭代生成器.

        :return: 每次迭代返回一个Answer对象， 获取到的Answer对象自带
            所在问题、答主、赞同数量、回答内容四个属性。获取其他属性需要解析另外的网页。
        :rtype: Answer.Iterable
        """
        global _session
        global _header
        self._make_soup()
        new_header = dict(_header)
        new_header['Referer'] = self.url
        params = {"url_token": self.id,
                  'pagesize': '50',
                  'offset': 0}
        data = {'_xsrf': self._xsrf,
                'method': 'next',
                'params': ''}
        for i in range(0, (self.answer_num - 1) // 50 + 1):
            if i == 0:
                # 修正各种建议修改的回答……
                error_answers = self.soup.find_all('div', id='answer-status')
                for each in error_answers:
                    each['class'] = ' zm-editable-content clearfix'
                # 正式处理
                authors = self.soup.find_all(
                    'h3', class_='zm-item-answer-author-wrap')
                urls = self.soup.find_all('a', class_='answer-date-link')
                upvote_nums = self.soup.find_all('span', class_='count')
                contents = self.soup.find_all(
                    'div', class_=' zm-editable-content clearfix')
                for author, url, upvote_num, content in \
                        zip(authors, urls, upvote_nums, contents):
                    author_obj = _parser_author_from_tag(author)
                    url = _Zhihu_URL + url['href']
                    upvote_num = _text2int(upvote_num.text)
                    content = _answer_content_process(
                        self.soup.new_tag(content))
                    yield Answer(url, self, author_obj, upvote_num, content)
            else:
                params['offset'] = i * 50
                data['params'] = json.dumps(params)
                r = _session.post(_Get_More_Answer_URL, data=data,
                                  headers=new_header)
                answer_list = r.json()['msg']
                for answer_html in answer_list:
                    soup = BeautifulSoup(answer_html)
                    # 修正各种建议修改的回答……
                    error_answers = soup.find_all('div', id='answer-status')
                    for each in error_answers:
                        each['class'] = ' zm-editable-content clearfix'
                    answer_url = \
                        self.url + 'answer/' + soup.div['data-atoken']
                    author = soup.find(
                        'h3', class_='zm-item-answer-author-wrap')
                    upvote_num = _text2int(
                        soup.find('span', class_='count').text)
                    content = soup.find(
                        'div', class_=' zm-editable-content clearfix')
                    content = _answer_content_process(content)
                    author_obj = _parser_author_from_tag(author)
                    yield Answer(answer_url, self, author_obj,
                                 upvote_num, content)

    @property
    def top_answer(self):
        """获取排名第一的答案.

        :return: 排名第一的答案对象，能直接获取的属性参见answers方法
        :rtype: Answer
        """
        for a in self.answers:
            return a

    def top_i_answer(self, i):
        """获取排名某一位的答案.

        :param int i: 要获取的答案的排名
        :return: 答案对象，能直接获取的属性参见answers方法
        :rtype: Answer
        """
        for j, a in enumerate(self.answers):
            if j == i - 1:
                return a

    def top_i_answers(self, i):
        """获取排名在前几位的答案.

        :param int i: 获取高位排名答案数量
        :return: 答案对象生成器，这些对象能直接获取的属性参见answers方法
        :rtype: Answer.Iterable
        """
        for j, a in enumerate(self.answers):
            if j <= i - 1:
                yield a

    @property
    def id(self):
        """获取答问题id，就是网址最后那串数字.

        :return: 问题id
        :rtype: int
        """
        return int(re.match(r'.*/(\d+)', self.url).group(1))


class Author:

    """用户类，用用户主页地址作为参数来构造对象，其他参数可选."""

    def __init__(self, url, name=None, motto=None, follower_num=None,
                 question_num=None, answer_num=None, upvote_num=None,
                 thank_num=None, photo_url=None):
        """类对象初始化.

        :param str url: 用户主页地址，形如 http://www.zhihu.com/people/7sdream
        :param str name: 用户名字，可选
        :param str motto: 用户简介，可选
        :param int follower_num: 用户粉丝数，可选
        :param int question_num: 用户提问数，可选
        :param int answer_num: 用户答案数，可选
        :param int upvote_num: 用户获得赞同数，可选
        :param str photo_url: 用户头像地址，可选
        :return: Author对象
        :rtype: Author
        """
        if url is not None:
            if _re_author_url.match(url) is None:
                raise ValueError('URL invalid')
            if url.endswith('/') is False:
                url += '/'
        self.url = url
        self.soup = None
        self.card = None
        self._nav_list = None
        self._name = name
        self._motto = motto
        self._follower_num = follower_num
        self._question_num = question_num
        self._answer_num = answer_num
        self._upvote_num = upvote_num
        self._thank_num = thank_num
        self._photo_url = photo_url
        self._xsrf = None
        self._hash_id = None

    def _make_soup(self):
        if self.soup is None and self.url is not None:
            global _session
            r = _session.get(self.url)
            self.soup = BeautifulSoup(r.content)
            self._nav_list = self.soup.find(
                'div', class_='profile-navbar clearfix').find_all('a')
            self._xsrf = self.soup.find(
                'input', attrs={'name': '_xsrf'})['value']
            div = self.soup.find('div', class_='zm-profile-header-op-btns')
            if div is not None:
                self._hash_id = div.button['data-id']
            else:
                ga = self.soup.find('script', attrs={'data-name': 'ga_vars'})
                self._hash_id = json.loads(ga.text)['user_hash']

    def _make_card(self):
        if self.card is None and self.url is not None:
            global _session
            params = {'url_token': self.id}
            real_params = {'params': json.dumps(params)}
            r = _session.get(_Get_Profile_Card_URL, params=real_params)
            self.card = BeautifulSoup(r.content)

    @property
    def id(self):
        """获取用户id，就是网址最后那一部分.

        :return: 用户id
        :rtype: str
        """
        return re.match(r'^.*/([^/]+)/$', self.url).group(1)

    @property
    @_check_soup('_name')
    def name(self):
        """获取用户名字.

        :return: 用户名字
        :rtype: str
        """
        if self.url is None:
            return '匿名用户'
        return self.soup.find('div', class_='title-section ellipsis').span.text

    @property
    @_check_soup('_motto')
    def motto(self):
        """获取用户自我介绍，由于历史原因，我还是把这个属性叫做motto吧.

        :return: 用户自我介绍
        :rtype: str
        """
        if self.url is None:
            return ''
        else:
            bar = self.soup.find(
                'div', class_='title-section ellipsis')
            if len(bar.contents) < 4:
                return ''
            else:
                return bar.contents[3].text

    @property
    @_check_soup('_photo_url', '_make_card')
    def photo_url(self):
        """获取用户头像图片地址.

        :return: 用户头像url
        :rtype: str
        """
        if self.url is not None:
            if self.soup is not None:
                img = self.soup.find(
                    'img', class_='zm-profile-header-img')['src']
                return img.replace('_l', '_r')
            else:
                assert(self.card is not None)
                return self.card.img['src'].replace('_m', '_l')
        else:
            return 'http://pic1.zhimg.com/da8e974dc_r.jpg'

    @property
    @_check_soup('_followee_num')
    def followee_num(self):
        """获取关注了多少人.

        :return: 关注的人数
        :rtype: int
        """
        if self.url is None:
            return 0
        else:
            number = _text2int(
                self.soup.find(
                    'div',
                    class_='zm-profile-side-following zg-clear').a.strong.text)
            return number

    @property
    @_check_soup('_follower_num')
    def follower_num(self):
        """获取追随者数量，就是关注此人的人数.

        :return: 追随者数量
        :rtype: int
        """
        if self.url is None:
            return 0
        else:
            number = _text2int(
                self.soup.find(
                    'div',
                    class_='zm-profile-side-following zg-clear').find_all(
                    'a')[1].strong.text)
            return number

    @property
    @_check_soup('_upvote_num')
    def upvote_num(self):
        """获取收到的的赞同数量.

        :return: 收到的的赞同数量
        :rtype: int
        """
        if self.url is None:
            return 0
        else:
            number = _text2int(self.soup.find(
                'span', class_='zm-profile-header-user-agree').strong.text)
            return number

    @property
    @_check_soup('_thank_num')
    def thank_num(self):
        """获取收到的感谢数量.

        :return: 收到的感谢数量
        :rtype: int
        """
        if self.url is None:
            return 0
        else:
            number = int(self.soup.find(
                'span', class_='zm-profile-header-user-thanks').strong.text)
            return number

    @property
    @_check_soup('_question_num')
    def question_num(self):
        """获取提问数量.

        :return: 提问数量
        :rtype: int
        """
        if self.url is None:
            return 0
        else:
            return int(self._nav_list[1].span.text)

    @property
    @_check_soup('_answer_num')
    def answer_num(self):
        """获取答案数量.

        :return: 答案数量
        :rtype: int
        """
        if self.url is None:
            return 0
        else:
            return int(self._nav_list[2].span.text)

    @property
    @_check_soup('_post_num')
    def post_num(self):
        """获取专栏文章数量.

        :return: 专栏文章数量
        :rtype: int
        """
        if self.url is None:
            return 0
        else:
            return int(self._nav_list[3].span.text)

    @property
    @_check_soup('_collection_num')
    def collection_num(self):
        """获取收藏夹数量.

        :return: 收藏夹数量
        :rtype: int
        """
        if self.url is None:
            return 0
        else:
            return int(self._nav_list[4].span.text)

    @property
    def questions(self):
        """获取此人问过的所有问题对象，返回生成器.

        :return: 每次迭代返回一个问题对象，获取到的问题对象自带
            标题，关注人数，答案数量三个属性
        :rtype: Question.Iterable
        """
        if self.url is None or self.question_num == 0:
            return
        for page_index in range(1, (self.question_num - 1) // 20 + 2):
            global _session
            html = _session.get(
                self.url + 'asks?page=' + str(page_index)).text
            soup = BeautifulSoup(html)
            question_links = soup.find_all('a', class_='question_link')
            question_datas = soup.find_all(
                'div', class_='zm-profile-section-main')
            for link, data in zip(question_links, question_datas):
                url = _Zhihu_URL + link['href']
                title = link.text
                answer_num = int(
                    _re_get_number.match(data.div.contents[4]).group(1))
                follower_num = int(
                    _re_get_number.match(data.div.contents[6]).group(1))
                q = Question(url, title, follower_num, answer_num)
                yield q

    @property
    def answers(self):
        """获取此人写的所有答案对象，返回生成器.

        :return: 此人的所有答案，能直接获取所在问题，答主，赞同数三个属性。
            其中所在问题对象可以直接获取标题。答主对象即为此对象本身。
        :rtype: Answer.Iterable
        """
        if self.url is None or self.answer_num == 0:
            return
        for page_index in range(1, (self.answer_num - 1) // 20 + 2):
            global _session
            html = _session.get(
                self.url + 'answers?page=' + str(page_index)).text
            soup = BeautifulSoup(html)
            questions = soup.find_all('a', class_='question_link')
            upvotes = soup.find_all('a', class_='zm-item-vote-count')
            for q, upvote in zip(questions, upvotes):
                answer_url = _Zhihu_URL + q['href']
                question_url = _Zhihu_URL + _re_a2q.match(q['href']).group(1)
                question_title = q.text
                upvote = _text2int(upvote.text)
                yield Answer(answer_url,
                             Question(question_url, question_title),
                             self, upvote)

    @property
    def followers(self):
        """获取此关注此用户的人.

        :return: 关注此用户的人的生成器
        :rtype: Author.Iterable
        """
        for x in self._follow_ee_ers('er'):
            yield x

    @property
    def followees(self):
        """获取此用户关注的人.

        :return: 用户关注的人的生成器
        :rtype: Author.Iterable
        """
        for x in self._follow_ee_ers('ee'):
            yield x

    def _follow_ee_ers(self, t):
        if self.url is None:
            return
        if t == 'er':
            all_number = self.follower_num
            request_url = _Get_More_Followers_URL
        else:
            all_number = self.followee_num
            request_url = _Get_More_Followees_URL
        if all_number == 0:
            return
        global _session
        params = {"order_by": "created", "offset": 0, "hash_id": self._hash_id}
        data = {'_xsrf': self._xsrf, 'method': 'next', 'params': ''}
        for i in range(0, all_number, 20):
            params['offset'] = i
            data['params'] = json.dumps(params)
            res = _session.post(request_url, data=data)
            for html in res.json()['msg']:
                soup = BeautifulSoup(html)
                h2 = soup.find('h2')
                author_name = h2.a.text
                author_url = h2.a['href']
                author_motto = soup.find('div', class_='zg-big-gray').text
                author_photo = soup.a.img['src'].replace('_m', '_r')
                numbers = [_text2int(_re_get_number.match(x.text).group(1))
                           for x in soup.find_all('a', target='_blank')]
                yield Author(author_url, author_name, author_motto, *numbers,
                             thank_num=None, photo_url=author_photo)

    @property
    def collections(self):
        """获取此人收藏夹对象集合，返回生成器.

        :return: 此人所有的收藏夹， 能直接获取拥有者，收藏夹名字，关注人数三个属性。
            其中拥有者即为此对象本身。
        :rtype: Collection.Iterable
        """
        if self.url is None or self.collection_num == 0:
            return
        else:
            global _session
            collection_num = self.collection_num
            for page_index in range(1, (collection_num - 1) // 20 + 2):
                html = _session.get(
                    self.url + 'collections?page=' + str(page_index)).text
                soup = BeautifulSoup(html)
                collections_names = soup.find_all(
                    'a', class_='zm-profile-fav-item-title')
                collection_follower_nums = soup.find_all(
                    'div', class_='zm-profile-fav-bio')
                for c, f in zip(collections_names, collection_follower_nums):
                    c_url = _Zhihu_URL + c['href']
                    c_name = c.text
                    c_fn = int(_re_get_number.match(f.contents[2]).group(1))
                    yield Collection(c_url, self, c_name, c_fn)

    @property
    def columns(self):
        """获取此人专栏，返回生成器.

        :return: 此人所有的专栏，能直接获取拥有者，名字，网址，文章数，关注人数。
        :rtype: Column.Iterable
        """
        if self.url is None or self.post_num == 0:
            return
        global _session
        soup = BeautifulSoup(_session.get(self.url + 'posts').text)
        column_tags = soup.find_all('div', class_='column')
        for column_tag in column_tags:
            name = column_tag.div.a.span.text
            url = column_tag.div.a['href']
            follower_num = _text2int(_re_get_number.match(
                column_tag.div.div.a.text).group(1))
            footer = column_tag.find('div', class_='footer')
            if footer is None:
                post_num = 0
            else:
                post_num = _text2int(
                    _re_get_number.match(footer.a.text).group(1))
            yield Column(url, name, follower_num, post_num)

    @property
    def activities(self):
        """获取用户的最近动态.

        :return: 最近动态生成器，根据不同的动态类型提供不同的成员
        :rtype: Activity.Iterable
        """
        if self.url is None:
            return
        self._make_soup()
        global _session
        gotten_feed_num = 20
        start = '0'
        while gotten_feed_num == 20:
            data = {'_xsrf': self._xsrf, 'start': start}
            res = _session.post(self.url + 'activities', data=data)
            gotten_feed_num = res.json()['msg'][0]
            soup = BeautifulSoup(res.json()['msg'][1])
            acts = soup.find_all(
                'div', class_='zm-profile-section-item zm-item clearfix')
            start = acts[-1]['data-time'] if len(acts) > 0 else 0
            for act in acts:
                act_time = datetime.datetime.fromtimestamp(
                    int(act['data-time']))
                useless_tag = act.div.find('a', class_='zg-link')
                if useless_tag is not None:
                    useless_tag.extract()
                type_string = next(act.div.stripped_strings)
                if type_string in ['赞同了', '在']:    # 赞同文章 or 发表文章
                    act_type = ActType.UPVOTE_POST \
                        if type_string == '赞同了' else ActType.PUBLISH_POST

                    column_url = act.find('a', class_='column_link')['href']
                    column_name = act.find('a', class_='column_link').text
                    column = Column(column_url, column_name)
                    try:
                        author_tag = act.find('div', class_='author-info')
                        author_url = _Zhihu_URL + author_tag.a['href']
                        author_info = list(author_tag.stripped_strings)
                        author_name = author_info[0]
                        author_motto = author_info[1] \
                            if len(author_info) > 1 else ''
                        photo_tag = act.div.a.img
                        photo_url = photo_tag['src'].replace('_s', '_r') \
                            if photo_tag is not None else None
                    except TypeError:
                        author_url = None
                        author_name = '匿名用户'
                        author_motto = ''
                        photo_url = None
                    author = Author(author_url, author_name, author_motto,
                                    photo_url=photo_url)
                    post_url = act.find('a', class_='post-link')['href']
                    post_title = act.find('a', class_='post-link').text
                    post_comment_num, post_upvote_num = self._parse_answer(act)
                    post = Post(post_url, column, author, post_title,
                                post_upvote_num, post_comment_num)

                    yield Activity(act_type, act_time, post=post)
                elif type_string == '关注了专栏':
                    act_type = ActType.FOLLOW_COLUMN
                    column = Column(act.div.a['href'], act.div.a.text)
                    yield Activity(act_type, act_time, column=column)
                elif type_string == '关注了问题':
                    act_type = ActType.FOLLOW_QUESTION
                    question = Question(
                        _Zhihu_URL + act.div.a['href'], act.div.a.text)
                    yield Activity(act_type, act_time, question=question)
                elif type_string == '提了一个问题':
                    act_type = ActType.ASK_QUESTION
                    question = Question(
                        _Zhihu_URL + act.div.contents[3]['href'],
                        list(act.div.children)[3].text)
                    yield Activity(act_type, act_time, question=question)
                elif type_string == '赞同了回答':
                    act_type = ActType.UPVOTE_ANSWER
                    question_url = _Zhihu_URL + _re_a2q.match(
                        act.div.a['href']).group(1)
                    question_title = act.div.a.text
                    question = Question(question_url, question_title)

                    try_find_author = act.find('h3').find_all(
                        'a', href=re.compile('^/people/[^/]*$'))
                    if len(try_find_author) == 0:
                        author_url = None
                        author_name = '匿名用户'
                        author_motto = ''
                        photo_url = None
                    else:
                        try_find_author = try_find_author[-1]
                        author_url = _Zhihu_URL + try_find_author['href']
                        author_name = try_find_author.text
                        try_find_motto = try_find_author.parent.strong
                        if try_find_motto is None:
                            author_motto = ''
                        else:
                            author_motto = try_find_motto['title']
                        photo_url = try_find_author.parent.a.img['src']\
                            .replace('_s', '_r')
                    author = Author(author_url, author_name, author_motto,
                                    photo_url=photo_url)

                    answer_url = _Zhihu_URL + act.div.a['href']
                    answer_comment_num, answer_upvote_num = \
                        Author._parse_answer(act)
                    answer = Answer(answer_url, question, author,
                                    answer_upvote_num)

                    yield Activity(act_type, act_time, answer=answer)
                elif type_string == '回答了问题':
                    act_type = ActType.ANSWER_QUESTION
                    question_url = _Zhihu_URL + _re_a2q.match(
                        act.div.find_all('a')[-1]['href']).group(1)
                    question_title = act.div.find_all('a')[-1].text
                    question = Question(question_url, question_title)

                    answer_url = _Zhihu_URL + \
                        act.div.find_all('a')[-1]['href']
                    answer_comment_num, answer_upvote_num = \
                        Author._parse_answer(act)
                    answer = Answer(answer_url, question, self,
                                    answer_upvote_num)

                    yield Activity(act_type, act_time, answer=answer)
                elif type_string == '关注了话题':
                    act_type = ActType.FOLLOW_TOPIC
                    topic_url = _Zhihu_URL + act.div.a['href']
                    topic_name = act.div.a['title']

                    yield Activity(act_type, act_time,
                                   topic=Topic(topic_url, topic_name))

    def is_zero_user(self):
        """返回当前用户是否为三零用户，其实是四零，分别为： 赞同0，感谢0，提问0，回答0.

        :return: 是否是三零用户
        :rtype: bool
        """
        return self.upvote_num + self.thank_num + \
            self.question_num + self.answer_num == 0

    @staticmethod
    def _parse_answer(act):
        upvote_num = _text2int(act.find(
            'a', class_='zm-item-vote-count')['data-votecount'])
        comment = act.find('a', class_='toggle-comment')
        comment_text = next(comment.stripped_strings)
        comment_num_match = _re_get_number.match(comment_text)
        comment_num = _text2int(comment_num_match.group(1)) \
            if comment_num_match is not None else 0
        return comment_num, upvote_num


class Answer:

    """答案类，用一个答案的网址作为参数构造对象，其他参数可选."""

    def __init__(self, url, question=None, author=None, upvote_num=None,
                 content=None):
        """类对象初始化.

        :param str url: 答案网址，形如
            http://www.zhihu.com/question/28297599/answer/40327808
        :param Question question: 答案所在的问题对象，自己构造对象不需要此参数
        :param Author author: 答案的回答者对象，同上。
        :param int upvote_num: 此答案的赞同数量，同上。
        :param str content: 此答案内容，同上。
        :return: 答案对象。
        :rtype: Answer
        """
        if _re_ans_url.match(url) is None:
            raise ValueError('URL invalid')
        if url.endswith('/') is False:
            url += '/'
        self.url = url
        self.soup = None
        self._question = question
        self._author = author
        self._upvote_num = upvote_num
        self._content = content

    def _make_soup(self):
        if self.soup is None:
            r = _session.get(self.url)
            self.soup = BeautifulSoup(r.content)
            self._aid = self.soup.find(
                'div', class_='zm-item-answer')['data-aid']

    @property
    @_check_soup('_html')
    def html(self):
        """获取网页html源码……话说我写这个属性是为了干啥来着.

        :return: 网页源码
        :rtype: str
        """
        return self.soup.prettify()

    @property
    @_check_soup('_author')
    def author(self):
        """获取答案作者对象.

        :return: 答案作者对象
        :rtype: Author
        """
        author = self.soup.find('h3', class_='zm-item-answer-author-wrap')
        return _parser_author_from_tag(author)

    @property
    @_check_soup('_question')
    def question(self):
        """获取答案所在问题对象.

        :return: 答案所在问题
        :rtype: Question
        """
        question_link = self.soup.find(
            "h2", class_="zm-item-title zm-editable-content").a
        url = _Zhihu_URL + question_link["href"]
        title = question_link.text
        followers_num = _text2int(self.soup.find(
            'div', class_='zh-question-followers-sidebar').div.a.strong.text)
        answers_num = _text2int(_re_get_number.match(self.soup.find(
            'div', class_='zh-answers-title').h3.a.text).group(1))
        return Question(url, title, followers_num, answers_num)

    @property
    @_check_soup('_upvote_num')
    def upvote_num(self):
        """获取答案赞同数量.

        :return: 答案赞同数量
        :rtype: int
        """
        return _text2int(self.soup.find('span', class_='count').text)

    @property
    def upvoters(self):
        """获取答案点赞用户，返回迭代器.

        :return: 点赞用户迭代器
        :rtype: Author.Iterable
        """
        global _session
        self._make_soup()
        next_req = '/answer/' + self._aid + '/voters_profile'
        while next_req != '':
            data = _session.get(_Zhihu_URL + next_req).json()
            next_req = data['paging']['next']
            for html in data['payload']:
                soup = BeautifulSoup(html)
                author_tag = soup.find('div', class_='body')
                if author_tag.string is None:
                    author_name = author_tag.div.a['title']
                    author_url = author_tag.div.a['href']
                    author_motto = author_tag.div.span.text
                    photo_url = soup.a.img['src'].replace('_m', '_r')
                    numbers_tag = soup.find_all('li')
                    numbers = [int(_re_get_number.match(x.get_text()).group(1))
                               for x in numbers_tag]
                else:
                    author_url = None
                    author_name = '匿名用户'
                    author_motto = ''
                    numbers = [None] * 4
                    photo_url = None
                # noinspection PyTypeChecker
                yield Author(author_url, author_name, author_motto, None,
                             numbers[2], numbers[3], numbers[0], numbers[1],
                             photo_url)

    @property
    @_check_soup('_content')
    def content(self):
        """返回答案内容，以处理过的Html代码形式.

        :return: 答案内容
        :rtype: str
        """
        content = self.soup.find('div', class_=' zm-editable-content clearfix')
        content = _answer_content_process(content)
        return content

    def save(self, filepath=None, filename=None, mode="html"):
        """保存答案为Html文档或markdown文档.

        :param str filepath: 要保存的文件所在的绝对目录或相对目录，
            不填为当前目录下以问题标题命名的目录, 设为"."则为当前目录
        :param str filename: 要保存的文件名，
            不填则默认为 所在问题标题 - 答主名.html/md
            如果文件已存在，自动在后面加上数字区分。
            自定义文件名时请不要输入后缀 .html 或 .md
        :return: None
        :rtype: None
        """
        if mode not in ["html", "md", "markdown"]:
            return
        file = _get_path(filepath, filename, mode,
                         self.question.title,
                         self.question.title + '-' + self.author.name)
        with open(file, 'wb') as f:
            if mode == "html":
                f.write(self.content.encode('utf-8'))
            else:
                import html2text

                h2t = html2text.HTML2Text()
                h2t.body_width = 0
                f.write(h2t.handle(self.content).encode('utf-8'))

    @property
    def id(self):
        """答案的ID，也就是网址最后的那串数字.

        :return: 答案ID
        :rtype: int
        """
        print(self.url)
        return int(re.match(r'.*/(\d+)/$', self.url).group(1))


class Collection:

    """收藏夹类，用收藏夹主页网址为参数来构造对象."""

    def __init__(self, url, owner=None, name=None, follower_num=None):
        """类对象初始化.

        :param str url: 收藏夹主页网址，必须
        :param Author owner: 收藏夹拥有者，可选，最好不要自己设置
        :param str name: 收藏夹标题，可选，可以自己设置
        :param int follower_num: 收藏夹关注人数，可选，可以自己设置
        :return: 收藏夹对象
        :rtype: Collection
        """
        if _re_collection_url.match(url) is None:
            raise ValueError('URL invalid')
        else:
            if url.endswith('/') is False:
                url += '/'
            self.url = url
            self.soup = None
            self._name = name
            self._owner = owner
            self._follower_num = follower_num

    def _make_soup(self):
        if self.soup is None:
            global _session
            self.soup = BeautifulSoup(_session.get(self.url).text)

    @property
    @_check_soup('_name')
    def name(self):
        """获取收藏夹名字.

        :return: 收藏夹名字
        :rtype: str
        """
        return _re_del_empty_line.match(
            self.soup.find('h2', id='zh-fav-head-title').text).group(1)

    @property
    @_check_soup('_owner')
    def owner(self):
        """获取收藏夹拥有者，返回Author对象.

        :return: 收藏夹拥有者
        :rtype: Author
        """
        a = self.soup.find('h2', class_='zm-list-content-title').a
        name = a.text
        url = _Zhihu_URL + a['href']
        motto = self.soup.find(
            'div', id='zh-single-answer-author-info').div.text
        photo_url = self.soup.find(
            'img', class_='zm-list-avatar-medium')['src'].replace('_m', '_r')
        return Author(url, name, motto, photo_url=photo_url)

    @property
    @_check_soup('_follower_num')
    def follower_num(self):
        """获取关注此收藏夹的人数.

        :return: 关注此收藏夹的人数
        :rtype: int
        """
        href = _re_collection_url_split.match(self.url).group(1)
        return int(self.soup.find('a', href=href + 'followers').text)

    @property
    def questions(self):
        """获取收藏夹内所有问题对象.

        :return: 收藏夹内所有问题，以生成器形式返回
        :rtype: Question.Iterable
        """
        self._make_soup()
        # noinspection PyTypeChecker
        for question in Collection._page_get_questions(self.soup):
            yield question
        i = 2
        while True:
            global _session
            soup = BeautifulSoup(_session.get(
                self.url[:-1] + '?page=' + str(i)).text)
            for question in self._page_get_questions(soup):
                if question == 0:
                    return
                yield question
            i += 1

    @property
    def answers(self):
        """获取收藏夹内所有答案对象.

        :return: 收藏夹内所有答案，以生成器形式返回
        :rtype: Answer.Iterable
        """
        self._make_soup()
        # noinspection PyTypeChecker
        for answer in Collection._page_get_answers(self.soup):
            yield answer
        i = 2
        while True:
            global _session
            soup = BeautifulSoup(_session.get(
                self.url[:-1] + '?page=' + str(i)).text)
            for answer in Collection._page_get_answers(soup):
                if answer == 0:
                    return
                yield answer
            i += 1

    @staticmethod
    def _page_get_questions(soup):
        question_tags = soup.find_all("div", class_="zm-item")
        if len(question_tags) == 0:
            yield 0
            return
        else:
            for question_tag in question_tags:
                if question_tag.h2 is not None:
                    question_title = question_tag.h2.a.text
                    question_url = _Zhihu_URL + question_tag.h2.a['href']
                    yield Question(question_url, question_title)

    @staticmethod
    def _page_get_answers(soup):
        answer_tags = soup.find_all("div", class_="zm-item")
        if len(answer_tags) == 0:
            yield 0
            return
        else:
            question = None
            for tag in answer_tags:
                # 判断是否是'建议修改的回答'等情况
                url_tag = tag.find('a', class_='answer-date-link')
                if url_tag is None:
                    reason = tag.find('div', id='answer-status').p.text
                    print("pass a answer, reason %s ." % reason)
                    continue
                author_name = '匿名用户'
                author_motto = ''
                author_url = None
                if tag.h2 is not None:
                    question_title = tag.h2.a.text
                    question_url = _Zhihu_URL + tag.h2.a['href']
                    question = Question(question_url, question_title)
                answer_url = _Zhihu_URL + url_tag['href']
                h3 = tag.find('h3')
                if h3.text != '匿名用户':
                    author_url = _Zhihu_URL + h3.a['href']
                    author_name = h3.a.text
                    if h3.strong is not None:
                        author_motto = tag.find('h3').strong['title']
                author = Author(author_url, author_name, author_motto)
                upvote = _text2int(tag.find(
                    'a', class_='zm-item-vote-count').text)
                answer = Answer(answer_url, question, author, upvote)
                yield answer


class Column:

    """专栏类，用专栏网址为参数来构造对象."""

    def __init__(self, url, name=None, follower_num=None,
                 post_num=None):
        """类对象初始化.

        :param str url: 专栏网址
        :param str name: 专栏名
        :param int follower_num: 关注者数量
        :param int post_num: 文章数量
        :return: 专栏对象
        :rtype: Column
        """
        match = _re_column_url.match(url)
        if match is None:
            raise ValueError('URL invalid')
        else:
            self._in_name = match.group(1)
        if url.endswith('/') is False:
            url += '/'
        self.url = url
        self.soup = None
        self._name = name
        self._follower_num = follower_num
        self._post_num = post_num

    def _make_soup(self):
        global _session
        if self.soup is None:
            assert isinstance(_session, requests.Session)
            origin_host = _session.headers.get('Host')
            _session.headers.update(Host='zhuanlan.zhihu.com')
            res = _session.get(_Columns_Base_Data.format(self._in_name))
            _session.headers.update(Host=origin_host)
            self.soup = res.json()

    @property
    @_check_soup('_name')
    def name(self):
        """获取专栏名称.

        :return: 专栏名称
        :rtype: str
        """
        return self.soup['name']

    @property
    @_check_soup('_follower_num')
    def follower_num(self):
        """获取关注人数.

        :return: 关注人数
        :rtype: int
        """
        return _text2int(self.soup['followersCount'])

    @property
    @_check_soup('_post_num')
    def post_num(self):
        """获取专栏文章数.

        :return: 专栏文章数
        :rtype: int
        """
        return _text2int(self.soup['postsCount'])

    @property
    def posts(self):
        """获取专栏的所有文章.

        :return: 专栏所有文章的迭代器
        :rtype: Post.Iterable
        """
        global _session
        origin_host = _session.headers.get('Host')
        for offset in range(0, (self.post_num - 1) // 10 + 1):
            _session.headers.update(Host='zhuanlan.zhihu.com')
            res = _session.get(
                _Columns_Posts_Data.format(self._in_name, offset * 10))
            soup = res.json()
            _session.headers.update(Host=origin_host)
            for post in soup:
                url = _Columns_Prefix + post['url'][1:]
                template = post['author']['avatar']['template']
                photo_id = post['author']['avatar']['id']
                photo_url = template.format(id=photo_id, size='r')
                author = Author(post['author']['profileUrl'],
                                post['author']['name'],
                                post['author']['bio'], photo_url=photo_url)
                title = post['title']
                upvote_num = post['likesCount']
                comment_num = post['commentsCount']
                yield Post(url, self, author, title, upvote_num, comment_num)


class Post:

    """知乎专栏的文章类，以文章网址为参数构造对象."""

    def __init__(self, url, column=None, author=None, title=None,
                 upvote_num=None, comment_num=None):
        """类对象初始化.

        :param str url: 文章所在URL
        :param Column column: 所属专栏
        :param Author author: 文章作者
        :param str title: 文章标题
        :param int upvote_num: 赞同数
        :param int comment_num: 评论数
        :return: Post
        """
        match = _re_post_url.match(url)
        if match is None:
            raise ValueError('URL invalid')
        if url.endswith('/') is False:
            url += '/'
        self.url = url
        self._column_in_name = match.group(1)
        self._slug = match.group(2)
        self._column = column
        self._author = author
        self._title = title
        self._upvote_num = upvote_num
        self._comment_num = comment_num
        self.soup = None

    def _make_soup(self):
        if self.soup is None:
            global _session
            origin_host = _session.headers.get('Host')
            _session.headers.update(Host='zhuanlan.zhihu.com')
            self.soup = _session.get(
                _Columns_Post_Data.format(
                    self._column_in_name, self._slug)).json()
            _session.headers.update(Host=origin_host)

    @property
    @_check_soup('_column')
    def column(self):
        """获取文章所在专栏.

        :return: 文章所在专栏
        :rtype: Column
        """
        url = _Columns_Prefix + self.soup['column']['slug']
        name = self.soup['column']['name']
        return Column(url, name)

    @property
    @_check_soup('_author')
    def author(self):
        """获取文章作者.

        :return: 文章作者
        :rtype: Author
        """
        url = self.soup['author']['profileUrl']
        name = self.soup['author']['name']
        motto = self.soup['author']['bio']
        template = self.soup['author']['avatar']['template']
        photo_id = self.soup['author']['avatar']['id']
        photo_url = template.format(id=photo_id, size='r')
        return Author(url, name, motto, photo_url=photo_url)

    @property
    @_check_soup('_title')
    def title(self):
        """获取文章标题.

        :return: 文章标题
        :rtype: str
        """
        return self.soup['title']

    @property
    @_check_soup('_upvote_num')
    def upvote_num(self):
        """获取文章赞同数量.

        :return: 文章赞同数
        :rtype: int
        """
        return _text2int(self.soup['likesCount'])

    @property
    @_check_soup('_comment_num')
    def comment_num(self):
        """获取评论数量.

        :return: 评论数量
        :rtype: int
        """
        return self.soup['commentsCount']

    def save(self, filepath=None, filename=None):
        """将文章保存为 markdown 格式.

        :param str filepath: 要保存的文件所在的绝对目录或相对目录，
            不填为当前目录下以专栏名命名的目录, 设为"."则为当前目录
        :param str filename: 要保存的文件名，不填则默认为 文章标题 - 作者名.md
            如果文件已存在，自动在后面加上数字区分。
            自定义参数时请不要输入扩展名 .md
        :return:
        """
        self._make_soup()
        file = _get_path(filepath, filename, 'md',
                         self.column.name,
                         self.title + ' - ' + self.author.name)
        with open(file, 'wb') as f:
            import html2text

            h2t = html2text.HTML2Text()
            h2t.body_width = 0
            f.write(h2t.handle(self.soup['content']).encode('utf-8'))


class ActType(enum.Enum):

    """用于表示用户动态的类型.

    ANSWER_QUESTION :回答了一个问题 提供属性 answer
    UPVOTE_ANSWER   :赞同了一个回答 提供属性 answer
    ASK_QUESTION    :提出了一个问题 提供属性 question
    FOLLOW_QUESTION :关注了一个问题 提供属性 question
    UPVOTE_POST     :赞同了一篇文章 提供属性 post
    FOLLOW_COLUMN   :关注了一个专栏 提供属性 column
    FOLLOW_TOPIC    :关注了一个话题 提供属性 topic
    PUBLISH_POST    :发表了一篇文章 提供属性 post
    """

    ANSWER_QUESTION = 1
    UPVOTE_ANSWER = 2
    ASK_QUESTION = 4
    FOLLOW_QUESTION = 8
    UPVOTE_POST = 16
    FOLLOW_COLUMN = 32
    FOLLOW_TOPIC = 64
    PUBLISH_POST = 128


class Activity:

    """用户动态类，不建议手动使用，请使用Author.activities获取."""

    def __init__(self, act_type, act_time, **kwarg):
        """类对象初始化.

        :param ActType act_type: 动态类型
        :param datatime.datatime act_time: 动态发生时间
        :return: 活动对象
        :rtype: Activity
        """
        if not isinstance(act_type, ActType):
            raise ValueError('invalid activity type')
        if len(kwarg) != 1:
            raise ValueError('except one kwarg (%d given)' % len(kwarg))
        self.type = act_type
        self.time = act_time
        for k, v in kwarg.items():
            self._attr = k
            setattr(self, k, v)

    @property
    def content(self):
        """获取此对象中能提供的那个属性，对应表请查看ActType类.

        :return: 对象提供的对象
        :rtype: Author or Question or Answer or Topic or Column or Post
        """
        return getattr(self, self._attr)


class Topic:

    """话题类，传入话题网址构造对象."""

    def __init__(self, url, name=None):
        """类对象初始化.

        :param url: 话题地址
        :param name: 话题名称
        :return: Topic
        """
        if _re_topic_url.match(url) is None:
            raise ValueError('URL invalid')
        if url.endswith('/') is False:
            url += '/'
        self.url = url
        self._name = name
        self.soup = None

    def _make_soup(self):
        if self.soup is None:
            global _session
            self.soup = BeautifulSoup(_session.get(self.url).content)

    @property
    @_check_soup('_name')
    def name(self):
        """获取话题名称.

        :return: 话题名称
        :rtype: str
        """
        return self.soup.find('h1').text


_init()
