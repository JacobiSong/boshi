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
    """
    """
    def __init__(self, logger, engine=None):
        super(BSQuesSimModel).__init__()
        self.logger = logger
        self.engine = engine
    
    def get_result_by_search_all(self, question, top_n=3):
        # 给定问题在全部问题类别中进行检索，并且不计算相似度
        search_results = self.engine.multi_search_bs('全部', question, limit=top_n)
        print(search_results)
        return search_results


    def get_result(self, question, top_n=3, question_classification=None):
        """
        根据问题得到结果，
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


qcs = {
    "摆臂式包装机": 'zd',
    "机器人码垛机": 'jq',
    "台车式包装机": 'tc',
    "高位码垛机": 'gw',
    "低位码垛机": 'dw',
    "套膜机": 'tm',
    "输送检测": 'ss',
    "FFS包装机": 'ffs',
    "全部": 'all',
}

#注意index_dir corpus_1是在

class MultiEngine(object):

    def __init__(self, logger, index_dir="QuestionAnswering/deeplearning_models/search/search_corpus", docs_size=100, qas_size=100, bs_size=100, rebuild=True):

        self.engines = {}
        for k, v in qcs.items():
            self.engines[v] = Engine(logger=logger, qc=v)
    
    # /root/remind/qa_demo/QuestionAnswering/deeplearning_models/search/search_corpus
    def build_bs_idx(self, index_dir="QuestionAnswering/deeplearning_models/search/search_corpus"):
        for k, engine in self.engines.items():
            engine.build_bs_idx()

    def multi_search_bs(self, question_classification, question, limit=8, limit_score=0.0):
        return self.engines[qcs[question_classification]].search_bs(question, limit=limit, limit_score=limit_score)

    def multi_add_example(self, question, answer, question_classification):
        if question_classification in qcs:
            if question_classification != '全部':
                self.engines[qcs[question_classification]].add_example(question, answer, question_classification)
            else: self.engines['all'].add_example(question, answer, question_classification)
        else:
            print('quesition_classification不在预定义的设备列表中')
    
    def multi_delete_example(self, question, answer, question_classification):
        if question_classification in qcs and question_classification != '全部':
            self.engines[qcs[question_classification]].delete_example(question, answer, question_classification)
            self.engines['all'].delete_example(question, answer, question_classification)
        else:
            print('quesition_classification不在预定义的设备列表中')

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
    def __init__(self, logger, qc=None, index_dir="QuestionAnswering/search_corpus", docs_size=100, qas_size=100, bs_size=100, rebuild=True):
        # 获取日志
        self.logger = logger
        self.qc = qc

        self.docs_size = docs_size
        self.qas_size = qas_size
        self.bs_size = bs_size

        # 建立索引和模式对象
        self.schema = Schema(question=TEXT(stored=True), id=ID(stored=True), answer=TEXT(stored=True), question_classification=TEXT(stored=True))
        self.index_dir = index_dir

        # self.bs_ix = index.create_in(index_dir, self.schema, indexname=self.qc)
        # 写入索引内容
        # self.logger.info("writing bs {} corpus to index...".format(self.qc))
        # self.bs_writer = self.bs_ix.writer()

        # 建立bs_qs库
        if rebuild or not index.exists_in(index_dir, indexname=self.qc):
            self.bs_ix = index.create_in(index_dir, self.schema, indexname=self.qc)
            # 写入索引内容
            self.logger.info("writing bs {} corpus to index...".format(self.qc))
            self.bs_writer = self.bs_ix.writer()
            self._write_bs_corpus()
            self.bs_writer.commit()
            self.logger.info("writing bs {} corpus size is {}".format(self.qc, self.bs_ix.doc_count()))
            self.logger.info("writing bs {} corpus done!".format(self.qc))
        else:
            self.bs_ix = index.open_dir(index_dir, indexname=self.qc)
            self.logger.info("reading bs {} corpus size is {}".format(self.qc, self.bs_ix.doc_count()))

    def build_bs_idx(self, index_dir="QuestionAnswering/search_corpus"):
        # 建立索引和模式对象
        # schema = Schema(question=TEXT(stored=True), id=ID(stored=True), answer=TEXT(stored=True), question_classification=TEXT(stored=True))

        # 建立索引存储目录
        if not os.path.exists(index_dir):
            os.mkdir(index_dir)
        self.bs_ix = index.create_in(index_dir, self.schema, indexname=self.qc)
        # 写入索引内容
        # self.logger.info("writing bs {} corpus to index...".format(self.qc))
        self.bs_writer = self.bs_ix.writer()
        self._write_bs_corpus()
        self.bs_writer.commit()
        self.logger.info("writing bs {} corpus size is {}".format(self.qc, self.bs_ix.doc_count()))
        self.logger.info("writing bs {} corpus done!".format(self.qc))

    def search_bs(self, question, limit=3, limit_score=0.0):
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

    def _write_bs_corpus(self, data_dir="QuestionAnswering/search_corpus", question_classification=None):
        """写qas库的索引内容"""
        count = 0
        with open(os.path.join(data_dir, self.qc + '.json'), 'r', encoding="utf-8") as f:
            # content = f.read()
            # lines = []
            # for ele in content.split('}\n{'):
            #     # ele = ele.strip('{}')
            #     lines.append('{' + ele.strip('{}') + '}')

            lines = json.load(f)

            # print(f'{self.qc}去重前数量为{len(lines)}')
            # lines = list(set(lines))
            # print(f'{self.qc}去重后数量为{len(lines)}')

            for line in lines:
                # d = json.load(line)
                d = line
                # print(d)
                if d['question'] is not None \
                     and d['answer'] is not None \
                          and d["question_classification"] is not None:
                    self.bs_writer.add_document(question=" ".join(d["question"]), answer=" ".join(d["answer"]), question_classification=d["question_classification"])
                    count += 1
                # if count != -1 and count == self.bs_size:
                # return

    def add_example(self, question, answer, question_classification, data_dir="QuestionAnswering/search_corpus"):
        question_whole = question
        question = list(jieba.cut(question))
        answer = list(jieba.cut(answer))
        example = {
            "production": None,
            "title": None,
            "chapter": None,
            "section": None,
            "question": question,
            "question_whole": question_whole,
            "answer": answer,
            "answer_whole": ''.join(answer),
            "similar_question": None,
            "similar_question_whole": None,
            "passage": None,
            "question_classification": question_classification,
        }
        # 重复检测
        with open(os.path.join(data_dir, self.qc + '.json'), 'r', encoding='utf-8') as f:
            questions = json.load(f)
            for temp_q in questions:
                if question_whole == temp_q['question_whole'] and question_classification == temp_q['question_classification']:
                    questions.remove(temp_q) 
            # if question_whole in questions:
            #     print(f'can\'t add question:({question_whole}) to json file because there has been one same question in indices')
            #     return
        
        with open(os.path.join(data_dir, self.qc + '.json'), 'w', encoding='utf-8') as f:
            questions.append(example)
            json.dump(questions, f, ensure_ascii=False, indent=4)
            # f.writelines('\n' + json.dumps(example, ensure_ascii=False, indent=4))
            print('add the example to json file')
        # with open(os.path.join(data_dir, 'all.json'), 'wa', encoding='utf-8') as f:
        #     f.writelines(json.dump(example, ensure_ascii=False))
        self.bs_ix = index.create_in(self.index_dir, self.schema, indexname=self.qc)
        # 写入索引内容
        self.logger.info("writing bs {} corpus to index...".format(self.qc))
        self.bs_writer = self.bs_ix.writer()
        self.bs_writer.add_document(question=" ".join(example['question']), answer=" ".join(example['answer']), question_classification=example['question_classification'])
        self.bs_writer.commit()
        self.logger.info('add the example to whoosh index')
        return
    
    def delete_example(self, question, answer, question_classification, data_dir="QuestionAnswering/search_corpus"):
        # 重复检测
        assert type(question) == str
        with open(os.path.join(data_dir, self.qc + '.json'), 'r', encoding='utf-8') as f:
            questions = json.load(f)
            for temp_q in questions:
                if question == temp_q['question_whole'] and question_classification == temp_q['question_classification']:
                    questions.remove(temp_q)
                    print('delete the example from the json file')
                    self.logger.info('delete the example from the json file')
        with open(os.path.join(data_dir, self.qc + '.json'), 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=4)
            # f.writelines('\n' + json.dumps(example, ensure_ascii=False, indent=4))
        
        # rebuild 一下 删掉在里面的索引
        self.bs_ix = index.create_in(self.index_dir, self.schema, indexname=self.qc)
        # 写入索引内容
        self.logger.info("writing bs {} corpus to index...".format(self.qc))
        self.bs_writer = self.bs_ix.writer()
        self._write_bs_corpus()
        self.bs_writer.commit()
        self.logger.info("writing bs {} corpus size is {}".format(self.qc, self.bs_ix.doc_count()))
        self.logger.info("writing bs {} corpus done!".format(self.qc))
        # seg_question = list(jieba.cut(question))
        # seg_ans = list(jieba.cut(answer))
        # try:
        #     # searcher = self.bs_ix.searcher(weighting=scoring.BM25F)
        #     # # 解析query
        #     # # 检索"question"和"answer"的field,指标是BM25
        #     # og = qparser.OrGroup.factory(0.9)
        #     # parser = qparser.QueryParser("question", schema=self.bs_ix.schema, group=og)
        #     # query = parser.parse(" ".join(seg_question))
        #     searcher = self.bs_ix.searcher()
        #     doc_num = searcher.document_number(question=' '.join(seg_question), answer=' '.join(seg_ans) ,question_classification=question_classification)
            
        #     # raise IndexError('GG 没有删除成功')
        #     if doc_num:
        #         self.bs_writer = self.bs_ix.writer()
        #         self.bs_writer.delete_document(doc_num)
        #         self.bs_writer.commit()
        #         self.logger.info('delete the example from the whoosh index')
        #         print('delete the example from the whoosh index')
        #     else:
        #         raise IndexError('GG 没有删除成功')
        # except IndexError:
        #     print(f'delete error and delete 0 item in whoosh index')
        #     self.logger.info(f'delete error and delete 0 item in whoosh index')


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
