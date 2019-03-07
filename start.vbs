Function CurrentPath( fso )
    strPath = Wscript.ScriptFullName
    Set objFile = fso.GetFile(strPath)
    CurrentPath = fso.GetParentFolderName(objFile)
End Function

Function CurrentVersion( fso, strCurrentPath )
    strVersionFile = strCurrentPath & "/code/version.txt"

    If (fso.FileExists(strVersionFile)) Then

        Set objFileToRead = fso.OpenTextFile(strVersionFile, 1)
        CurrentVersion = objFileToRead.ReadLine() ' 读取文本中记录的版本号

        version_path = strCurrentPath & "/code/" & CurrentVersion & "/launcher/start.py"

        If( Not fso.FileExists(version_path) ) Then ' 确认读取的版本路径是否存在
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

Set fso = CreateObject("Scripting.FileSystemObject")
strCurrentPath = CurrentPath( fso )
strCurrentVersion = CurrentVersion( fso, strCurrentPath )
Dim strArgs
quo = """"

If isConsole() Then
    python_cmd = "python.exe"
Else
    python_cmd = "pythonw.exe"
End If

strExecutable = quo & strCurrentPath & "\code\" & strCurrentVersion & "\python27\1.0\" & python_cmd & quo
strArgs = strExecutable & " " & quo & strCurrentPath & "\code\" & strCurrentVersion & "\launcher\start.py" & quo
' WScript.Echo strArgs

Set oShell = CreateObject ("Wscript.Shell")
oShell.Run strArgs, isConsole(), false