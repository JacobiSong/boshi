# 部署文档

## 小程序代码部署
* 用微信小程序开发工具打开小程序项目，点击上传即可。
* 发布需要添加开发者的微信号为管理员。添加后可在[小程序后台](https://mp.weixin.qq.com/wxamp/index/index?lang=zh_CN&token=1778053258)进行管理。
  * 注意小程序的appid不要修改，使用程序默认即可。




## 后端服务部署
* 安装配置相关工具
  * Nginx
  * Nodejs
  * Django
  * Anaconda
  
* 将网页代码放在nginx的目录下
  * 一般为/usr/share/nginx
  
* 将问答系统代码和服务端放在 root 下, 放置之后的路径应该为：

  * root
    * wechat-im-master
    * remind
  * usr
    * share
      * nginx
        * html
        * module(自带)

* 进入remind文件夹，安装python包

  > cd remind
  >
  > conda create -n bs python=3.6
  >
  > conda activate bs
  >
  > conda install --yes --file requirements.txt



## 后端服务启动

### 网页后台部分

> cd wechat-im-master/.server
>
> node https_server.js

### 问答系统部分

>cd remind/qa_demo
>
>conda activate bs
>
>python manage.py runserver 0.0.0.0:82
