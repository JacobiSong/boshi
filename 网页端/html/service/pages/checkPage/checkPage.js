data = []
faq = []
// label_list = []
map = {}

function getData() {
    getQAPairs()
    // getQAPairs_in_database()
}

function add_new_label() {
    // 添加新的产品类别标签
    new_label_str = document.getElementById("add_new_label_input").value
    console.log(new_label_str)
    console.log("WebSocket" in window)
    
    console.log('start to send')
    var ws = new WebSocket("wss://boshitech.net:8001");
    var response = {}
    ws.onopen = function () {
        // console.log('get_data')
        response['type'] = "add_label"
        response['data'] = new_label_str
        ws.send(JSON.stringify(response));
    };
    ws.onmessage = function() {};
    ws.onclose = function () {};
    
}

function getQAPairs() {
    /*
     * @return:
     *      返回一个包含所有问答对的list，每个问答对的形式为一个dict，dict中包含三个键：id、question、answer
     */
    if ("WebSocket" in window) {
        var ws = new WebSocket("wss://boshitech.net:8001");
        var response = {}
        ws.onopen = function () {
            // console.log('get_data')
            response['type'] = "get-question-history"
            response['data'] = ' '
            ws.send(JSON.stringify(response));
        };
        ws.onmessage = function (evt) {
            label_list = []
            received_msg = evt.data;
            // console.log(received_msg)
            var obj = JSON.parse(received_msg);
            var id = 0
            label_list = obj['labels']
            // console.log()
            obj = obj['content']
            if (obj != null) {
                for (var va in obj) {
                    id += 1
                    data.push({ 'id': id, 'question': va, 'answer': obj[va]['answer'], "frequency": obj[va]['count'], 'label': obj[va]['label'] })
                }
            }
            // console.log(data)
            let qaPairs = data.sort(function (a, b) { return - a['frequency'] + b['frequency'] })
            let htmls = ""

            console.log("qapairs")
            console.log(data)

            for (let i in qaPairs) {
                let qaPair = qaPairs[i]
                let id = qaPair['id']
                map[id] = i
                let question = qaPair['question']
                let answer = qaPair['answer']
                htmls += construct_new_html(id, question, answer, label_list)
            }
            $('#qa_table_tbody').html("")
            $('#qa_table_tbody').html(htmls)
        };
        ws.onclose = function () { };
    }

}



function get_label_list() {
    /*
     *  查询库中的问题类别列表，用于构造selector 
     */
    // this.label_list = []
    //TODO
    response = {}
    var ws = new WebSocket("wss://boshitech.net:8001");
    ws.onopen = function () {
        // console.log('get_data')
        response['type'] = "get-history"
        // response['data'] = result
        ws.send(JSON.stringify(response));
    };
    ws.onmessage = function (evt) {
        received_msg = evt.data;
        // console.log(received_msg)
        received_msg = JSON.parse(received_msg)
        received_msg = received_msg['content']['related_question']
        for (var item in received_msg) {
            label_list.push(received_msg[item]['text'])
        }
    };
    ws.onclose = function () { };
    console.log(label_list)
    return label_list
}


function construct_new_html(id, question, answer, label_list) {
    // 构造入库界面

    let label_selector_html = '<select id="' + id + '_label_textarea" lay-verify="">' +
        '<option value="-">请选择类别</option>'
    // label_list = []
    // get_label_list(label_list)
    // console.log(label_list)
    for (var label_idx in label_list) {
        // console.log(label_list[label_idx])
        label_selector_html += '<option value=' + label_list[label_idx] + '>' + label_list[label_idx] + '</option>'
    }
    label_selector_html += '</select>'

    let new_html = ""
    new_html += '<tr><td><button class ="layui-btn layui-btn-sm" id="'+ id + '" onclick="submit_single_pair(this.id)">入库</button></td>' +
        '<td>' +
        // '<textarea placeholder="'+label+'" id="'+id+'_label_textarea"></textarea>'+
        label_selector_html +
        '</td>' +
        '<td>' + 
        '<textarea id="' + id + '_question_textarea" style="width: 100%">' + question + '</textarea>' +
        '</td>' +
        '<td>' + 
        '<textarea id="' + id + '_answer_textarea" style="width: 100%">' + answer + '</textarea>'+ 
        '</td>'

    return new_html

}


function submit_single_pair(id) {
    // 单独提交问答对的函数在这里
    // 输入值为问答对的ID， 直接查找即可
    console.log("button", id)


    var label = document.getElementById(id + "_label_textarea").value
    if (label == "-") {
        // label = document.getElementById(id + "_label_textarea").placeholder
        alert("未选择类别")
        return
    }
    // else{
    //     console.log("label: ", label)
    // }


    result = []
    $("#" + id).addClass('layui-btn-disabled')
    
    // var item = data[map[id]]
    // var question = item['question']
    // var answer = item['answer']
    // var label = item['label']

    /* 
        Get the input question.
        If nothing is input, get the placeholder.
    */ 
    var question_textarea = document.getElementById(id + "_question_textarea")
    var question = question_textarea.value
    if (question == "")
    {
        question = question_textarea.placeholder
    }
    /* 
        Get the input answer.
        If nothing is input, get the placeholder.
    */ 
    var answer_textarea = document.getElementById(id + "_answer_textarea")
    var answer = answer_textarea.value
    if (answer == "")
    {
        answer = answer_textarea.placeholder
    }
    
    /* 
        Console Printing line for test.
    */ 
    console.log("id:", id, "question:", question, "answer:", answer, "label", label)
    // return label

    result.push({ 'question': question, 'answer': answer, 'label': label })
    console.log(result)
    // return 
    response = {}
    if ("WebSocket" in window) {
        var ws = new WebSocket("wss://boshitech.net:8001");
        ws.onopen = function () {
            // console.log('get_data')
            response['type'] = "upload-corpus"
            response['data'] = result
            ws.send(JSON.stringify(response));
        };
        ws.onmessage = function (evt) {
            received_msg = evt.data;
            console.log(received_msg)
        };
        ws.onclose = function () { };
    }

}






//////////////////////////////////////////
//    删除部分                           //
//////////////////////////////////////////


function getQAPairs_in_database() {
    /*
     * 这个函数目前的内容是我直接复制上面入库函数的代码，删除的话应该改一下qa_paires的获取方式就可以
     * @return:
     *      返回一个包含所有数据库中的问答对的list，每个问答对的形式为一个dict，dict中包含三个键：id、question、answer
     */

    /*
    * 9.20 新增类别选择
    */
    // let selector = document.getElementById('delete_product_category_selector')
    // let index = selector.selectedIndex
    // console.log(index)
    faq = []
    // let category_to_check = selector.options[index].value 
    // console.log(category_to_check)
    // return category_to_check
    //category_to_check 就是要查询的类别的文本字符串

    /* 
    * 11.23 将 selector 替换为 textarea
    */
    let category_to_check = document.getElementById('delete_product_category_selector').value


    if ("WebSocket" in window) {
        var ws = new WebSocket("wss://boshitech.net:8001");
        var response = {}
        ws.onopen = function () {
            // console.log('get_data')
            response['type'] = "get-faq-question"
            response['data'] = category_to_check
            ws.send(JSON.stringify(response));
        };
        ws.onmessage = function (evt) {
            received_msg = evt.data;
            // console.log(received_msg)
            var obj = JSON.parse(received_msg);
            var id = 0
            if (obj != null) {
                for (var va in obj) {
                    id += 1
                    // console.log(va)
                    // console.log(obj[va])
                    faq.push({ 'id': id, 'question': va, 'answer': obj[va]['answer'], "frequency": obj[va]['count'], 'label': obj[va]['label'] })
                }
            }
            console.log(faq)
            let qaPairs = faq.sort(function (a, b) { return - a['frequency'] + b['frequency'] })
            let htmls = ""
            for (let i in qaPairs) {
                let qaPair = qaPairs[i]
                let id = qaPair['id']
                map[id] = i
                let question = qaPair['question']
                let answer = qaPair['answer']
                htmls += construct_new_html_in_delete_page(id, question, answer)
            }
            $('#qa_indatabase_tbody').html("")
            $('#qa_indatabase_tbody').html(htmls)
        };
        ws.onclose = function () { };
    }
}

function delete_single_pair(id) {
    // 单独删除某个问答对
    // input 为要删除的问答对的id，直接查找即可

    id = String(id)
    id = id.substring(7)
    console.log("button delete", id)
    $("#delete_" + id).addClass('layui-btn-disabled')

    var item_id = map[id]
    var item = faq[item_id]
    // console.log(item)
    var response = {}
    if ("WebSocket" in window) {
        var ws = new WebSocket("wss://boshitech.net:8001");
        ws.onopen = function () {
            // console.log('get_data')
            response['type'] = "delete-question"
            response['data'] = { 'question': item['question'], 'answer': item['answer'], 'label': item['label'] }
            ws.send(JSON.stringify(response));
        };
        ws.onmessage = function (evt) {
            received_msg = evt.data;
            console.log(received_msg)
        };
        ws.onclose = function () { };
    }
    $("#" + id).addClass('layui-btn-disabled')

}

function construct_new_html_in_delete_page(id, question, answer) {
    // 添加前端html代码，不用动
    let new_html = ""
    new_html += '<tr><td><button class ="layui-btn layui-btn-sm" id="delete_' + id + '" onclick="delete_single_pair(this.id)">删除</button></td><td>' + question + '</td><td>' + answer + '</td>'
    return new_html

}


function submit_new_qapair() {
    /*
     * 提交新问答对，函数中参数
     *      new_question：问题文本
     *      new_label：问题标签
     *      new_answer： 问题答案
     * 最好在提交之后能给一个返回值，这样可以探出一个确认窗口（现在是 if_submit）
     */
    console.log('submit')
    let new_question = document.getElementById('new_question_input').value
    let new_label = document.getElementById('new_label_input').value
    let new_answer = document.getElementById('new_answer_input').value

    // console.log(new_question)
    // console.log(new_label)
    // console.log(new_answer)
    result = []

    result.push({ 'question': new_question, 'answer': new_answer, 'label': new_label })
    console.log(result)
    response = {}
    if ("WebSocket" in window) {
        var ws = new WebSocket("wss://boshitech.net:8001");
        ws.onopen = function () {
            console.log('get_data')
            response['type'] = "upload-corpus"
            response['data'] = result
            ws.send(JSON.stringify(response));
            // alert("提交成功");
        };
        ws.onmessage = function (evt) {
            received_msg = evt.data;
            console.log(received_msg)
            // alert("提交成功");
        };
        ws.onclose = function () { };
    }
    alert("提交成功");

}