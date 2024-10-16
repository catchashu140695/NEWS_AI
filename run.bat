@echo off
REM Change to the directory where your virtual environment and Python script are located
cd D:\Python Scripts\NEWS_AI

REM Activate the virtual environment
call NEWSAI\Scripts\activate

REM Run your Python script
python app.py

REM Deactivate the virtual environment
deactivate

REM Pause to keep the command prompt open if you want to see any output
pause
