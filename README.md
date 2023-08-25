# 部署文档

## 小程序代码部署
* 用微信小程序开发工具打开小程序项目，点击上传即可。
* 发布需要添加开发者的微信号为管理员。添加后可在[小程序后台](https://mp.weixin.qq.com/wxamp/index/index?lang=zh_CN&token=1778053258)进行管理。



## 后端服务部署
* 安装配置相关工具
  * nginx
  * nodejs
* 将网页代码放在nginx的目录下
  * 一般为/usr/share/nginx
  
* 将问答系统代码和服务端放在 root 下
* 放置之后的路径应该为：
  * root
    * wechat-im-master
  * usr
    * share
      * nginx
        * html
        * module(自带)

* 放置完成之后，进入root/wechat-im-master，运行http_server.js开启服务
