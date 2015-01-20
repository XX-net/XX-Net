叉叉网(XX-Net)


主要特性
========

* GoAgent 集成搜索 google ip
* 基于Web 的配置界面、上传部署、Log查看
* 内置了公共 appid, 安装即可上网, 注册自己的google appid
* 新版本提示、更新升级

平台支持情况
================
* Windows XP （需要 tcpip.sys 补丁, 比如用 tcp-z）
* Win7
* Win8
* Ubuntu （不能显示系统托盘）
* Debian
* Mac OS X 暂时未调试， 下一个版本解决

## 链接
|   |   |
| --------   | :----  |
|下载: |https://codeload.github.com/XX-net/XX-Net/zip/1.0.0|
|问题报告:  |https://github.com/XX-net/XX-Net/issues|
|讨论群:  |https://groups.google.com/forum/#!forum/xx-net|
|Email:   |xxnet.dev at gmail.com|


使用方法：
========
* Windows下, 双击 start.lnk 快捷方式
  启动会弹出浏览器 访问 http://localhost:8085/
  托盘图标点击可弹出Web管理界面, 右键可显示常用功能菜单。
  Win7会提示请求管理员权限, 安装CA证书。请点击同意。
  第一次启动, 会提示在桌面建立快捷方式,可根据自己需要选择。
  推荐用Chrome浏览器, 安装SwichySharp, 可在goagent/3.1.30/local/plugin 下找到插件和配置文件
* Linux下, 执行 start.sh
  第一次启动, 请用sudo ./start.sh, 以安装CA证书
  配置http代理 localhost 8087, 勾选全部协议使用这个代理。
* 虽然系统内置了公共appid, 还是建议部署自己的appid

感谢
=========
* GoAgent
* GoGoTest
* goagentfindip
* checkgoogleip
