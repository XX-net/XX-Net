# 部署工具使用方法
## Windows 用户
1. 在资源管理器的空白处Shift + 右键，在弹出的菜单里选择"在此处打开命令行窗口"
2. 输入下面的命令来部署服务端：  
   <code>uploader.bat <appids> [-debug] [-password rc4_password]</code> 
3. 例子  
   部署 xxnet-1|xxnet-2|xxnet-3 这三个 appid  
   <code>uploader.bat xxnet-1|xxnet-2|xxnet-3</code>  
   开启调试输出并部署 xxnet-1 这个 appid  
   <code>uploader.bat xxnet-1 -debug</code>  
   使用 123456 作为 RC4 密码并部署 xxnet-1 这个 appid  
   <code>uploader.bat xxnet-1 -password 123456</code>  
   使用 123456 作为 RC4 密码并开启调试输出并部署 xxnet-1 这个 appid  
   <code>uploader.bat xxnet-1 -debug -password 123456</code>

## Linux & Mac 用户
1. 打开终端并 cd 到 server 目录
2. 参考 Windows 用户的说明，并将 <code>uploader.bat</code> 改为 <code>python uploader.py</code>

## 其他
* 请保证当前目录为 server，在其他目录部署脚本将无法工作。
* 多个 Appid 之间用 | 来分割
* 参数解释
  * -debug 开启调试输出
  * -password 设置 RC4 密码
