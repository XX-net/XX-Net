#!/bin/sh

#
BaseDir=$(cd `dirname $0`; pwd)
ContentsDir=`dirname $BaseDir`
CurAppDir=`dirname "$ContentsDir"`

export LANG=zh_CN.UTF-8

#
XXNetDir0="$CurAppDir/XX-Net"
StartPath="$XXNetDir0/start"
if [ -f "$StartPath" ]; then
	echo "$StartPath"
	"$StartPath"
	exit 0
fi

#
XXNetDir=`dirname "$CurAppDir"`
StartPath="$XXNetDir/start"
if [ ! -f "$StartPath" ]; then
	osascript -e "display alert \"未找到 XX-Net\" message \"$XXNetDir\" as critical"
	exit -1
fi

#
AppName=`basename "$CurAppDir"`
AppDir="/Applications/$AppName"
echo $AppDir
if [ -d "$AppDir" ]; then
	$StartPath
	exit 1
fi

#
osascript -e "display dialog \"找到 XX-Net\n\n$XXNetDir\n\n您要在“应用程序“文件夹中创建 XX-Net 程序吗？\" with title \"创建应用程序\" with icon note buttons {\"不再提示\", \"创建\"} default button 2 cancel button 1"
if [ $? == 0 ]; then
	cp -a "$CurAppDir" /Applications/
	cp -a "$XXNetDir" "$AppDir/XX-Net"
	rm -rf "$AppDir/XX-Net/$AppName"
	osascript -e "display alert \"已创建应用程序\n$AppDir\" message \"您可以在“应用程序文件”夹中启动它。\n($XXNetDir 可被删除)\""
	exit 2
fi

#
ln -s "$XXNetDir" "$XXNetDir0"
$StartPath
exit 1
