' AirFlick Drop - Silent Background Server Launcher
' Runs the core AirFlick file-receiving server in the background with zero CMD window
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir
WshShell.Run "pythonw.exe """ & currentDir & "\server.py""", 0, False
