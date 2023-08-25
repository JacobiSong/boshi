from itertools import product
import re
from django.shortcuts import render
from django.http import HttpResponse
import logging
import random
import string
import time
import jieba
import json
import re
import os

# from search_engine import BSQuesSimModel, MultiEngine
from single_search_engine import BSQuesSimModel, MultiEngine
from QuestionAnswering.deeplearning_models.dbqa_model_simple1 import DbqaModel
from QuestionAnswering.deeplearning_models.question_classify import QuestionClassifyModel
from QuestionAnswering.utils import post_process_bs_qs_answer, post_process_dst_qs_answer, post_process_bs_qs_answer_without_similarity_and_classification

logger = logging.getLogger("load_model")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

engines = MultiEngine(logger=logger)

DBQA_MODEL = DbqaModel(data_file='QuestionAnswering/data.json')
Question_Classify_Model = QuestionClassifyModel(file_path='QuestionAnswering/deeplearning_models/questionclassify/file')

print('加载博实检索引擎')
BS_QS_MODEL = BSQuesSimModel(logger, engine=engines)
print('加载jieba分词器...')
jieba.initialize()
print('模型加载完成！')

# qcs = {
#     "摆臂式包装机": 'zd',
#     "机器人码垛机": 'jq',
#     "台车式包装机": 'tc',
#     "高位码垛机": 'gw',
#     "低位码垛机": 'dw',
#     "套膜机": 'tm',
#     "输送检测": 'ss',
#     "FFS包装机": 'ffs',
#     "全部": 'all',
# }


def bs_client(request):
    """
    博实客服用于故障查询的接口
    """
    # 这是不带问题分类的
    total_time1 = time.time()
    question = None
    if request.method == 'POST':
        question = request.POST.get('question')
        print('智能客服接收到问题：{}'.format(question))  # 输入框对应的问题
        task = request.POST.get('task')
    MAX_TOP_N = 30
    RET_TOP_N = 8

    if question:
        if len(question.split('@')) == 2:
            question, qc = question.split('@')
            if question.startswith(qc) and qc != '套膜机':
                question = question[len(qc):]
            # if re.search(r'垛盘([0-9])+动作超时', question) and re.search(r'([0-9])+', question).group() != '1':
            #     if qc == '高位码垛机':
            #         question = re.sub(r'([0-9])+','x(2-10)',question)
            #     else:
            #         question = re.sub(r'([0-9])+','x(2-5)',question)
            answer = BS_QS_MODEL.get_result(question, top_n=MAX_TOP_N, question_classification=qc)
            answer = post_process_bs_qs_answer(answer)
        else:
            # if re.search(r'垛盘([0-9])+动作超时', question) and re.search(r'([0-9])+', question).group() != '1':
            #     num = int(re.search(r'([0-9])+', question).group(1))
            #     if num >= 2 and num <= 5:
            #         question = re.sub(r'([0-9])+','x(2-5)',question)
            #     else:
            #         question = re.sub(r'([0-9])+','x(2-10)',question)
            answer = BS_QS_MODEL.get_result_by_search_all(question, top_n=MAX_TOP_N)
            answer = post_process_bs_qs_answer_without_similarity_and_classification(answer)
        # print(answer)
        if answer:
            if task != 'ans': 
                filter_answer = []
                ret_questions = [i['question'] for i in answer['qas']]
                
                for ans in answer['qas']:
                    if ans['question'].startswith(question):
                        filter_answer.append(ans)
                answer['qas'] = filter_answer
                # 模糊匹配，猜你想问
                # 目前设置规则
                #   1. 如果提问“垛盘”，则shuffle一下所有答案
                #   2. 如果提问“垛盘x”,则只返回垛盘x相关的问题
                if question == '垛盘':
                    random.shuffle(answer['qas'])
                if question == '垛盘1':
                    temp = []
                    for ans in answer['qas']:
                        if not ans['question'].startswith('垛盘10'):
                            temp.append(ans)
                    answer['qas'] = temp
            else:
                # 回答问题的任务
                # 首先去重
                filter_answer = []
                for ans in answer['qas']:
                    if ans not in filter_answer:
                        filter_answer.append(ans)
                


                ret_questions = [i['question'] for i in filter_answer]
                for ans in filter_answer:
                    if ret_questions.count(ans['question']) > 1:
                            ans['question'] = ans['question_classification'] + '' + ans['question']
                answer['qas'] = filter_answer

                # 这里需要特殊判定的是垛盘x动作超时，直接判断问题
                # if re.search(r'垛盘([0-9])+动作超时', question):
                #     for __i, ans in enumerate(answer['qas']):
                #         if ans['question'] == question:
                #             answer['best_answer'] = ans['answer']
                #             break

                # 特殊判定一下垛盘x开头的问题，直接判断问题
                if len(re.findall('(垛盘[0-9]+)', question)) > 0:
                    for ans in answer['qas']:
                        if ans['question'] == question:
                            answer['best_answer'] = ans['answer']
                
                # 判断是不是通用类型的问题例如“故障”、“报警”避免出现错误的回答
                if question in ['故障','报警']:
                    answer['best_answer'] = ''
        else:
            answer = {
                'question': question,
                'qas': [
                    {
                        'question': '',
                        'answer': '',
                        'question_classification': '',
                        'match_score': 0,
                        'sim_score': 0,
                    }
                ],
                'best_answer': '',
            }
    else:
        answer = {}
        state = 'empty'

    if 'qas' in answer:
        answer['qas'] = answer['qas'][:RET_TOP_N]

    total_time2 = time.time()
    answer['total_time'] = total_time2 - total_time1
    print('智能客服最终给出的答案是：{}'.format(answer))
    return HttpResponse(json.dumps(answer, ensure_ascii=False))
    '''
    # 以下为带有问题分类的初始版本
    total_time1 = time.time()
    question = None
    if request.method == 'POST':
        question = request.POST.get('question')
        print('智能客服接收到问题：{}'.format(question))  # 输入框对应的问题

    if question:
        qc = Question_Classify_Model.get_result(question)
        print('智能客服将问题分类为：{}'.format(qc))
        answer = BS_QS_MODEL.get_result(question, top_n=3, question_classification=qc)
        answer = post_process_bs_qs_answer(answer)
        if not answer:
            answer = {
                'question': question,
                'qas': [
                    {
                        'question': '',
                        'answer': '',
                        'question_classification': '',
                        'match_score': 0,
                        'sim_score': 0,
                    }
                ],
                'best_answer': '',
            }
    else:
        answer = {}
        state = 'empty'
    total_time2 = time.time()
    answer['total_time'] = total_time2 - total_time1
    print('智能客服最终给出的答案是：{}'.format(answer))
    return HttpResponse(json.dumps(answer, ensure_ascii=False))
    '''


def update(request):
    """
    博实客服用于新增（以及更新）问题的库
    """
    total_time1 = time.time()
    print(request)
    question, answer, question_classification = None, None, None
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        question_classification = request.POST.get('question_classification')
        print(f'待更新的问题：{question}，回答：{answer}，问题类别：{question_classification}')  # 输入框对应的问题

    if question and answer and question_classification:
        engines.multi_add_example(question, answer, question_classification)
    return HttpResponse(json.dumps({'is_updated': True}, ensure_ascii=False))

def add_label(request):
    """
    博实客服用于新增（以及更新）问题的库
    """
    total_time1 = time.time()
    question_classification = None
    
    if request.method == 'POST':
        question_classification = request.POST.get('label')
        if question_classification[0] == '"' and question_classification[-1] == '"':
            question_classification = question_classification[1:-1]
        print(f'新增问题类别：{question_classification}')  # 输入框对应的问题类别

    # if question and answer and question_classification:
    #     engines.multi_add_example(question, answer, question_classification)
    engines.multi_add_label(question_classification)

    return HttpResponse(json.dumps({'is_updated': True}, ensure_ascii=False))



def bs_dbqa(request):
    """
    博实客服DBQA的接口
    """
    total_time1 = time.time()
    question = None
    if request.method == 'POST':
        question = request.POST.get('question')
    if question:
        classs = Question_Classify_Model.get_result(question).strip()
        # print(classs)
        answer = {'result': DBQA_MODEL.get_result(question, classs), 'class': classs}
    else:
        answer = {'result': []}
        state = 'empty'
    total_time2 = time.time()
    answer['total_time'] = total_time2 - total_time1
    return HttpResponse(json.dumps(answer, ensure_ascii=False))


def get_qa_pair(request):
    """
    博实客服用户获取某类型产品所有问答对的方法
    """
    # TODO: 获得数据库中的所有问题, debug 为30 正常是不应该设置的
    if request.method == 'POST':
        product_name = request.POST.get('product')
    # data_dir="QuestionAnswering/search_corpus"
    # ret = {}
    # # product = request.POST.get('product')
    # # for k, v in {'全部':'all'}.items():
    # for k, v in qcs.items():
    #     with open(os.path.join(data_dir, v + '.json'), 'r', encoding="utf-8") as f:
    #         lines = json.load(f)
    #         # print(lines)
    #         for line in lines:
    #             ret[line["question_whole"] + '@' + k] = {'answer': line["answer_whole"], 'label': k, 'count': 1}
    #     break


    if product_name in engines.get_all_question_classification():
        # 1. 产品类型
        ret = engines.get_all_qa_pairs(product_name, max_num=-1)
    else:
        # 模糊查询
        # 这是不带问题分类的
        total_time1 = time.time()
        question = product_name
        MAX_TOP_N = 30

        if question:
            if len(question.split('@')) == 2:
                question, qc = question.split('@')
                if question.startswith(qc) and qc != '套膜机':
                    question = question[len(qc):]
                # if re.search(r'垛盘([0-9])+动作超时', question) and re.search(r'([0-9])+', question).group() != '1':
                #     if qc == '高位码垛机':
                #         question = re.sub(r'([0-9])+','x(2-10)',question)
                #     else:
                #         question = re.sub(r'([0-9])+','x(2-5)',question)
                answer = BS_QS_MODEL.get_result(question, top_n=MAX_TOP_N, question_classification=qc)
                answer = post_process_bs_qs_answer(answer)
            else:
                # if re.search(r'垛盘([0-9])+动作超时', question) and re.search(r'([0-9])+', question).group() != '1':
                #     num = int(re.search(r'([0-9])+', question).group(1))
                #     if num >= 2 and num <= 5:
                #         question = re.sub(r'([0-9])+','x(2-5)',question)
                #     else:
                #         question = re.sub(r'([0-9])+','x(2-10)',question)
                answer = BS_QS_MODEL.get_result_by_search_all(question, top_n=MAX_TOP_N)
                answer = post_process_bs_qs_answer_without_similarity_and_classification(answer)
            # print(answer)
            if answer:
                filter_answer = []
                ret_questions = [i['question'] for i in answer['qas']]
                
                for ans in answer['qas']:
                    if ans['question'].startswith(question):
                        filter_answer.append(ans)
                answer['qas'] = filter_answer
                
                # 模糊匹配，猜你想问
                # 目前设置规则
                #   1. 如果提问“垛盘”，则shuffle一下所有答案
                #   2. 如果提问“垛盘x”,则只返回垛盘x相关的问题
                if question == '垛盘':
                    random.shuffle(answer['qas'])
                if question == '垛盘1':
                    temp = []
                    for ans in answer['qas']:
                        if not ans['question'].startswith('垛盘10'):
                            temp.append(ans)
                    answer['qas'] = temp
            else:
                answer = {
                    'question': question,
                    'qas': [
                        {
                            'question': '',
                            'answer': '',
                            'question_classification': '',
                            'match_score': 0,
                            'sim_score': 0,
                        }
                    ],
                    'best_answer': '',
                }
        else:
            answer = {}
            state = 'empty'
        
        temp_ans = {
            k['question'] + '@' + k['question_classification']: \
                {
                    'answer' : k['answer'],
                    'label' : k['question_classification'],
                    'count' : 1
                }
                    for k in answer['qas']
             }
        answer = temp_ans
        ret = answer
        
    # print(ret)
    return HttpResponse(json.dumps(ret, ensure_ascii=False))

def delete_question(request):
    """
    博实客服用于删除问题的接口
    """
    question, answer, question_classification = None, None, None
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        question_classification = request.POST.get('question_classification')
    if question and question_classification:
        if '@' in question: question = question.split('@')[0]
        engines.multi_delete_example(question, answer, question_classification)
    return HttpResponse(json.dumps({'is_updated': True}, ensure_ascii=False))

# 故障查询，返回所有产品的名字
def get_product_name(request):
    """
    博实客服用于动态返回所有产品名称的接口
    """
    return HttpResponse(json.dumps({'product_names': engines.get_all_question_classification()}, ensure_ascii=False))

# 针对某个产品查询所有的故障
def get_all_questions(request):
    """
    博实客服用于针对某类型产品返回所有问题@产品名称的接口
    """
    # product_name = request.POST.get('product_name')
    # data_dir="QuestionAnswering/search_corpus"
    # ret = {}
    # with open(os.path.join(data_dir, qcs[product_name] + '.json'), 'r', encoding="utf-8") as f:
    #     lines = json.load(f)
    #     # print(lines)
    #     for line in lines:
    #         ret[line["question_whole"] + '@' + product_name] = {'answer': line["answer_whole"], 'label': product_name, 'count': 1}
    product_name = request.POST.get('product_name')
    ret = engines.get_one_classification_qa_pairs(product_name)
    return HttpResponse(json.dumps(ret, ensure_ascii=False))
