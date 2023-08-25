#!/usr/bin/python
# coding:utf-8



def post_process_dbqa_answer(dbqa_answer):
    '''
    dbqa答案的后处理
    1. 过滤字符<sep>，<eop>等
    :param dbqa_answer:
    :return:
    '''
    if dbqa_answer:
        for idx, para in enumerate(dbqa_answer['paras']):
            dbqa_answer['paras'][idx]['content'] = ''.join(para['content']).replace('<sep>', '？').replace('<eop>', '')
    return dbqa_answer


def post_process_qs_answer(qs_answer):
    '''
    问题相似度对应答案的后处理
    答案格式如下：
    {
        'question': list, 源问题
        'qas': [
                {
                    'question': list, 相似问题1
                    'answer': list, 对应答案1
                    'match_score': float, 检索系统得分
                    'sim_score': float, 模型匹配得分
                },
                {
                    ...
                }
                ...
        ]
    }
    :param qs_answer:
    :return:
    {
        'question': str, 源问题
        'best_answer': str, 最佳答案， 若匹配得分都较差则为空
        'qas': [
                {
                    'question': str, 相似问题1
                    'answer': str, 对应答案1
                    'match_score': float, 检索系统得分
                    'sim_score': float, 模型匹配得分
                },
                {
                    ...
                }
                ...
        ]
    }
    '''
    if qs_answer:
        best_answer = ''
        best_score = 0.0
        qs_answer['question'] = ''.join(qs_answer['question'])
        for qa in qs_answer['qas']:
            qa['question'] = ''.join(qa['question'])
            qa['answer'] = ''.join(qa['answer'])
            if qa['sim_score'] > best_score:
                best_score = qa['sim_score']
                best_answer = qa['answer']
        if best_score > 0.5:
            qs_answer['best_answer'] = best_answer
        else:
            qs_answer['best_answer'] = ''
    return qs_answer


def post_process_bs_qs_answer(qs_answer):
    """
    问题相似度对应答案的后处理
    答案格式如下：
    {
        'question': list, 源问题
        'qas': [
                {
                    'question': list, 相似问题1
                    'answer': list, 对应答案1
                    'match_score': float, 检索系统得分
                    'sim_score': float, 模型匹配得分
                },
                {
                    ...
                }
                ...
        ]
    }
    :param qs_answer:
    :return:
    {
        'question': str, 源问题
        'best_answer': str, 最佳答案， 若匹配得分都较差则为空
        'qas': [
                {
                    'question': str, 相似问题1
                    'answer': str, 对应答案1
                    'match_score': float, 检索系统得分
                    'sim_score': float, 模型匹配得分
                },
                {
                    ...
                }
                ...
        ]
    }
    """
    if qs_answer:
        best_answer = ''
        best_score = 0.0
        qs_answer['question'] = ''.join(qs_answer['question'])
        for qa in qs_answer['qas']:
            qa['question'] = ''.join(qa['question'])
            qa['answer'] = ''.join(qa['answer'])
            if qa['sim_score'] > best_score:
                best_score = qa['sim_score']
                best_answer = qa['answer']
        if best_score > 0.5:
            qs_answer['best_answer'] = best_answer
        else:
            qs_answer['best_answer'] = None
    return qs_answer


def post_process_bs_qs_answer_without_similarity_and_classification(qs_answer):
    """
    问题相似度对应答案的后处理
    答案格式如下：
    {
        'question': list, 源问题
        'qas': [
                {
                    'question': list, 相似问题1
                    'answer': list, 对应答案1
                    'match_score': float, 检索系统得分
                },
                {
                    ...
                }
                ...
        ]
    }
    :param qs_answer:
    :return:
    {
        'question': str, 源问题
        'best_answer': str, 最佳答案
        'qas': [
                {
                    'question': str, 相似问题1
                    'answer': str, 对应答案1
                    'match_score': float, 检索系统得分
                },
                {
                    ...
                }
                ...
        ]
    }
    """
    if qs_answer:
        best_answer = ''
        best_score = 0.0
        qs_answer['question'] = ''.join(qs_answer['question'])
        for qa in qs_answer['qas']:
            qa['question'] = ''.join(qa['question'])
            qa['answer'] = ''.join(qa['answer'])
            if qa['match_score'] > best_score:
                best_score = qa['match_score']
                best_answer = qa['answer']
        if best_score > 0.5:
            qs_answer['best_answer'] = best_answer
        else:
            qs_answer['best_answer'] = None
    return qs_answer


def post_process_dst_qs_answer(qs_answer):
    """
    问题相似度对应答案的后处理
    答案格式如下：
    {
        'question': list, 源问题
        'qas': [
                {
                    'question': list, 相似问题1
                    'answer': list, 对应答案1
                    'match_score': float, 检索系统得分
                    'sim_score': float, 模型匹配得分
                },
                {
                    ...
                }
                ...
        ]
    }
    :param qs_answer:
    :return:
    {
        'question': str, 源问题
        'best_answer': str, 最佳答案， 若匹配得分都较差则为空
        'qas': [
                {
                    'question': str, 相似问题1
                    'answer': str, 对应答案1
                    'match_score': float, 检索系统得分
                    'sim_score': float, 模型匹配得分
                },
                {
                    ...
                }
                ...
        ]
    }
    """
    if qs_answer:
        best_answer = ''
        best_score = 0.0
        qs_answer['question'] = qs_answer['question']
        for qa in qs_answer['qas']:
            # qa['question'] = qa['question']
            # qa['answer'] = ''.join(qa['answer'])
            if qa['sim_score'] > best_score:
                best_score = qa['sim_score']
                best_answer = qa['answer']
        if best_score > 0.5:
            qs_answer['best_answer'] = best_answer
        else:
            qs_answer['best_answer'] = None
    return qs_answer


def post_process_kbqa_answer(kbqa_answer):
    '''
    KBQA答案的后处理
    :return:
    '''
    # triple = kbqa_answer[0][:3]
    # score = kbqa_answer[0][3]
    # answer = triple[2]
    # new_answer = {
    #     'triple': triple,
    #     'score': score,
    #     'answer': answer,
    # }
    if kbqa_answer.get('answer', None):
        new_answer = {
            'answer': kbqa_answer.get('answer', None),
        }
        return new_answer
    return None
