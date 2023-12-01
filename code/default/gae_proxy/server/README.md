## 设置使用密码：
如果你担心流量被别人使用，可以设置使用密码。  
编辑main.py 里的 __password____
注意在客户端中也需要设置一样的密码才能访问。  
一般你不泄露appid，别人是无法使用你的流量的。  

## 下载gcloud 并安装
https://cloud.google.com/sdk/docs/install

## 登陆google账户，选择部署的appid
  需要先指定代理服务器，可以使用X-tunnel作为代理服务器，端口1080。 
  `gcloud config set proxy/type socks5`  
  `gcloud config set proxy/address localhost`  
  `gcloud config set proxy/port 1080`   
  请先确认X-Tunnel 已经登陆并可以访问google服务。  

  参考这里：  
  https://cloud.google.com/sdk/docs/proxy-settings

  登陆并选择需要部署的appid：  
 `gcloud init`  
  

## 未绑定信用卡的需要绑定:
  https://console.cloud.google.com/billing/enable

## 部署：
`cd XX-Net/code/default/gae_proxy/server/gae`  
`gcloud app deploy`  

  