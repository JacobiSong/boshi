from .base_model import BaseModel
import sys
sys.path.append("QuestionAnswering")
import logging
import json
from collections import defaultdict

samples = ['当进垛输送和整形输送同时运转，将垛盘送到整形输送时，整形输送机何时停止运转？',
'套膜机控制柜操作面板有哪些控制元件组成？','触摸屏中的自动画面中的多状态指示灯共有几种状态？',
'套膜控制系统采用多少个变频，分别控制哪些电机','套膜机调偏机构由什么元件组成？',
'高位码垛机的托盘仓包括哪四个部分？','高位码垛机的转位机构包括哪三个部分？','低位码垛机的转位机构包括哪三个部分？',
'低位码垛机：如果进入编组机的料袋是一组中的最后一袋，编组机何时停止运转？','低位码垛机：当码垛最后一层完成，开始排垛前，升降机会上升到什么位置？',
'低位码垛机： 码垛机由停止状态进入自动运行状态时，推袋小车应处于什么位置，推袋板处于什么状态？','低位码垛机： 如何调整编组机料袋间距？']

class DbqaModel(BaseModel):

    def __init__(self, data_file):
        super(DbqaModel).__init__()
        with open(data_file, 'r', encoding='utf-8') as f_open:
            data = json.load(f_open)
        self.titles = [title for title, _ in data.items()]
        self.data = data
        # print(data)

    def question_title_classify(self, question):
        key_words1 = ['低位码垛机','低位码垛']
        key_words2 = ['高位码垛机', '高位码垛', '码垛机'] 
        key_words3 = ['套膜机', '套膜控制系统', '拉伸套膜机']
        key_words4 = ['称重系统','测重系统','测重','称重','称量']
        key_words5 = ['除尘','去尘']
        key_words6 = ['单摆臂','摆臂']
        key_words7 = ['机器人码垛','机器人']
        key_words8 = ['输送检测控制系统','输送检测']
        key_words9 = ['自动包装控制系统','自动包装']
        key_words10 = ['封口控制系统','封口']
        if any(key_word in question for key_word in key_words1):
            return '低位码垛控制系统'
        elif any(key_word in question for key_word in key_words2):
            return '高位码垛控制系统'
        elif any(key_word in question for key_word in key_words3):
            return '拉伸套膜控制系统'
        elif any(key_word in question for key_word in key_words4):
            return '称重控制系统'
        elif any(key_word in question for key_word in key_words5):
            return '除尘控制系统'
        elif any(key_word in question for key_word in key_words6):
            return '单摆臂自动包装控制系统'
        elif any(key_word in question for key_word in key_words7):
            return '机器人码垛控制系统'
        elif any(key_word in question for key_word in key_words8):
            return '输送检测控制系统'
        elif any(key_word in question for key_word in key_words9):
            return '自动包装控制系统'
        elif any(key_word in question for key_word in key_words10):
            return '封口控制系统' 
        else:
            return None

    def get_secondary_headings(self, title):
        secondary_headings = {}
        # print(self.data.keys())
        contents = self.data[title]
        first_heading_id = 0
        for first_heading, _ in contents.items():
            first_heading_id += 1
            paragraph = contents[first_heading]
            secondary_heading_id = 0
            for secondary_heading, _ in paragraph.items():
                if(secondary_heading != 'text'):
                    secondary_heading_id += 1
                    secondary_headings[secondary_heading] = {'first_heading': first_heading, 'heading_id': str(first_heading_id)+'.'+str(secondary_heading_id)}
        return secondary_headings

    def question_section_classify(self, question, sections, topn=5):
    
        def preprocess_section(section):
            section = section.replace('部分', '')
            if '控制柜' not in section and '控制台' not in section:
                section = section.replace('控制', '')
            section = section.split('、')
            return section

        sections_t = list(sections.keys())
        scores = {}
        max_score = -1
        for section in sections_t:
            if(section in question):
                scores[section] = 100
                continue
                # return {section:sections[section]}
            score = 0
            section_t = preprocess_section(section)
            for sec in section_t:
                if(sec in question):
                    scores[section] = 100
                    continue
                    # return {section:sections[section]}
                for character in list(set(question)):
                    if(character in sec):
                        score += 1 
            score /= len(''.join(section_t))
            # if(score > max_score):
            #     res = [section]
            #     max_score = score
            # elif(score == max_score):
            #     res.append(section)
            scores[section] = score 
        sorted_section = sorted(scores.items(),key=lambda kv:(kv[1], kv[0]))[::-1]
        res = {}
        # print(sorted_section)
        for i in range(min(topn, len(sorted_section))):
            res[sorted_section[i][0]] = sections[sorted_section[i][0]]
        # return {re:sections[re] for re in res}
        return res

    def question_classify(self, question, topn=5):
        title = self.question_title_classify(question)
        if(title is None):
            return None, None
        else:
            print(title)
            secondary_headings = self.get_secondary_headings(title)
            return self.question_section_classify(question, secondary_headings, topn=topn), title

    def get_contents(self, question_classes, title):
        res = []
        for question_class, _ in question_classes.items():
            section = question_class 
            first_heading = question_classes[question_class]['first_heading']
            res.append(self.data[title][first_heading][section])
        return res

    def postprocess(self, contents):

        def helper(json_data):
            re = ''
            text = json_data['text']
            if(text != ''):
                re = re + text + '\n'
            for section, section_content in json_data.items():
                if(section != 'text'):
                    re = re + section + '\n' + helper(section_content)
            return re
        res = []
        for content in contents:
            content = helper(content)
            res.append(content)
        return res

    def get_result(self, question, title,  topn=5):
        # print(question)
        # question_classes, title = self.question_classify(question, topn=topn)
        if(title is not None):
            secondary_headings = self.get_secondary_headings(title)
            question_classes = self.question_section_classify(question, secondary_headings, topn=topn)
            contents = self.get_contents(question_classes, title)
            return  self.postprocess(contents)
        else:
            return []


# a = DbqaModel('data.json')
# ques = '变频故障'
# print(a.get_result(ques))
