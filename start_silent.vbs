' AirFlick Drop - Silent Background App Launcher
' Runs AirFlick companion in system tray with zero CMD popups
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir
WshShell.Run "pythonw.exe """ & currentDir & "\main_window.py"" --startup", 0, False
