# 部署工具使用方法
## Windows 用户
1. 在资源管理器打开 server 目录(就是这个文件所在的文件夹)。
2. 在资源管理器的空白处 Shift + 右键，在弹出的菜单里选择"在此处打开命令行窗口"。
3. 输入下面的命令来部署服务端：  
   <code>uploader.bat \<appids\> [-debug] [-password rc4_password]</code> 
4. 例子：  
   部署 xxnet-1|xxnet-2|xxnet-3 这三个 appid  
   <code>uploader.bat "xxnet-1|xxnet-2|xxnet-3"</code>  
   开启调试输出并部署 xxnet-1 这个 appid  
   <code>uploader.bat "xxnet-1" -debug</code>  
   使用 123456 作为 RC4 密码并部署 xxnet-1 这个 appid  
   <code>uploader.bat "xxnet-1" -password 123456</code>  
   开启调试输出，使用 123456 作为 RC4 密码并部署 xxnet-1 这个 appid  
   <code>uploader.bat "xxnet-1" -debug -password 123456</code>

## Linux & Mac 用户
1. 打开终端并 cd 到 server 目录。
2. 参考 Windows 用户的说明，并将执行 <code>uploader.bat</code> 改为执行 <code>python uploader.py</code>。

## 其他
0. 确保运行部署时本地127.0.0.1：8087代理在正常运行，否则部署不成功（此处直接运行好XX-NET即可）
1. 请保证当前目录为 server，在其他目录部署脚本将无法工作。
2. 多个 Appid 之间用 | 来分割，同时为了避免 | 被识别为管道，Appid 需要被引号包裹。  
   如：<code>"xxnet-1|xxnet-2|xxnet-3"</code>。
3. 参数解释：
  * -debug 开启调试输出
  * -password 设置 RC4 密码
