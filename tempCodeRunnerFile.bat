@echo off
call venv\Scripts\activate

flask --app wsgi.py run --debug
pause