import os

files_to_delete = [
    "/home/datnd/Projects/AI_Talk_Practice/backend/app/modules/auth/router.py",
    "/home/datnd/Projects/AI_Talk_Practice/backend/app/modules/auth/schemas.py",
    "/home/datnd/Projects/AI_Talk_Practice/backend/app/modules/auth/service.py",
    "/home/datnd/Projects/AI_Talk_Practice/backend/app/modules/users/router.py",
    "/home/datnd/Projects/AI_Talk_Practice/backend/app/modules/users/schemas.py",
    "/home/datnd/Projects/AI_Talk_Practice/backend/app/modules/users/service.py",
    "/home/datnd/Projects/AI_Talk_Practice/backend/app/modules/sessions/schemas.py",
    "/home/datnd/Projects/AI_Talk_Practice/backend/app/modules/scenarios/models.py",
]

for file_path in files_to_delete:
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Successfully deleted: {file_path}")
        else:
            print(f"File not found, skipping: {file_path}")
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")
