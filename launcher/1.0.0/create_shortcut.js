
function CreateShortcut(target_path)
{
   wsh = new ActiveXObject('WScript.Shell');
   link = wsh.CreateShortcut(wsh.SpecialFolders("Desktop") + '\\XX-Net.lnk');
   link.TargetPath = target_path;
   link.Arguments = '"' + wsh.CurrentDirectory + '\\start.py"';
   link.WindowStyle = 7;
   link.Description = 'XX-Net';
   link.WorkingDirectory = wsh.CurrentDirectory;
   link.Save();
}


function main(){
    wsh = new ActiveXObject('WScript.Shell');
    if(wsh.Popup('Create shortcut on desktop?', 60, 'XX-Net', 1+32) == 1) {
        CreateShortcut('"' + wsh.CurrentDirectory + '\\..\\..\\python27\\1.0\\pythonw.exe"');
    }
}
main();
