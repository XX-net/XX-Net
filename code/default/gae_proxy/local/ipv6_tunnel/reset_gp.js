// coding:ANSI
// Detect and Reset Teredo Group Policy.
// This file is Microsoft JScript source code and needs to be compiled to binary.
// Compile with .Net Framwork's JScript compiler JScriptCompiler, 1.0 version not supported.
// jsc.exe /t:winexe /platform:anycpu /fast /out:x:\reset_gp.exe x:\reset_gp.js
// reset_gp.exe.config is .Net Framwork Version Compatibility Profile.
// Windows 2000 must have .Net Framwork 1.0 or higher installed to run this program.

function BinaryFile(filepath){
    this.path = filepath;
    this._initNewStream = function(){
        var Stream = new ActiveXObject('ADODB.Stream');
        Stream.Type = 2;
        Stream.CharSet = 'iso-8859-1';
        Stream.Open();
        return Stream;
    }
    this.WriteAll = function(content){
        var Stream = this._initNewStream();
        Stream.WriteText(content);
        Stream.SaveToFile(this.path, 2);
        Stream.Close();
    }
    this.ReadAll = function(){
        var Stream = this._initNewStream();
        Stream.LoadFromFile(this.path);
        var content = Stream.ReadText();
        Stream.Close();
        return content;
    }
}

import System.Windows.Forms;

var Wsr = new ActiveXObject('WScript.Shell');
var gp_split = '[\x00';
var gp_teredo = 'v6Transition\x00;Teredo'.split('').join('\x00');
var gp_regpol_filename = Wsr.ExpandEnvironmentStrings('%windir%') + '\\System32\\GroupPolicy\\Machine\\Registry.pol';
var gp_regpol_file = new BinaryFile(gp_regpol_filename);
var gp_regpol_old = gp_regpol_file.ReadAll().split(gp_split);
var gp_regpol_new = new Array();

for (var i=0; i<gp_regpol_old.length; i++) {
    var gp = gp_regpol_old[i];
    if (gp.indexOf(gp_teredo) == -1) {
        gp_regpol_new.push(gp);
    }
}

var result;
if (gp_regpol_new.length != gp_regpol_old.length) {
    result = MessageBox.Show(
        'Found Group Policy Teredo settings, do you want to reset it?',
        'Notice',
        MessageBoxButtons.OKCancel,
        MessageBoxIcon.Warning,
        MessageBoxDefaultButton.Button1
    );
}

var cmd = 'for /f "tokens=2 delims=[" %a in (\'ver\') do (' +
'for /f "tokens=2 delims= " %b in ("%a") do (' +
'for /f "tokens=1 delims=]" %c in ("%b") do (' +
'if %c lss 5.1 (' +
'secedit /refreshpolicy machine_policy /enforce' +
') else (' +
'gpupdate /target:computer /force))))';

if (result == DialogResult.OK) {
    gp_regpol_file.WriteAll(gp_regpol_new.join(gp_split));
    Wsr.Run("cmd.exe /c " + cmd, 0, true);
}

