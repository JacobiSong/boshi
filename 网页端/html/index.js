let current_user_id = "";
var current_question = ""
var current_message = ""
var chat_history = {}
var finished_chat = {}
var showLog = true
var first = true
var users = {}
setInterval("check_chat_history()","20000");

function get_data() {
    /* 查询所有聊天对象的id，在加载页面过程中完成 */
    // 将滚轮放到最下方
    let div = document.getElementById('message-container');
    div.scrollTop = div.scrollHeight;
    get_all_user()
	console.log(users)
    // ############################################
    // 测试数据
    //all_user_id2name = {"user-1": "xiao ming", "user-2": "xiao hong", "user-3": "xiao li", "user-4": "xiaogang"}
    // ############################################
}

function get_all_user() {
    /*
     * 查询本机需要处理的所有会话的联系人
     * @params：
     *
     * @returns：
     *   user_id2name -> Dict:{id->string: name->string}
     *      eg:  {  (id)  : (name)
     *              user-1: 小明,
     *              user-2: 小红,
     *           }
     */
	 if ("WebSocket" in window){
		response = {}
        var ws = new WebSocket("wss://boshitech.net:8001"); 
        var myDate = new Date() 
		ws.onopen = function(){
            response['type'] = 'get-user-list';
            response['role'] = 0;
            ws.send(JSON.stringify(response));
        };    
        ws.onmessage = function (evt) { 
		    data = []
            received_msg = evt.data;
			users = JSON.parse(received_msg);
			if (users != null){
				for(va in users){
					if(!chat_history.hasOwnProperty(users[va])){
						chat_history[va] = []
						finished_chat[va] = []
						check_chat_history(va)
					}
				}
				show_all_chat(users)
			}
            ws.close()
        };       
        ws.onclose = function(){};
    }
	check_chat_history()
}

function check_chat_history() {
    /*
     * 查询当前用户下所有需要显示的聊天记录
     * @params：
     *   user_id -> string:  当前聊天的用户标识符
     * @returns：
     *   chat_history -> Dict:{key->string: value-> value}:
     *       所有需要显示的聊天记录，dict形式，键为聊天记录文本，值为消息发送方(0为对方发送，1为自己发送)
     *       eg:
     *           {
     *              "这是一条对方发来的消息": 0,
     *              "这是第一条本机发送的消息": 1,
     *              "这是第二条对方发来的消息": 0,
     *              "这是第二条本机发送的消息": 1
     *           }
     */
	 user_id = current_user_id
	 var finished = finished_chat[user_id]
	 var ret_chat = {}	 
	 if ("WebSocket" in window){
		response = {}
        var ws = new WebSocket("wss://boshitech.net:8001"); 
        var myDate = new Date() 
		ws.onopen = function(){
            response['type'] = 'get-question';
			response['user'] = user_id;
            response['role'] = 0;
            ws.send(JSON.stringify(response));
        };    
        ws.onmessage = function (evt) { 
		    data = []
            received_msg = evt.data;
			var obj = JSON.parse(received_msg);
			console.log(obj)
			chat_history[user_id] = []
			if (obj != null){
				if(obj['type'] == 0){
					obj = obj['infos']
					for(va in obj){
						chat_history[user_id].push({'question': va, 'answer':obj[va]})
					}
				}else{
					obj = obj['infos']
					for(var q in obj){
						console.log(q)
						console.log(obj[q])
						datat = obj[q]
						for(var q1 in datat){
							chat_history[q].push({'question':q1, 'answer': datat[q1]})
						}
					}
				}
				 choose_chat(current_user_id)
			}
            ws.close()
        };       
        ws.onclose = function(){};
    }	
}

function check_related_ans(user_id, question) {
    /*
     * 根据问题检索问题类型和相关答案
     * @params：
     *      user_id -> string: 当前聊天的用户标识符号
     *      question -> string: 待查询的问题
     * @return:
     *      type_and_ans -> Dict:    查询结果，包含两项: 问题类型和三个备选回答，具体如下：
     *          {
     *              "type" : questiong_type -> string,
     *              "ans"  : ans_list -> List[string],
     *          }
     */
	 var chats = chat_history[user_id]
	 var ret_chat = {}
	 console.log(chats)
	 for(va in chats){
		 va = chats[va]
		 if(va['question'] == question){
			 ret_chat['type'] = va['answer']['label']
			 ret_chat['answer'] = va['answer']['answer']
			 break
		 }
	 }
	 return ret_chat
}

function send_message(question, user_id, msg_str) {
    /*
     * 发送消息，返回消息发送状态(如果在本地缓存了聊天记录，则需要在这个函数里将新消息添加到聊天记录中！！！！前端代码中没有对应数据结构缓存聊天记录！！！！！！！)
     * @params:
     *   user_id -> string:    当前聊天的用户标识符
     *   msg_str -> string:    需要发送的消息内容
     * @return:
     *   status -> bool :      消息的发送状态
     */
	 console.log(question)
	 var chats = chat_history[user_id]
	 console.log(chats)
	 var response = {}
	 response['question'] = question
	 response['answer'] = msg_str
	 response['user'] = user_id
	 if ("WebSocket" in window){	
        var ws = new WebSocket("wss://boshitech.net:8001"); 	
        ws.onopen = function(){
            response['type'] = 'answer-question'
            response['role'] = 0;
            response['action'] = 'answer-question'
            ws.send(JSON.stringify(response));
			if(showLog){
				console.log('start to connect')
			}
            };    
        ws.onmessage = function (evt) { 
            ws.close()
        };       
        ws.onclose = function(){};
    }
	check_chat_history()
	return true
}

function show_all_chat(all_user_id2name) {
    /*
     * 添加所有的聊天会话
     * @params:
     *  all_user_id2name -> Dict:{id->string: name -> string}
     * @return:
     *  none
     */
	console.log(all_user_id2name)
    console.log("show all chat")
    // 首先删除原有的html
    let chat_user = document.getElementsByClassName('chat-user')[0]
    chat_user.innerHTML = ""

    // 逐个构造新的html
    let new_html = ""
    for (let id in all_user_id2name) {
        let html = add_new_chat(id, all_user_id2name[id])
        new_html += html
    }
    chat_user.innerHTML = new_html
}

function add_new_chat(user_id, user_name) {
	console.log('here')
	console.log(user_name)

    // 构造新的user-info
    html = '<div class="user-info layui-row" id="' + user_id + '" onclick="choose_chat(this.id)">\n' +
        '                <div class="layui-col-xs3 user-avatar">\n' +
        '                    <img src="C:/Users/super-tang/Desktop/service/resources/img/mine_fill.png">\n' +
        '                </div>\n' +
        '                <div class="layui-col-xs8 user-name" >' + user_name + '</div>\n' +
        '                <span class="layui-badge-dot layui-col-xs1 msg-tips"></span>\n' +
        '            </div> \n'
    return html
}

function add_agent_msg(msg) {

    // 构造新的本机消息气泡
    var html = ' <div class="message-agent">\n' +
        '                <div class="message-agent-time-sender message-time-sender">\n' +
        '                    <span class="">我</span>\n' +
        '                </div>\n';
    html += '  <div class="message-agent-content message-content">\n' +
        '        <div>' + msg + '</div>\n' +
        '    </div>\n' +
        '</div>\n';
    return html
}

function add_client_msg(user_id, msg) {
    // 构造新的客户消息气泡
    var html = ' <div class="message-client">\n' +
        '                <div class="message-client-time-sender message-time-sender">\n' +
        '                    <span class="">' + user_id + '</span>\n' +
        '                </div>\n';
    html += '  <div class="message-client-content message-content">\n' +
        '        <div>' + msg + '</div>\n' +
        '    </div>\n' +
        '    </div>\n';
    return html
}

function choose_chat(user_id) {
    // 选择聊天会话，将聊天记录显示在聊天框中，并将问题的相关信息检索出来

    /*
     * Part1:
     *      查询聊天记录并显示
     */

    // 查询聊天记录
    console.log("click", user_id)
    current_user_id = user_id

    chats = chat_history[current_user_id]
	console.log(chats)
	ret_chat = {}
	var index = 0
	for(va in chats){
		va = chats[va]
		console.log(va)
		if(va.hasOwnProperty('answer') && va['answer'].hasOwnProperty('answer')){
			var key = va['question'] + "#" + index
			ret_chat[key] = 0
			index += 1
		}else{
			if(va['question'] != ''){
				var key = va['question'] + "#" + index
				index += 1
				ret_chat[key] = 0
			}
			key = va['answer'] + "#" + index
			index += 1
			ret_chat[key] = 1
		}
	}
	console.log(ret_chat)
	chat_history1 = ret_chat

	console.log(chat_history1)

    // #######################################
    // 以下为测试数据
    // let chat_history = {}
    if(user_id == 'user-1'){
        chat_history={"你好我是小明1": 0, "你好小明1": 1, "小明和您说再见1": 0, "再见小明1": 1,"你好我是小明2": 0, "你好小明2": 1, "小明和您说再见2": 0, "再见小明2": 1,"你好我是小明3": 0, "你好小明3": 1, "小明和您说再见3": 0, "再见小明3": 1,"你好我是小明4": 0, "你好小明4": 1, "小明和您说再见4": 0, "再见小明4": 1,"你好我是小明": 0, "你好小明": 1, "颗粒是什么颜色的": 0} // data for test
    }else if(user_id == "user-2"){
        chat_history={"你好我是小红": 0, "你好小红": 1, "小红和您说再见": 0, "再见小红": 1,} // data for test
    }
    // #######################################

    const user_class = document.getElementsByClassName('message-container')
    // var message_client = document.getElementsByClassName("message-client")
    user_class[0].innerHTML = ''
    let new_HTML = ""
    let question = ""
    for (msg in chat_history1) {
		const reg = /#\d*/
        const sender = chat_history1[msg];
        msg = msg.replace(reg, "")
        // console.log(msg)
        if (sender == "1") {
            //
            new_HTML += add_agent_msg(msg)
        } else {
            new_HTML += add_client_msg(user_id, msg)
            question = msg
        }
    }
    user_class[0].innerHTML = '<div class="user-section"> \n' + new_HTML + '</div>\n'
    let div = document.getElementById('message-container');
    div.scrollTop = div.scrollHeight;


    /*
     * Part2:
     *      查询相关信息并显示
     */

     let related_ans = check_related_ans(user_id, question)
     let question_type = related_ans['type']
     let answers = related_ans['answer']


    // #######################################
    // 以下为测试数据
	if(!question_type){
     question = ""
     question_type = ""
     answers = ["", "", ""]
	}
    // #######################################
	

    current_question = question
    let question_input = document.getElementById('question_content')
    question_input.value = question
    let question_type_input = document.getElementById('question_type')
    question_type_input.value = question_type
    let answer1 = document.getElementById("related_answer1")
    answer1.value = answers[0]
    let answer2 = document.getElementById("related_answer2")
    answer2.value = answers[1]
    let answer3 = document.getElementById("related_answer3")
    answer3.value = answers[2]

}

function choose_an_answer(answer_block_id) {
    // 点击相关答案时，将对应答案填写到消息输入框中
    let answer_block = document.getElementById(answer_block_id)
    let answer_textarea = answer_block.children[0]
    const answer = answer_textarea.value;
    let msg_send_textarea = document.getElementById('msg-send-textarea')
    msg_send_textarea.innerHTML = ""
    msg_send_textarea.value = answer
    current_message = answer
}

function send_new_msg() {

    // 先对对话进行检查，如果未选择会话则不能发送消息
    if (current_user_id == "") {
        let msg_send_textarea = document.getElementById('msg-send-textarea')
        msg_send_textarea.value = ""
        alert("请先选择对话，再发送消息！");
        return;
    }

    // 对当前要发送的消息进行检查(如果选择了相关信息的备选答案，该答案会自动放入msg-send-textarea，所以直接获取消息输入框内容即可)
    current_message = document.getElementById('msg-send-textarea').value;
    if (current_message == "") {
        alert("不能发送空消息！");
        return;
    }

    // 与服务器通信，发送新消息
	var question = document.getElementById('question_content').value
    let send_status = send_message(question, current_user_id, current_message) // 与服务器通信，发送消息
    let new_msg_html = ""

    // ############################################################
    // 测试数据
    send_status = 1
    // ############################################################

    // 如果发送成功，则添加一个新的消息气泡
    if (send_status) {
        new_msg_html = add_agent_msg(current_message) // 构造新的本机消息气泡
    } else {
        alert("消息未发送，请检查网络！");  // 如果没有发送成功则弹窗
    }

    // 构造新的message-container内容
    let user_section_content = document.getElementsByClassName("user-section")[0].innerHTML
    let new_HTML = user_section_content + new_msg_html
    console.log(new_HTML)

    // 替换message_container内容
    const message_container = document.getElementsByClassName('message-container')[0]
    new_HTML = '<div class="user-section"> \n' + new_HTML + '</div>\n'
    message_container.innerHTML = new_HTML

    // 滚轮置底
    message_container.scrollTop = message_container.scrollHeight;

    // 清除输入框中残留内容
    let msg_send_textarea = document.getElementById('msg-send-textarea')
    msg_send_textarea.value = ""

    // 清除缓存区消息内容
    current_message = ""

}
