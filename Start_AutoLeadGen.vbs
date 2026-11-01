' AutoLeadGen - Completely Silent Windows Launcher
' Launches Start_AutoLeadGen.bat without opening any command prompt window.

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get directory containing this VBS script
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strBatPath = strScriptDir & "\Start_AutoLeadGen.bat"

' Check that .bat exists
If Not objFSO.FileExists(strBatPath) Then
    MsgBox "ملف التشغيل Start_AutoLeadGen.bat غير موجود في: " & vbCrLf & strScriptDir, 16, "AutoLeadGen - خطأ"
    WScript.Quit 1
End If

' Run batch file completely hidden (0 = hidden window, False = don't wait for completion)
objShell.CurrentDirectory = strScriptDir
objShell.Run Chr(34) & strBatPath & Chr(34), 0, False
