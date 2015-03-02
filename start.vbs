Set oShell = CreateObject ("Wscript.Shell") 

strPath = Wscript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objFile = objFSO.GetFile(strPath)
strFolder = objFSO.GetParentFolderName(objFile) 

Dim strArgs
strArgs = strFolder & "/python27/1.0/pythonw.exe" & " " & strFolder & "/launcher/start.py"
oShell.Run strArgs, 0, false
