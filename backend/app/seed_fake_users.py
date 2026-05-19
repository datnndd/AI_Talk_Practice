from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

import app.db.models  # noqa: F401
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User

PASSWORD = "Test123@"

FAKE_USERS = [
    ("minh.nguyen", "Nguyễn Minh", "A1", 120),
    ("lan.tran", "Trần Lan", "A2", 450),
    ("huy.pham", "Phạm Huy", "B1", 880),
    ("mai.le", "Lê Mai", "B2", 1350),
    ("khoa.vo", "Võ Khoa", "C1", 2210),
    ("anh.do", "Đỗ Anh", "A1", 75),
    ("thao.bui", "Bùi Thảo", "A2", 610),
    ("nam.hoang", "Hoàng Nam", "B1", 940),
    ("linh.dang", "Đặng Linh", "B2", 1680),
    ("quang.phan", "Phan Quang", "C1", 2520),
    ("nhi.ngo", "Ngô Nhi", "A1", 210),
    ("tuan.dinh", "Đinh Tuấn", "A2", 530),
    ("vy.truong", "Trương Vy", "B1", 1020),
    ("son.ly", "Lý Sơn", "B2", 1890),
    ("ha.vu", "Vũ Hà", "C1", 2780),
    ("bao.huynh", "Huỳnh Bảo", "A1", 160),
    ("yen.cao", "Cao Yến", "A2", 700),
    ("dat.ta", "Tạ Đạt", "B1", 1130),
    ("hanh.lam", "Lâm Hạnh", "B2", 1970),
    ("phuc.ma", "Mã Phúc", "C1", 3100),
]

def cefr_from_level(level: str) -> str:
    return level.upper()

async def seed_fake_users() -> None:
    password_hash = hash_password(PASSWORD)
    created = 0
    updated = 0

    async with AsyncSessionLocal() as db:
        for index, (handle, display_name, level, total_xp) in enumerate(FAKE_USERS, start=1):
            email = f"{handle}@example.test"
            user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if user is None:
                user = User(
                    email=email,
                    password_hash=password_hash,
                    auth_provider="local",
                    role="user",
                    is_email_verified=True,
                    display_name=display_name,
                    age=18 + (index % 18),
                    level=level,
                    current_cefr=cefr_from_level(level),
                    total_xp=total_xp,
                    coin_balance=50 + index * 7,
                    favorite_topics=["travel", "work", "daily life"][0:1 + (index % 3)],
                    learning_purpose=["communication", "career"],
                    main_challenge="Speaking confidence",
                    is_onboarding_completed=True,
                    preferences={"handle": handle},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(user)
                await db.flush()
                db.add(Subscription(user_id=user.id, tier="FREE", status="active", features={}))
                created += 1
            else:
                user.password_hash = password_hash
                user.role = "user"
                user.level = level
                user.current_cefr = cefr_from_level(level)
                user.total_xp = total_xp
                user.is_email_verified = True
                user.is_onboarding_completed = True
                user.updated_at = datetime.now(timezone.utc)
                updated += 1

        await db.commit()

    print(f"Seeded fake users. created={created}, updated={updated}, password={PASSWORD}")

if __name__ == "__main__":
    asyncio.run(seed_fake_users())
