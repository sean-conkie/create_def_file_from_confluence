@echo off
title def file from confluence setup

@REM check for python install
python --version
if %ERRORLEVEL% neq 0 goto PythonCheckError

@REM create a virtual environment in this dir
python -m venv .\def-file-venv

@REM launch venv
.\def-file-venv\Scripts\activate
if %ERRORLEVEL% neq 0 goto VenvError

@REM install python requirements
python -m pip install -r .\requirements.txt
if %ERRORLEVEL% neq 0 goto PipInstallError

exit /b 0

:PythonCheckError
echo You must install Python to continue.
pause
exit /b 1

:VenvError
echo Error setting up environment.
pause
exit /b 1

:PipInstallError
echo Error installing requirements.
pause
exit /b 1