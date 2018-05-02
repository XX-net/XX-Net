function CreateShortcut() {
    wsh = new ActiveXObject('WScript.Shell');
    target_path = '"' + wsh.CurrentDirectory + '\\..\\..\\..\\start.vbs"';
    icon_path = wsh.CurrentDirectory + '\\web_ui\\favicon.ico';

    link = wsh.CreateShortcut(wsh.SpecialFolders("Desktop") + '\\XX-Net.lnk');
    link.TargetPath = target_path;
    link.Arguments = '';
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
