
Function PreparePython()
    Set fso=CreateObject("Scripting.FileSystemObject")
      
    ' Check if python have installed.
    pythonDir = "python27\2.0\"
    If DirIsExist(pythonDir) then
        PreparePython = True
        Exit Function
    End If
    
    CreateDir("data")
    CreateDir("data\download")

    py_url = "https://www.python.org/ftp/python/2.7.17/python-2.7.17.msi"
    py_fn = "data\download\python.msi"
    If not DownloadAndCheckSize(py_url, py_fn, 19570688) then
        WScript.Echo "Download python env fail."
        PreparePython = False
        Exit Function
    End if
    py_extract_dir = "data\download\python\"
    call ExtractMsi(py_fn, py_extract_dir)

    call InstallLib("https://files.pythonhosted.org/packages/9e/de/f8342b68fa9e981d348039954657bdf681b2ab93de27443be51865ffa310/pyOpenSSL-19.1.0-py2.py3-none-any.whl", 53749)
    call InstallLib("https://files.pythonhosted.org/packages/28/ca/9b337cf6efe4d3f09066088d6a72a2216a11b121ce32de85fea209b440ea/cryptography-2.8-cp27-cp27m-win32.whl", 1262461)
    call InstallLib("https://files.pythonhosted.org/packages/0c/6f/08fa16905a358f36c3b13e0841acbfa98fde0d39edb091060b4ff975a1de/cffi-1.14.0-cp27-cp27m-win32.whl", 160416)
    call InstallLib("https://files.pythonhosted.org/packages/3d/50/5ce5dbe42eaf016cb9b062caf6d0f38018454756d4feb467de3e29431dae/pyasn1-0.4.8-py2.4.egg", 177299)
    call InstallLib("https://files.pythonhosted.org/packages/c5/db/e56e6b4bbac7c4a06de1c50de6fe1ef3810018ae11732a50f15f62c7d050/enum34-1.1.6-py2-none-any.whl", 12427)
    call InstallLib("https://files.pythonhosted.org/packages/c2/f8/49697181b1651d8347d24c095ce46c7346c37335ddc7d255833e7cde674d/ipaddress-1.0.23-py2.py3-none-any.whl", 18159)
    call InstallLib("https://files.pythonhosted.org/packages/65/eb/1f97cb97bfc2390a276969c6fae16075da282f5058082d4cb10c6c5c1dba/six-1.14.0-py2.py3-none-any.whl", 10938)
    call InstallLib("https://files.pythonhosted.org/packages/a3/58/35da89ee790598a0700ea49b2a66594140f44dec458c07e8e3d4979137fc/ply-3.11-py2.py3-none-any.whl", 49567)
    
    CreateDir("python27")
    call MoveDir("data\download\python", "python27\2.0")

    call RemoveDir("data\download")
    PreparePython = True
End Function

Function InstallLib(url, filesize)
    a = split(url, "/")
    fn = a(Ubound(a)) & ".zip"

    dfn = "data\download\" & fn
    If not DownloadAndCheckSize(url, dfn, filesize) then
        WScript.Echo "Download " & url & " fail."
        Wscript.Quit
    End if

    call UnzipFiles(dfn, "data\download\python\Lib\site-packages\")
End Function

Function DirIsExist(strPath)
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set shl = CreateObject("WScript.Shell")

    exists = fso.FolderExists(strPath)

    if (exists) then 
        DirIsExist = True
    Else
        DirIsExist = False
    end if
End Function

Function CreateDir(strPath)
    set filesys=CreateObject("Scripting.FileSystemObject") 
    If Not filesys.FolderExists(strPath) Then 
        Set newfolder = filesys.CreateFolder(strPath) 
    End If 
End Function

Function DownloadFile(url, strPath)
    dim xHttp: Set xHttp = createobject("Microsoft.XMLHTTP")
    dim bStrm: Set bStrm = createobject("Adodb.Stream")
    xHttp.Open "GET", url, False
    xHttp.Send

    with bStrm
        .type = 1 '//binary
        .open
        .write xHttp.responseBody
        .savetofile strPath, 2 '//overwrite
    end with

    DownloadFile = GetFileSize(strPath)
End Function

Function GetFileSize(strPath)
    set filesys=CreateObject("Scripting.FileSystemObject") 
    GetFileSize = filesys.GetFile(strPath).Size
End Function

Function DownloadAndCheckSize(url, path, size)
    For i = 1 to 3
        fs = DownloadFile(url, path)
        if fs = size then
            DownloadAndCheckSize = True
            Exit Function
        end if 
    Next
    DownloadAndCheckSize = False
End Function

Function GetAbslutePath(path)
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
    GetAbslutePath = fso.GetAbsolutePathName(path)
End Function

Sub ExtractMsi(fn, fd)
    afd = GetAbslutePath(fd)
    Set oShell = CreateObject ("Wscript.Shell")
    strCmd = "msiexec /quiet /passive /a " & fn & " /qn TARGETDIR=" & afd
    'WScript.Echo strCmd
    oShell.Run strCmd, 0, true
End Sub

Sub Unzip(ZipFile, ExtractTo)
    Dim objShell: set objShell = CreateObject("Shell.Application")
    Dim FilesInZip
    dim ns
    ZipFile = GetAbslutePath(ZipFile)
    ExtractTo = GetAbslutePath(ExtractTo)
    x = CreateDir(ExtractTo)
    set ns = objShell.NameSpace(ZipFile)
    set FilesInZip = ns.items()
    objShell.NameSpace(ExtractTo).CopyHere(FilesInZip)
End Sub

Sub UnzipFilesPowerShell(zipFile, targetDir)
    ' For Windows 10.
    cmd = "powershell -windowstyle hidden -command Expand-Archive -Path " & zipFile & " -DestinationPath " & targetDir
    Set objShell = CreateObject("Wscript.shell")
    objShell.run cmd, 0, true
End Sub

Sub UnzipFiles(zipFile, targetDir)
    'WScript.Echo "unzip " & zipFile
    'call UnzipFilesPowerShell(zipFile, targetDir)
    call Unzip(zipFile, targetDir)
End Sub

Sub MoveDir(srcDir, dstDir)
    srcDir = GetAbslutePath(srcDir)
    dstDir = GetAbslutePath(dstDir)
    set fs = CreateObject("Scripting.FileSystemObject")
    set folder = fs.GetFolder(srcDir)
    folder.Move dstDir
End Sub

Sub RemoveDir(strFolderPath)
    Dim objFSO, objFolder
    Set objFSO = CreateObject ("Scripting.FileSystemObject")
    If objFSO.FolderExists(strFolderPath) Then
        objFSO.DeleteFolder strFolderPath, True
    End If
End Sub


python_is_ready  = PreparePython()
If not python_is_ready then
    WScript.Echo "XX-Net Download Python Environment fail!"
    Wscript.Quit
End if

Function CurrentPath()
    strPath = Wscript.ScriptFullName
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    Set objFile = objFSO.GetFile(strPath)
    CurrentPath = objFSO.GetParentFolderName(objFile)
End Function

Function CurrentVersion()
    strCurrentPath = CurrentPath()
    strVersionFile = strCurrentPath & "/code/version.txt"

    Set fso = CreateObject("Scripting.FileSystemObject")
    If (fso.FileExists(strVersionFile)) Then

        Set objFileToRead = CreateObject("Scripting.FileSystemObject").OpenTextFile(strVersionFile,1)
        CurrentVersion = objFileToRead.ReadLine()

        version_path = strCurrentPath & "/code/" & CurrentVersion & "/launcher/start.py"
        If( Not fso.FileExists(version_path) ) Then
            CurrentVersion = "default"
        End If

        objFileToRead.Close
        Set objFileToRead = Nothing
    Else
       CurrentVersion = "default"
    End If

End Function


Function isConsole()
    Set objArgs = Wscript.Arguments
    'WScript.Echo objArgs.Count
    'WScript.Echo objArgs(0)
    isConsole = 0
    If objArgs.Count > 0 Then
        if objArgs(0) = "console" Then
            isConsole = 1
        End If
    End If
End Function


strCurrentPath = CurrentPath()
strVersion = CurrentVersion()
Dim strArgs
quo = """"

If isConsole() Then
    python_cmd = "python.exe"
Else
    python_cmd = "pythonw.exe"
End If

strExecutable = quo & strCurrentPath & "\python27\2.0\" & python_cmd & quo
strArgs = strExecutable & " " & quo & strCurrentPath & "\code\" & strVersion & "\launcher\start.py" & quo
'WScript.Echo strArgs

Set oShell = CreateObject ("Wscript.Shell")
oShell.Environment("Process")("PYTHONPATH")=""
oShell.Environment("Process")("PYTHONHOME")=""
oShell.Run strArgs, isConsole(), false
