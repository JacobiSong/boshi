# coding:utf-8
# %%

import functools
import sys
from whoosh.index import IndexError
# coding:utf-8
sys.path.append("QuestionAnswering")
# %%

def get_instance(module, name, config, *args):
    return getattr(module, config[name]['type'])(*args, **config[name]['args'])


class BSQuesSimModel():
    '''
    description: 封装了相似度计算模型的博实问答相似度计算类（目前删掉了精排阶段的相似度计算模型） 
    '''
    def __init__(self, logger, engine=None):
        super(BSQuesSimModel).__init__()
        self.logger = logger
        self.engine = engine

    def get_result_by_search_all(self, question, top_n=3):
        """
        根据“粗排”来返回结果
        :param top_n: 最多返回多少个结果
        :param question: str, the question to be answered
        :return(dict): 返回结果是字典类型，返回的答案信息
        the res dict has two keys:
            "answer: ", str
            "paras: ", a list of list of str
        """
        # 给定问题在全部问题类别中进行检索，并且不计算相似度
        search_results = self.engine.multi_search_bs(None, question, limit=top_n)
        # print(search_results)
        return search_results


    def get_result(self, question, top_n=3, question_classification=None):
        """
        根据问题得到结果，这个函数注释部分的代码包括了精排代码
        :param top_n: 最多返回多少个结果
        :param question: str, the question to be answered
        :return(dict): 返回结果是字典类型，返回的答案信息
        the res dict has two keys:
            "answer: ", str
            "paras: ", a list of list of str
        """
        # 实现的逻辑是：首先在对应的问题类别内检索相关的问题，如果没有匹配结果，则改为在全部问题类别中检索
        search_results = self.engine.multi_search_bs(question_classification, question, limit=6)
        print('召回阶段得到的检索结果为：{}'.format(search_results))
        if not search_results:
            search_results = self.engine.multi_search_bs('全部', question, limit=top_n)
            if not search_results:
                return None
            print('question classification repaired to all')

        search_results['qas'] = [ele for ele in search_results['qas'] if ele['question_classification'] == question_classification]
        # print(search_results)
        if search_results:
            question = search_results['question']
            for candidate in search_results['qas']:
                sim_question = candidate['question']
                sim_score = 0.0 
                # print('sim_question: ', sim_question)
                # try:
                #     sim_score = self.question_similarity(question, sim_question)
                # except Exception:
                #     self.logger.warn('Fail to calculate. Param: %s', sim_question, exc_info=True)
                #     sim_score = 0.0
                candidate['sim_score'] = sim_score
            # results = dict(sorted(results.items(), key=lambda x: x[1]))
        search_results['qas'].sort(key=functools.cmp_to_key(cmp))
        search_results['qas'] = search_results['qas'][0:top_n]
        return search_results

    
    def question_similarity(self, q1, q2):
        """
        问题相似度计算模型
        :param q1: str, 问句1
        :param q2: str, 问句2
        :return float: 返回问句1、问句2的相似度计算得分
        the res dict has two keys:
            "answer: ", str
            "paras: ", a list of list of str
        """
        return self.trainer.predict_onesample(q1, q2, '0')


def cmp(a, b):
    if a['sim_score'] <= b['sim_score']:
        return 1
    else:
        return -1


# here put the import lib
# %%
import os
import json
import logging
from whoosh.fields import *
from whoosh import index, qparser
from whoosh.qparser import QueryParser
from whoosh.writing import AsyncWriter
from whoosh import scoring
import jieba


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

#注意index_dir corpus_1是在

class MultiEngine(object):
    '''
    description: 多类别检索引擎，可以实现对多个whoosh index的检索，目前采用的方法是直接进行全库检索 
    '''
    def __init__(self, logger, index_dir="QuestionAnswering/search_corpus", rebuild=True):
        # self.engines = {}
        # for k, v in qcs.items():
        #     self.engines[v] = Engine(logger=logger, qc=v)
        self.engine = Engine(logger)
        self.question_classification_lst = self.engine.get_all_question_classification()
    
    # /root/remind/qa_demo/QuestionAnswering/deeplearning_models/search/search_corpus
    def build_bs_idx(self, index_dir="QuestionAnswering/search_corpus"):
        """
        建立whoosh索引
        :param index_dir: index文件储存的目标文件夹
        :return: None
        """
        self.engine.build_bs_idx()

    def multi_search_bs(self, question_classification, question, limit=15, limit_score=0.0):
        """
        多引擎检索（目前直接对全库这个单引擎进行的检索）
        :param index_dir: index文件储存的目标文件夹
        :return（dcit）：dict 结构如下：
        {
            "question": []
            “qas” : [
                {
                    "question": res["question"],
                    "answer": answer,
                    "question_classification": question_classification,
                    "match_score": 114514
                }
            ]
        }
        """
        return self.engine.search(question, question_classification)
        # return self.engine.search_bs(question, question_classification, limit=limit, limit_score=limit_score)

    def multi_add_example(self, question, answer, question_classification):
        """
        多引擎添加Item（目前直接对全库这个单引擎进行的Item）
        :param question: 待添加的问题
        :param answer: 待添加的回答
        :param question_classification: 待添加的问题分类
        :return None
        """
        self.engine.add_example(question, answer, question_classification)
        
    def multi_add_label(self, question_classification):
        """
        多引擎添加问题分类（目前直接对全库这个单引擎进行的添加问题分类）
        :param question_classification: 待添加的问题分类
        :return None
        """
        if question_classification not in self.question_classification_lst:
            self.question_classification_lst.append(question_classification)
        
    def multi_delete_example(self, question, answer, question_classification):
        """
        多引擎删除Item（目前直接对全库这个单引擎进行的Item）
        :param question: 待删除的问题
        :param answer: 待删除的回答
        :param question_classification: 待删除的问题分类
        :return None
        """
        self.engine.delete_example(question, answer, question_classification)
    
    def get_all_question_classification(self):
        """
        动态获取目前所有的问题分类
        :return list ： ['摆臂式包装机', '高位码垛机', ...]
        """
        # return self.engine.get_all_question_classification()
        return self.question_classification_lst
    
    def get_all_qa_pairs(self, product, max_num=-1):
        """
        获取一个问题类型的所有问答对
        :param product: 产品问题分类
        :param max_num: max_num 为-1则返回该问题类型所有的问答对，不为-1则返回max_num个该问题类型的问答对
        :return dict :
            {
                'q1':'a1',
                'q2':'a2',
                
            }
        """
        ret = self.engine.get_all_qa_pairs(product)
        if max_num != -1:
            temp_ret = list(ret.items())[:max_num]
            return {t[0]: t[1] for t in temp_ret}
        return ret
    
    def get_one_classification_qa_pairs(self, question_classification):
        """
        获取一个问题类型的所有问题
        :param question_classification: 产品问题分类
        :return list :
        ['q1@question_classification', ...]
        """
        return self.engine.get_one_classification_qa_pairs(question_classification)
        # qa_pairs = self.engine.json_corpus.values()
        # ret = []
        # for item in qa_pairs:
        #     if item['question_classification'] == question_classification:
        #         ret.append(item['question']+'@'+item['question_classification'])
        # return ret

class Engine(object):
    """构建本地库的搜索引擎.
    1.建立索引和模式对象
    2.写入索引文件
    3.提供搜索接口
    ------------------------------------
    'logger': logger.
    'index_dir: ', search index directory.
    'docs_size: ', the number of docs contained in local index corpus, -1 for all corpus.
    'qas_size: ', the number of qas contained in local index corpus, -1 for all corpus.
    'rebuild': if rebuild the index directory.
    """
    def __init__(self, logger, qc='all', index_dir="QuestionAnswering/search_corpus", rebuild=True):
        # 获取日志
        self.logger = logger
        self.qc = qc
        # 建立索引和模式对象
        self.schema = Schema(question=TEXT(stored=True), id=ID(stored=True), answer=TEXT(stored=True), question_classification=TEXT(stored=True))
        self.index_dir = index_dir
        # 记录当前所有的问答对 dict
        # json_corpus format
        #   {
        #   question_whole : {
        #           question_classification : answer_whole
        #       }
        #   }
        self.json_corpus = {}
        self.load_json_corpus()

        # 建立bs_qs库
        if rebuild or not index.exists_in(index_dir, indexname=self.qc):
            self.build_bs_idx()
            # self.bs_ix = index.create_in(index_dir, self.schema, indexname=self.qc)
            # # 写入索引内容
            # self.logger.info("writing bs {} corpus to index...".format(self.qc))
            # self.bs_writer = self.bs_ix.writer()
            # self._write_bs_corpus()
            # self.bs_writer.commit()
            # self.logger.info("writing bs {} corpus size is {}".format(self.qc, self.bs_ix.doc_count()))
            # self.logger.info("writing bs {} corpus done!".format(self.qc))
        else:
            self.bs_ix = index.open_dir(index_dir, indexname=self.qc)
            self.logger.info("reading bs {} corpus size is {}".format(self.qc, self.bs_ix.doc_count()))
    
    def get_all_qa_pairs(self, question_classification):
        """
        获取一个问题类型的所有问答对
        :param question_classification: 产品问题分类
        :return dict :
            {
                'q1': {
                    'answer' : answer, 
                    'label' : question_classification,
                    'count' : 1
                    },
                ...                
            }
        """
        ret = {}
        for question_whole, values in self.json_corpus.items():
            for qc, answer_whole in values.items():
                if qc == question_classification:
                    ret[question_whole+'@'+question_classification] = {
                        'answer': answer_whole,
                        'label': question_classification,
                        'count': 1
                    }
        return ret
    
    def get_one_classification_qa_pairs(self, question_classification):
        """
        获取一个问题类型的所有问题
        :param question_classification: 产品问题分类
        :return list :
        ['q1@question_classification', ...]
        """
        ret = []
        for question_whole, values in self.json_corpus.items():
            for qc, answer_whole in values.items():
                if qc == question_classification:
                    ret.append(question_whole + '@' + question_classification)
        return ret
    
    def get_all_question_classification(self,):
        """
        动态获取目前所有的问题分类
        :return list ： ['摆臂式包装机', '高位码垛机', ...]
        """
        qcs = set()
        for k, v in self.json_corpus.items():
            for qc in v.keys():
                qcs.add(qc)
        return list(qcs)
    
    def dump_to_json_file(self):
        """
        将当前的json_corpus库中记录的所有问题全部都重新dump至文件中
        :return None
        """
        pop_items = []
        for question_whole, values in self.json_corpus.items():
            if len(values) == 0:
                pop_items.append(question_whole)
        for it in pop_items:
            self.json_corpus.pop(it)
        with open(os.path.join(self.index_dir, self.qc + '.json'), 'w', encoding='utf-8') as f:
            json.dump(self.json_corpus, f, ensure_ascii=False, indent=4)
            self.logger.info('dump json corpus to json file')

    def add_to_json_corpus(self, question_whole, answer_whole, question_classification, dump_to_file=True):
        """
        将问答信息添加至json_corpus中
        :param question_whole: 问题字符串
        :param answer_whole: 回答字符串
        :param question_classification: 产品问题分类
        :param dump_to_file: 是否将改动dump到文件中
        :return None
        """
        if question_whole not in self.json_corpus:
            self.json_corpus[question_whole] = {}
        self.json_corpus[question_whole][question_classification] = answer_whole
        if dump_to_file:
            self.dump_to_json_file()
    
    def delete_from_json_corpus(self, question_whole, answer_whole, question_classification, dump_to_file=True):
        """
        将问答信息从json_corpus中删除
        :param question_whole: 问题字符串
        :param answer_whole: 回答字符串
        :param question_classification: 产品问题分类
        :param dump_to_file: 是否将改动dump到文件中
        :return None
        """
        if question_whole not in self.json_corpus or question_classification not in self.json_corpus[question_whole]:
            return
        self.json_corpus[question_whole].pop(question_classification)
        if dump_to_file:
            self.dump_to_json_file()
    
    def search_json_corpus(self, question_whole, question_classification):
        res = {}
        res["question"] = list(jieba.cut(question_whole))
        if question_whole in self.json_corpus and question_classification in self.json_corpus[question_whole]:
            answer = list(jieba.cut(self.json_corpus[question_whole][question_classification]))
            qas = [
                {
                    "question": res["question"],
                    "answer": answer,
                    "question_classification": question_classification,
                    "match_score": 114514
                }
            ]
            res["qas"] = qas
            return res
        return None

    def load_json_corpus(self,):
        """
        从json文件中加载数据至self.json_corpus
        :return None
        """
        # 这里是对全信息的all.json加载的方法
        # with open(os.path.join(self.index_dir, self.qc + '.json'), 'r', encoding="utf-8") as f:
        #     lines = json.load(f)
        #     for line in lines:
        #         d = line
        #         if d['question'] is not None \
        #              and d['answer'] is not None \
        #                   and d["question_classification"] is not None:
        #             self.add_to_json_corpus(d["question_whole"], d['answer_whole'], d["question_classification"], dump_to_file=False)
        # count = 0
        # for k, v in self.json_corpus.items():
        #     count += len(v.keys())
        # self.logger.info(f'load json corpus with {count} items')
        
        # 这里是对目前过滤后的all.json加载的方法
        with open(os.path.join(self.index_dir, self.qc + '.json'), 'r', encoding="utf-8") as f:
            self.json_corpus = json.load(f)
        count = 0
        for k, v in self.json_corpus.items():
            count += len(v)
        self.logger.info(f'load json corpus with {count} questions')
         

    def build_bs_idx(self, index_dir="QuestionAnswering/search_corpus"):
        """
        构建whoosh index索引
        :param index_dir: 索引文件夹位置
        :return None
        """
        def _write_bs_corpus(data_dir=self.index_dir):
            """写qas库的索引内容"""
            # 通过文件写，目前这种方法是已经弃用的
            # with open(os.path.join(data_dir, self.qc + '.json'), 'r', encoding="utf-8") as f:
            #     lines = json.load(f)
            #     for line in lines:
            #         d = line
            #         if d['question'] is not None \
            #             and d['answer'] is not None \
            #                 and d["question_classification"] is not None:
            #             self.bs_writer.add_document(question=" ".join(d["question"]), answer=" ".join(d["answer"]), question_classification=d["question_classification"])

            # 通过json_corpus
            for question_whole, values in self.json_corpus.items():
                for question_classification, answer_whole in values.items():
                    # 加空格分割的方法
                    question = list(jieba.cut(question_whole))
                    answer = list(jieba.cut(answer_whole))
                    self.bs_writer.add_document(question=" ".join(question), answer=" ".join(answer), question_classification=question_classification)

                    # # 不加空格分割的方法
                    # self.bs_writer.add_document(question=question_whole, answer=answer_whole, question_classification=question_classification)

        # 建立索引存储目录
        if not os.path.exists(index_dir):
            os.mkdir(index_dir)
        self.bs_ix = index.create_in(index_dir, self.schema, indexname=self.qc)
        # 写入索引内容
        # self.logger.info("writing bs {} corpus to index...".format(self.qc))
        self.bs_writer = self.bs_ix.writer()
        _write_bs_corpus()
        self.bs_writer.commit()
        self.logger.info("writing bs {} corpus size is {}".format(self.qc, self.bs_ix.doc_count()))
        self.logger.info("writing bs {} corpus done!".format(self.qc))

    def search_bs(self, question, question_classification=None, limit=20, limit_score=0.0):
        """根据博实项目相关的question检索相关qa pairs.
        "question": str type. question str.
        "limit": int type, returned contexts num.
        "limit_score": float type, match score of every searched qas.
        return
            "res": dict type. It has two keys:
                "question": a list of str, segmented question.
                "qas": a list of list of dicts, several contexts related to the question.
            if return None, it represents no related qas.
        """
        seg_question = list(jieba.cut(question))
        # print(question, self.qc)
        try:
            searcher = self.bs_ix.searcher(weighting=scoring.BM25F)
            # 解析query
            # 检索"question"和"answer"的field,指标是BM25
            og = qparser.OrGroup.factory(0.9)
            parser = qparser.QueryParser("question", schema=self.bs_ix.schema, group=og)
            query = parser.parse(" ".join(seg_question))
            result = searcher.search(query, limit=limit)
            if result.is_empty():
                return None

            # 抽取返回结果信息
            res = {}
            res["question"] = seg_question
            qas = []
            for i, hit in enumerate(result):
                # print(i, '\t\t\t', hit)
                if question_classification and question_classification != hit["question_classification"]:
                    continue
                c = {}
                c["question"] = hit["question"].split(" ")
                c["answer"] = hit["answer"].split(" ")
                c["question_classification"] = hit["question_classification"]
                c["match_score"] = result.score(i)
                # if score is not larger than limit_score, filter it
                # if c["match_score"] <= limit_score:
                # continue
                qas.append(c)
            if len(qas) == 0:
                return None
            else:
                res["qas"] = qas
                return res
        finally:
            searcher.close()
    
    def search(self, question, question_classification=None):
        """
        先从json_corpus检索是否有匹配的，没有的话从whoosh index中进行检索
        :param index_dir: index文件储存的目标文件夹
        :return（dcit）：dict 结构如下：
        {
            "question": []
            “qas” : [
                {
                    "question": res["question"],
                    "answer": answer,
                    "question_classification": question_classification,
                    "match_score": 114514
                }
            ]
        }
        """
        question_whole = question
        if question_classification:
            json_res = self.search_json_corpus(question_whole, question_classification)
            if json_res:
                return json_res
        return self.search_bs(question_whole, question_classification)

    def add_example(self, question, answer, question_classification, data_dir="QuestionAnswering/search_corpus"):
        """
        单引擎添加Item
        :param question: 待添加的问题
        :param answer: 待添加的回答
        :param question_classification: 待添加的问题分类
        :return None
        """
        question_whole = question
        answer_whole = answer
        question = list(jieba.cut(question))
        answer = list(jieba.cut(answer))
        # example = {
        #     "production": None,
        #     "title": None,
        #     "chapter": None,
        #     "section": None,
        #     "question": question,
        #     "question_whole": question_whole,
        #     "answer": answer,
        #     "answer_whole": answer_whole,
        #     "similar_question": None,
        #     "similar_question_whole": None,
        #     "passage": None,
        #     "question_classification": question_classification,
        # }
        self.add_to_json_corpus(question_whole, answer_whole, question_classification, dump_to_file=True)
        self.build_bs_idx()
        self.logger.info(f'add question : {question_whole}, answer : {answer_whole}, question_classification : {question_classification} to Engine')
        return        
    
    def delete_example(self, question, answer, question_classification, data_dir="QuestionAnswering/search_corpus"):
        """
        单引擎删除Item
        :param question: 待删除的问题
        :param answer: 待删除的回答
        :param question_classification: 待删除的问题分类
        :return None
        """
        assert type(question) == str
        question_whole = question
        answer_whole = answer
        self.delete_from_json_corpus(question_whole, answer_whole, question_classification, dump_to_file=True)
        self.build_bs_idx()
        self.logger.info(f'delete question : {question_whole}, answer : {answer_whole}, question_classification : {question_classification} to Engine')

        # # 以下是初始版本
        # with open(os.path.join(data_dir, self.qc + '.json'), 'r', encoding='utf-8') as f:
        #     questions = json.load(f)
        #     for temp_q in questions:
        #         if question == temp_q['question_whole'] and question_classification == temp_q['question_classification']:
        #             questions.remove(temp_q)
        #             # print('delete the example from the json file')
        #             self.logger.info('delete the example from the json file')
        # with open(os.path.join(data_dir, self.qc + '.json'), 'w', encoding='utf-8') as f:
        #     json.dump(questions, f, ensure_ascii=False, indent=4)
        #     # f.writelines('\n' + json.dumps(example, ensure_ascii=False, indent=4))
        
        # if question in self.json_corpus:
        #     self.json_corpus.pop(question)
        
        # # rebuild 一下 删掉在里面的索引
        # self.bs_ix = index.create_in(self.index_dir, self.schema, indexname=self.qc)
        # # 写入索引内容
        # self.logger.info("writing bs {} corpus to index...".format(self.qc))
        # self.bs_writer = self.bs_ix.writer()
        # self._write_bs_corpus()
        # self.bs_writer.commit()
        # self.logger.info("writing bs {} corpus size is {}".format(self.qc, self.bs_ix.doc_count()))
        # self.logger.info("writing bs {} corpus done!".format(self.qc))
        # # seg_question = list(jieba.cut(question))
        # # seg_ans = list(jieba.cut(answer))
        # # try:
        # #     # searcher = self.bs_ix.searcher(weighting=scoring.BM25F)
        # #     # # 解析query
        # #     # # 检索"question"和"answer"的field,指标是BM25
        # #     # og = qparser.OrGroup.factory(0.9)
        # #     # parser = qparser.QueryParser("question", schema=self.bs_ix.schema, group=og)
        # #     # query = parser.parse(" ".join(seg_question))
        # #     searcher = self.bs_ix.searcher()
        # #     doc_num = searcher.document_number(question=' '.join(seg_question), answer=' '.join(seg_ans) ,question_classification=question_classification)
            
        # #     # raise IndexError('GG 没有删除成功')
        # #     if doc_num:
        # #         self.bs_writer = self.bs_ix.writer()
        # #         self.bs_writer.delete_document(doc_num)
        # #         self.bs_writer.commit()
        # #         self.logger.info('delete the example from the whoosh index')
        # #         print('delete the example from the whoosh index')
        # #     else:
        # #         raise IndexError('GG 没有删除成功')
        # # except IndexError:
        # #     print(f'delete error and delete 0 item in whoosh index')
        # #     self.logger.info(f'delete error and delete 0 item in whoosh index')


if __name__ == '__main__':
    # local test code
    # prepare logger
    logger = logging.getLogger("MC")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # run engine
    engines = MultiEngine(logger)
    engines.build_bs_idx()
    with open('/root/remind/qa_demo/test_questions.txt', 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines()]
    
    for q in lines:
        question,qc = q.split('@')
        result = engines.multi_search_bs(qc, question, limit=1)
        print(q)
        print(result)

    # print(engines.multi_search_bs('套膜机', '套膜机控制柜操作面板有哪些控制元件组成？'))
    # print(engines.multi_search_bs('低位码垛机', '低位码垛机的转位机构包括哪三个部分？'))

    # engine = Engine(logger)
    # engine.build_bs_idx()
    # print(engine.search_bs('套膜机控制柜操作面板有哪些控制元件组成？'))

    # print("检索与问题相关的文档：")
    # res = engine.search("茄子意面的做法是？")
    # # res = engine.search("周杰伦的生日是啥？")
    # # res = engine.search("英雄联盟？")
    # print("搜索结果：")
    # print(res)
    #
    # print("检索与问题相关的qa对：")
    # # qas_res = engine.search_qas("2017有什么好看的小说?")
    # qas_res = engine.search_qas("截至和截止的区别？")
    # print("搜索结果: ")
    # print(qas_res)

# %%
