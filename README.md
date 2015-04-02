叉叉Net
========



下载链接：
==========
https://codeload.github.com/XX-net/XX-Net/zip/1.7.0

版本历史： https://github.com/XX-net/XX-Net/releases
   
  
  

主要特性
========
* GoAgent 稳定快速
* Web界面，傻瓜易用
* 内置了公共 appid, 上千可用ip, 开箱即用
* 自动导入证书

## XX-Net不是匿名工具 
详情请看：  
https://github.com/XX-net/XX-Net/wiki/Anonymous-and-Security


平台支持情况
================
* Windows XP （需要 tcpip.sys 补丁, 比如用 tcp-z）
* Win7/8/10
* Ubuntu （不显示系统托盘）
* Debian
* Mac OS X

## 链接
|   |   |
| --------   | :----  |
|问题报告:  |https://github.com/XX-net/XX-Net/issues|
|讨论群:  |https://groups.google.com/forum/#!forum/xx-net|
|Email:   |xxnet.dev at gmail.com|

使用方法：
========
* Windows下, 双击 start.lnk/start.bat/start.vbs 快捷方式
  - 启动弹出浏览器： 访问 http://localhost:8085/
  - 托盘图标：点击可弹出Web管理界面, 右键可显示常用功能菜单。
  - Win7/8/10：提示请求管理员权限, 安装CA证书。请点击同意。
  - 第一次启动, 会提示在桌面建立快捷方式,可根据自己需要选择。
  - 推荐用Chrome浏览器, 安装SwichySharp, 可在swichysharp目录下找到插件和配置文件
  - Firefox 需手动导入证书 data/goagent/CA.crt 启动后生成
* Linux下, 执行 start.sh
  - 自动导入证书，需安装 libnss3-tools 包
  - 第一次启动, 请用sudo ./start.sh, 以安装CA证书
  - 配置http代理 localhost 8087, 勾选全部协议使用这个代理。
* Mac下，双击 start.command
  - 会自动导入证书，如果还有提示非安全连接，请手动导入data/goagent/CA.crt证书
* 服务端
  - 协议采用3.1的版本，请重新部署服务端，新版服务端兼容3.2的客户端
  - 虽然系统内置了公共appid, 还是建议部署自己的appid，公共appid限制看视频

感谢
=========
* GoAgent
* GoGoTest
* goagentfindip
* checkgoogleip





附图
======

GoAgent状态页面

![goagent_status](https://cloud.githubusercontent.com/assets/10395528/5849287/f71c62fc-a1b9-11e4-9ae0-b33fc78ed5fd.png)

GoAgent 配置页面

![goagent_config](https://cloud.githubusercontent.com/assets/10395528/5849285/f68ac84c-a1b9-11e4-808a-5ec78f2fd3af.png)

GoAgent 部署服务端页面

![goagent_deploy](https://cloud.githubusercontent.com/assets/10395528/5849286/f6e81dda-a1b9-11e4-94f8-2b9d2492bd39.png)

GoAgent 查看日志页面

![goagent_log](https://cloud.githubusercontent.com/assets/10395528/5849288/f72138cc-a1b9-11e4-94df-d0b7ab160f0c.png)
