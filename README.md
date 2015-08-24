
翻墙软件

XX-Net
========
项目状态：新用户启动后，需要等待一段时间（十分钟到1小时），扫描到足够ip之后会比较流畅   


下载链接：
==========
测试版：
https://codeload.github.com/XX-net/XX-Net/zip/2.1.2

稳定版：
https://codeload.github.com/XX-net/XX-Net/zip/2.0.5


查看历史版本：  
https://github.com/XX-net/XX-Net/releases
   
  
  

主要特性
========
* 集成GoAgent、GoGoTest等自动扫描IP，省事省力
* Web界面，人性化交互，傻瓜易用
* 内置了公共 appid, 方便新手
* 方便易用的细节、细节提示


平台支持情况
================
* Windows 7/8/10 （xp 需要 tcpip.sys 补丁, 比如用 tcp-z）
* Linux （Ubuntu不显示系统托盘）
* Mac OS X(10.7; 10.8; 10.9; 10.10)

## 链接
|   |   |
| --------   | :----  |
|问题报告:  |https://github.com/XX-net/XX-Net/issues|
|讨论群:  |https://groups.google.com/forum/#!forum/xx-net|
|Email:   |xxnet.dev at gmail.com|

使用方法：
========
* Windows下, 双击 start.lnk/start.vbs
  - 启动弹出浏览器： 访问 http://localhost:8085/
  - 托盘图标：点击可弹出Web管理界面, 右键可显示常用功能菜单。
  - Win7/8/10：提示请求管理员权限, 安装CA证书。请点击同意。
  - 推荐用Chrome浏览器, 安装SwichySharp, 可在swichysharp目录下找到插件和配置文件
  - Firefox 需手动导入证书 data/gae_proxy/CA.crt 启动后生成
* Linux下, 执行 start.sh
  - 自动导入证书，需安装 libnss3-tools 包
  - 没有安装PyGtk的，需要先安装gtk：sudo apt-get install python-gtk2
  - 第一次启动, 请用sudo ./start.sh, 以安装CA证书
  - 配置http代理 localhost 8087, 勾选全部协议使用这个代理。
    推荐Chrome + SwitchyOmega
* Mac下，双击 start.command
  - 会自动导入证书，如果还有提示非安全连接，请手动导入data/gae_proxy/CA.crt证书
  - 命令行启动方式：./start.sh
    推荐Chrome + SwitchyOmega
* 服务端
  - 协议采用3.3的版本，请重新部署服务端，服务端兼容3.1.x/3.2.x的客户端
  - 虽然系统内置了公共appid, 还是建议部署自己的appid，公共appid限制看视频

感谢
=========
* GoAgent
* GoGoTest
* goagentfindip
* checkgoogleip


如何帮助项目
==========
https://github.com/XX-net/XX-Net/wiki/How-to-contribute


附图
======

GAEProxy状态页面

![goagent_status](https://cloud.githubusercontent.com/assets/10395528/5849287/f71c62fc-a1b9-11e4-9ae0-b33fc78ed5fd.png)

GAEProxy 配置页面

![goagent_config](https://cloud.githubusercontent.com/assets/10395528/5849285/f68ac84c-a1b9-11e4-808a-5ec78f2fd3af.png)

GAEProxy 部署服务端页面

![goagent_deploy](https://cloud.githubusercontent.com/assets/10395528/5849286/f6e81dda-a1b9-11e4-94f8-2b9d2492bd39.png)

GAEProxy 查看日志页面

![goagent_log](https://cloud.githubusercontent.com/assets/10395528/5849288/f72138cc-a1b9-11e4-94df-d0b7ab160f0c.png)

集成XX-Net的项目
===============
* ChromeGAE
  主页：http://www.ccav1.com/chromegae
  集成Google Chrome和XX-Net的自动翻墙浏览器
  维护人：Yanu
* 集成Chrome和XX-Net
  https://github.com/yeahwu/chrome
* plusburg
  主页：https://github.com/Plusburg/Plusburg
  集成XX-Net的启动光盘镜像
* appifed-xx-net
  https://github.com/binarydist/appified-xx-net
  Mac OSX 环境下，变成一个标准的app
