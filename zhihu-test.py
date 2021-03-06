#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = '7sDream'

import zhihu
import os
import shutil


def test_question():
    url = 'http://www.zhihu.com/question/24825703'
    question = zhihu.Question(url)

    # 获取该问题的详细描述
    print(question.title)
    # 亲密关系之间要说「谢谢」吗？

    # 获取该问题的详细描述
    print(question.details)
    # 从小父母和大家庭里，.......什么时候不该说"谢谢”？？

    # 获取回答个数
    print(question.answer_num)
    # 630

    # 获取关注该问题的人数
    print(question.follower_num)
    # 4320

    # 获取该问题所属话题
    print(question.topics)
    # ['心理学', '恋爱', '社会', '礼仪', '亲密关系']

    # 获取排名第一的回答的点赞数
    print(question.top_answer.upvote_num)
    # 197

    # 获取排名前十的十个回答的点赞数
    for answer in question.top_i_answers(10):
        print(answer.upvote_num)
    # 197
    # 49
    # 89
    # 425
    # ...

    # 获取所有回答的作者名和点赞数
    for _, answer in zip(range(0, 10), question.answers):
        # do something with answer
        print(answer.author.name, answer.upvote_num)
        pass
    # 小不点儿 197
    # 龙晓航 49
    # 芝士就是力量 89
    # 欧阳忆希 424
    # ...


def test_answer():
    url = 'http://www.zhihu.com/question/24825703/answer/30975949'
    answer = zhihu.Answer(url)

    # 获取答案url
    print(answer.url)

    # 获取该答案所在问题标题
    print(answer.question.title)
    # 关系亲密的人之间要说「谢谢」吗？

    # 获取该答案作者名
    print(answer.author.name)
    # 甜阁下

    # 获取答案赞同数
    print(answer.upvote_num)
    # 1155

    # 获取答案点赞人昵称和感谢赞同提问回答数，并输出三零用户比例
    three_zero_user_num = 0
    for upvoter in answer.upvoters:
        print(upvoter.name, upvoter.upvote_num, upvoter.thank_num,
              upvoter.question_num, upvoter.answer_num)
        if upvoter.is_zero_user():
            three_zero_user_num += 1
    print('\n三零用户比例 %.3f%%' % (three_zero_user_num / answer.upvote_num * 100))
    # ...
    # 空空 23 14 1 7
    # 五月 42 15 3 35
    # 陈半边 6311 1037 3 101
    # 刘柯 3107 969 273 36
    #
    # 三零用户比例 36.364%

    # 获取答案内容的HTML
    print(answer.content)
    # <html>
    # ...
    # </html>

    # 保存HTML
    answer.save(filepath='.')
    # 当前目录下生成 "亲密关系之间要说「谢谢」吗？ - 甜阁下.html"

    # 保存markdown
    answer.save(filepath='.', mode="md")
    # 当前目录下生成 "亲密关系之间要说「谢谢」吗？ - 甜阁下.md"


def test_author():
    url = 'http://www.zhihu.com/people/7sdream'
    author = zhihu.Author(url)

    # 获取用户名称
    print(author.name)
    # 7sDream

    # 获取用户介绍
    print(author.motto)
    # 二次元新居民/软件爱好者/零回答消灭者

    # 获取用户头像地址
    print(author.photo_url)
    # http://pic3.zhimg.com/893fd554c8aa57196d5ab98530ef479a_r.jpg

    # 获取用户得到赞同数
    print(author.upvote_num)
    # 1338

    # 获取用户得到感谢数
    print(author.thank_num)
    # 468

    # 获取用户关注人数
    print(author.followee_num)
    # 82

    # 获取用户关注人
    for _, followee in zip(range(0, 10), author.followees):
        print(followee.name)
    # yuwei
    # falling
    # 伍声
    # bhuztez
    # 段晓晨
    # 冯东
    # ...

    # 获取用户粉丝数
    print(author.follower_num)
    # 303

    # 获得用户粉丝
    for _, follower in zip(range(0, 10), author.followers):
        print(follower.name)
    # yuwei
    # falling
    # 周非
    # 陈泓瑾
    # O1Operator
    # ...

    # 获取用户提问数
    print(author.question_num)
    # 16

    # 获取用户所有提问的标题
    for _, question in zip(range(0, 10), author.questions):
        print(question.title)
    # 用户「松阳先生」的主页出了什么问题？
    # C++运算符重载在头文件中应该如何定义？
    # 亚马逊应用市场的应用都是正版的吗？
    # ...

    # 获取用户答题数
    print(author.answer_num)
    # 247

    # 获取用户所有回答的点赞数
    for _, answer in zip(range(0, 10), author.answers):
        print(answer.upvote_num)
    # 0
    # 5
    # 12
    # 0
    # ...

    # 获取用户文章数
    print(author.post_num)
    # 0

    # 获取用户专栏名
    for column in author.columns:
        print(column.name)
    # 我没有专栏T^T

    # 获取用户收藏夹数
    print(author.collection_num)
    # 5

    # 获取用户收藏夹名
    for collection in author.collections:
        print(collection.name)
    # 教学精品。
    # 可以留着慢慢看～
    # OwO
    # 一句。
    # Read it later

    # 获取用户动态
    for _, act in zip(range(0, 10), author.activities):
        print(act.content.url)
        if act.type == zhihu.ActType.FOLLOW_COLUMN:
            print('%s 在 %s 关注了专栏 %s' %
                  (author.name, act.time, act.column.name))
        elif act.type == zhihu.ActType.FOLLOW_QUESTION:
            print('%s 在 %s 关注了问题 %s' %
                  (author.name, act.time, act.question.title))
        elif act.type == zhihu.ActType.ASK_QUESTION:
            print('%s 在 %s 提了个问题 %s' %
                  (author.name, act.time, act.question.title))
        elif act.type == zhihu.ActType.UPVOTE_POST:
            print('%s 在 %s 赞同了专栏 %s 中 %s 的文章 %s, '
                  '此文章赞同数 %d, 评论数 %d' %
                  (author.name, act.time, act.post.column.name,
                   act.post.author.name, act.post.title, act.post.upvote_num,
                   act.post.comment_num))
        elif act.type == zhihu.ActType.PUBLISH_POST:
            print('%s 在 %s 在专栏 %s 中发布了文章 %s, '
                  '此文章赞同数 %d, 评论数 %d' %
                  (author.name, act.time, act.post.column.name,
                   act.post.title, act.post.upvote_num,
                   act.post.comment_num))
        elif act.type == zhihu.ActType.UPVOTE_ANSWER:
            print('%s 在 %s 赞同了问题 %s 中 %s(motto: %s) 的回答, '
                  '此回答赞同数 %d' %
                  (author.name, act.time, act.answer.question.title,
                   act.answer.author.name, act.answer.author.motto,
                   act.answer.upvote_num))
        elif act.type == zhihu.ActType.ANSWER_QUESTION:
            print('%s 在 %s 回答了问题 %s 此回答赞同数 %d' %
                  (author.name, act.time, act.answer.question.title,
                   act.answer.upvote_num))
        elif act.type == zhihu.ActType.FOLLOW_TOPIC:
            print('%s 在 %s 关注了话题 %s' %
                  (author.name, act.time, act.topic.name))


def test_collection():
    url = 'http://www.zhihu.com/collection/37770691'
    collection = zhihu.Collection(url)

    # 获取收藏夹名字
    print(collection.name)
    # 教学精品。

    # 获取收藏夹关注人数
    print(collection.follower_num)
    # 0

    # 获取收藏夹创建者名字
    print(collection.owner.name)
    # 7sDream

    # 获取收藏夹内所有答案的点赞数
    for _, answer in zip(range(0, 10), collection.answers):
        print(answer.upvote_num)
    # 2561
    # 535
    # 223
    # 258
    # ...

    # 获取收藏夹内所有问题标题
    for _, question in zip(range(0, 10), collection.questions):
        print(question.title)
    # 如何完成标准的平板支撑？
    # 有没有适合 Android 开发初学者的 App 源码推荐？
    # 如何挑逗女朋友？
    # 有哪些计算机的书适合推荐给大一学生？
    # ...


def test_column():
    url = 'http://zhuanlan.zhihu.com/xiepanda'
    column = zhihu.Column(url)

    # 获取专栏名
    print(column.name)
    # 谢熊猫出没注意

    # 获取关注人数
    print(column.follower_num)
    # 73570

    # 获取文章数量
    print(column.post_num)
    # 68

    # 获取所有文章标题
    for _, post in zip(range(0, 10), column.posts):
        print(post.title)
    # 伦敦，再见。London, Pride.
    # 为什么你来到伦敦?——没有抽到h1b
    # “城邦之国”新加坡强在哪？
    # ...


def test_post():
    url = 'http://zhuanlan.zhihu.com/xiepanda/19950456'
    post = zhihu.Post(url)

    # 获取文章地址
    print(post.url)

    # 获取文章标题
    print(post.title)
    # 为什么最近有很多名人，比如比尔盖茨，马斯克、霍金等，让人们警惕人工智能？

    # 获取所在专栏名称
    print(post.column.name)
    # 谢熊猫出没注意

    # 获取作者名称
    print(post.author.name)
    # 谢熊猫君

    # 获取赞同数
    print(post.upvote_num)
    # 18491

    # 获取评论数
    print(post.comment_num)
    # 1748

    # 保存为 markdown
    post.save(filepath='.')
    # 当前目录下生成
    # 为什么最近有很多名人，比如比尔盖茨，马斯克、霍金等，让人们警惕人工智能？ - 谢熊猫君.md

if os.path.exists("test"):
    shutil.rmtree("test")

os.mkdir("test")
os.chdir("test")

test_question()
test_answer()
test_author()
test_collection()
test_column()
test_post()
