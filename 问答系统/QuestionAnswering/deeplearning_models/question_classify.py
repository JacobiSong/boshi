import torch.nn.functional as F
import torch.nn as nn
import torch
from QuestionAnswering.deeplearning_models.questionclassify.model.cnn import *
import logging
from .base_model import BaseModel
import jieba
import re
import json
import sys
sys.path.append("QuestionAnswering")
# from QuestionAnswering.deeplearning_models.questionclassify.model.cnn import TextCNN

regex = re.compile(r'[^\u4e00-\u9fa5aA-Za-z0-9]')


class QuestionClassifyModel(BaseModel):

    def __init__(self, file_path):
        super(QuestionClassifyModel).__init__()
        self.word2idx = json.load(open(file_path+'/'+'word2idx.json'))
        label2idx = json.load(open(file_path+'/'+'label2idx.json'))
        self.idx2label = {idx: label for label, idx in label2idx.items()}
        self.model = torch.load(file_path+'/'+'model.pkl', map_location='cpu')
        self.model.eval()
        # print('load model done')

    def keywordssearch(self, question):
        key_words1 = ['低位码垛机', '低位码垛']
        key_words2 = ['高位码垛机', '高位码垛', '码垛机']
        key_words3 = ['套膜机', '套膜控制系统', '拉伸套膜机']
        key_words4 = ['单摆臂', '摆臂']
        key_words5 = ['机器人码垛', '机器人']
        key_words6 = ['输送检测控制系统', '输送检测']
        key_words7 = ['封口控制系统', '封口']
        key_words8 = ['台车', '台车式']
        if any(key_word in question for key_word in key_words1):
            return '低位码垛机'
        elif any(key_word in question for key_word in key_words2):
            return '高位码垛机'
        elif any(key_word in question for key_word in key_words3):
            return '套膜机'
        elif any(key_word in question for key_word in key_words4):
            return '自动包装控制系统(单摆臂)'
        elif any(key_word in question for key_word in key_words5):
            return '机器人码垛机'
        elif any(key_word in question for key_word in key_words6):
            return '输送检测'
        elif any(key_word in question for key_word in key_words7):
            return '封口机'
        elif any(key_word in question for key_word in key_words8):
            return '台车式包装机'
        else:
            return None

    def get_result(self, question):
        res = self.keywordssearch(question)
        # print(res)
        if res:
            return res
        question = regex.sub(' ', question)
        words = [word for word in jieba.cut(question) if question.strip()]
        wordids = [self.word2idx[word] if word in self.word2idx else 1 for word in words]
        while len(wordids) < 2:
            wordids.append(0)
        logit = self.model(torch.tensor(wordids).unsqueeze(0))
        pred = torch.max(logit, 1)[1].item()
        # print(self.idx2label[pred])
        return self.idx2label[pred]
