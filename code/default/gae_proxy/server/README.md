## 修改密码：
编辑gae.py 里的 __password__

## 下载gcloud
https://cloud.google.com/sdk/docs/install

## 安装:
`./google-cloud-sdk/install.sh`

## 登陆google账户，选择部署的appid
 `gcloud init`

## 部署：
`cd XX-Net/code/default/gae_proxy/server/gae`  
`gcloud app deploy`  
`gcloud app deploy cron.yaml`  


## 配置代理
  https://cloud.google.com/sdk/docs/proxy-settings
  