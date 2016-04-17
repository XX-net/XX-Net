


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
strExecutable = quo & strCurrentPath & "\code\" & strVersion & "\python27\1.0\python.exe" & quo
strArgs = strExecutable & " " & quo & strCurrentPath & "\code\" & strVersion & "\launcher\start.py" & quo
'WScript.Echo strArgs

Set oShell = CreateObject ("Wscript.Shell")
oShell.Run strArgs, isConsole(), false