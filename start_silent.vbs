' AirFlick Drop - Silent Background Launcher
' Starts AirFlick minimized into the System Tray with zero CMD window popups
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir
WshShell.Run "pythonw.exe """ & currentDir & "\main_window.py"" --minimized", 0, False
