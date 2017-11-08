请点击上面的 ↑【Preview】标签↑ 查看格式化后的说明。

阅读完毕后，请点击上面的【 Write】标签，先【删除】本说明内容，然后描述你遇到的问题。

---
## 常见问题：  
* 扫描不到GAE的ip  
   请尝试启用IPv6，参考  
   https://github.com/XX-net/XX-Net/wiki/%E5%A6%82%E4%BD%95%E5%BC%80%E5%90%AFIPv6    
   
   或者试试X-Tunnel 模块  
   https://github.com/XX-net/XX-Net/wiki/x-tunnel%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B  
   
* X-Tunnel 流量丢失  
  先确认采用最新的版本，能够正常登录x-tunnel。
  请给xxnet.dev@gmail.com 发邮件
  
* X-tunnel 无法连接  
  如果能够登录，请确认代理端口为1080.
  如果速度不稳定或无法登录，请贴出X-Tunnel 的Status页面。
   
---
## 提问之前
1. 首先请确认你使用的是[最新版本](https://github.com/XX-net/XX-Net/blob/master/code/default/download.md)，你的问题可能已经在新版本里解决了。
2. 请阅读[故障速查手册](https://github.com/XX-net/XX-Net/wiki/故障速查手册)，大部分问题都能在这里找到答案。
3. 请在 [issue](https://github.com/XX-net/XX-Net/issues) 区搜索有无类似的问题。

---
## 问题内容
1. 请尽可能详细的描述你的问题，如问题能重现请附带重现方法。
2. 当你的问题得到解决后，记得关闭问题。
3. 可以参考[示例 issue](https://github.com/XX-net/XX-Net/issues/3193)。

### 附加内容
1. 提交 issue 时请贴出诊断信息、GAEProxy 日志，以便开发者和其他用户更好地帮助你。
2. 如果是部署相关的问题，请一并附带部署日志。
3. 如果你有任何与这个问题有关的信息，也请一并发出来。
4. 如果你没有提供诊断信息，我们很可能会忽略这个问题。

#### 获取诊断信息
点击[状态页](http://127.0.0.1:8085)下方的【诊断信息】按钮，如没有这个按钮，请将显示详细信息从【OFF】改为【ON】。

#### 获取日志
打开 [GAEProxy 日志页](http://127.0.0.1:8085/?module=gae_proxy&menu=logging) 复制网页右边部分的内容。
