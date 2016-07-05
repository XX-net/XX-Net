#!/bin/sh

#
BaseDir=$(cd "`dirname "$0"`"; pwd)
ContentsDir=`dirname "$BaseDir"`
CurAppDir=`dirname "$ContentsDir"`

export LANG=`defaults read -g AppleLocale`

if [[ $LANG = zh_CN* ]]; then
	LANG_ErrorMessage="未找到 XX-Net"

	LANG_PromptTitle="创建应用程序"
	LANG_PromptLine1="找到 XX-Net"
	LANG_PromptLine2="您要在“应用程序“文件夹中创建 XX-Net 程序吗？"
	LANG_PromptNever="不再提示"
	LANG_PromptCreate="创建应用程序"

	LANG_InfoCreated="已创建应用程序"
	LANG_InfoMessage="您可以在“应用程序文件”夹中启动它。"
	LANG_InfoDeletable="可被删除"
else
	LANG_ErrorMessage="XX-Net Not Found"

	LANG_PromptTitle="Create XX-Net Application"
	LANG_PromptLine1="XX-Net Found"
	LANG_PromptLine2="Do you want to create XX-Net application in Applications Foler?"
	LANG_PromptNever="Never"
	LANG_PromptCreate="Create"

	LANG_InfoCreated="Application Created"
	LANG_InfoMessage="You can launch it from Applications Folder."
	LANG_InfoDeletable="can be deleted"
fi

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
	osascript -e "display alert \"$LANG_ErrorMessage\" message \"$XXNetDir\" as critical"
	exit -1
fi

#
AppName=`basename "$CurAppDir"`
AppDir="/Applications/$AppName"
echo $AppDir
if [ -d "$AppDir" ]; then
	"$StartPath"
	exit 1
fi

#
osascript -e "display dialog \"$LANG_PromptLine1\n\n$XXNetDir\n\n$LANG_PromptLine2\" with title \"$LANG_PromptTitle\" with icon note buttons {\"$LANG_PromptNever\", \"$LANG_PromptCreate\"} default button 2 cancel button 1"
if [ $? == 0 ]; then
	cp -a "$CurAppDir" /Applications/
	cp -a "$XXNetDir" "$AppDir/XX-Net"
	rm -rf "$AppDir/XX-Net/$AppName"
	osascript -e "display alert \"$LANG_InfoCreated\n$AppDir\" message \"$LANG_InfoMessage\n($XXNetDir $LANG_InfoDeletable)\""
	exit 2
fi

#
ln -s "$XXNetDir" "$XXNetDir0"
"$StartPath"
exit 1
