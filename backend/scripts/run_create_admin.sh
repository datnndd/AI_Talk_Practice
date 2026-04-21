#!/bin/bash
cd /home/datnd/Projects/AI_Talk_Practice/backend
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.
python scripts/create_admin.py
