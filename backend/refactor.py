import os
import shutil
from pathlib import Path

BASE_DIR = Path('/home/datnd/Projects/AI_Talk_Practice/backend/app')

def move(src_rel, tgt_rel):
    src = BASE_DIR / src_rel
    tgt = BASE_DIR / tgt_rel
    if src.exists():
        tgt.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(tgt))
        print(f"Moved {src_rel} -> {tgt_rel}")

# 1. Infra
move("services/llm", "infra/llm")
move("services/asr", "infra/asr")
move("services/tts", "infra/tts")
move("services/email.py", "infra/email.py")
move("services/factory.py", "infra/factory.py")

# 2. Auth
move("api/v1/auth.py", "modules/auth/router.py")
move("schemas/auth.py", "modules/auth/schemas.py")
move("services/auth_service.py", "modules/auth/service.py")

# 3. Users
move("models/user.py", "modules/users/models/user.py")
move("models/subscription.py", "modules/users/models/subscription.py")
move("schemas/user.py", "modules/users/schemas.py")
move("repositories/user_repository.py", "modules/users/repository.py")
move("services/user_service.py", "modules/users/service.py")
move("api/v1/users.py", "modules/users/router.py")
(BASE_DIR / "modules/users/models/__init__.py").touch()

# 4. Scenarios
move("models/scenario.py", "modules/scenarios/models.py")
move("schemas/scenario.py", "modules/scenarios/schemas/scenario.py")
move("schemas/admin_scenario.py", "modules/scenarios/schemas/admin_scenario.py")
(BASE_DIR / "modules/scenarios/schemas/__init__.py").touch()

move("repositories/scenario_repository.py", "modules/scenarios/repository.py")
move("services/scenario_service.py", "modules/scenarios/services/scenario_service.py")
move("services/admin_scenario_service.py", "modules/scenarios/services/admin_scenario_service.py")
move("services/variation_service.py", "modules/scenarios/services/variation_service.py")
(BASE_DIR / "modules/scenarios/services/__init__.py").touch()

move("api/v1/scenarios.py", "modules/scenarios/routers/user.py")
move("api/v1/admin_scenarios.py", "modules/scenarios/routers/admin.py")
(BASE_DIR / "modules/scenarios/routers/__init__.py").touch()

# 5. Sessions
session_models = ["session.py", "message.py", "correction.py", "message_score.py", "session_score.py", "phoneme_error.py", "word_error.py"]
for sm in session_models:
    move(f"models/{sm}", f"modules/sessions/models/{sm}")
(BASE_DIR / "modules/sessions/models/__init__.py").touch()

move("schemas/session.py", "modules/sessions/schemas.py")
move("repositories/session_repository.py", "modules/sessions/repository.py")

move("services/session_service.py", "modules/sessions/services/session.py")
move("services/conversation.py", "modules/sessions/services/conversation.py")
(BASE_DIR / "modules/sessions/services/__init__.py").touch()

move("api/v1/sessions.py", "modules/sessions/routers/rest.py")
move("api/v1/ws.py", "modules/sessions/routers/ws.py")
(BASE_DIR / "modules/sessions/routers/__init__.py").touch()

# 6. Gamification
for gm in ["daily_stat.py"]:
    move(f"models/{gm}", f"modules/gamification/models/{gm}")
(BASE_DIR / "modules/gamification/models/__init__.py").touch()

print("File movement completed.")
