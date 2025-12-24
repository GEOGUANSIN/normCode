' ============================================
' NormCode Website Dev Server - Silent GUI Launcher
' ============================================
' This VBS script launches the GUI launcher without showing a console window
' Double-click this file for the cleanest launch experience!

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strPythonScript = strScriptPath & "\launch_dev_gui.pyw"

' Check if the Python GUI launcher exists
If objFSO.FileExists(strPythonScript) Then
    ' Launch the Python GUI without showing a console window
    ' 0 = Hide window, False = Don't wait for it to finish
    objShell.Run "pythonw """ & strPythonScript & """", 0, False
Else
    ' Show error message if the GUI launcher is missing
    MsgBox "Error: launch_dev_gui.pyw not found!" & vbCrLf & vbCrLf & _
           "Please make sure the file exists in:" & vbCrLf & strScriptPath, _
           vbCritical, "NormCode Dev Launcher"
End If

