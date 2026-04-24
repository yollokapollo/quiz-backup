#!/bin/bash
cd /home/quiz
export QUIZ_DB_PASSWORD="bfw01"
exec python3 /home/quiz/quiz_cli.py
