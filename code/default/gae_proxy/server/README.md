Uploader command line usage:    
    <code>python uploader.py YourAppid1|YourAppid2|YourAppid3...</code>    
or    
    <code>..\..\python27\1.0\python.exe uploader.py YourAppid1|YourAppid2|YourAppid3...</code>    
if you don't have python2 installed.

Note:    
* Keep the path name as server, other wise upload can't work.
* Appid support combind multi appid with |.
* RC4 password no longer supported by default. If you want to set a password, please modify uploader.py, line 197 from
  * <code>uploads(appids)</code>
  * to
  * <code>uploads(appids,"YourPassword")</code>
