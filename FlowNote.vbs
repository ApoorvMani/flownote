' FlowNote silent launcher (no terminal window)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\") - 1)

' Detect python in venv first, then system python
Dim python
If FileExists(WshShell.CurrentDirectory & "\.venv\Scripts\pythonw.exe") Then
    python = """" & WshShell.CurrentDirectory & "\.venv\Scripts\pythonw.exe"""
ElseIf FileExists(WshShell.CurrentDirectory & "\venv\Scripts\pythonw.exe") Then
    python = """" & WshShell.CurrentDirectory & "\venv\Scripts\pythonw.exe"""
Else
    python = "pythonw"
End If

WshShell.Run python & " """ & WshShell.CurrentDirectory & "\run.py""", 0, False

Function FileExists(path)
    Dim fso
    Set fso = CreateObject("Scripting.FileSystemObject")
    FileExists = fso.FileExists(path)
End Function
