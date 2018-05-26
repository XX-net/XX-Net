function CreateShortcut() {
    wsh = new ActiveXObject('WScript.Shell');
    fso = new ActiveXObject("Scripting.FileSystemObject")
    system_folder = fso.GetSpecialFolder(1)
    target_path = '"' + system_folder + '\\wscript.exe"';
    argument_file = '"' + wsh.CurrentDirectory + '\\..\\..\\..\\start.vbs"';
    icon_path = wsh.CurrentDirectory + '\\web_ui\\favicon.ico';

    link = wsh.CreateShortcut(wsh.SpecialFolders("Desktop") + '\\XX-Net.lnk');
    link.TargetPath = target_path;
    link.Arguments = argument_file;
    link.WindowStyle = 7;
    link.IconLocation = icon_path;
    link.Description = 'XX-Net';
    link.WorkingDirectory = wsh.CurrentDirectory;
    link.Save();
}


function main() {
    CreateShortcut();
}

main();
