from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

import app.db.models  # noqa: F401
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.gamification.models.daily_stat import DailyStat
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

WEEKLY_XP = [
    2460,
    2290,
    2135,
    1980,
    1845,
    1710,
    1595,
    1460,
    1325,
    1190,
    1065,
    940,
    825,
    710,
    595,
    480,
    365,
    250,
    135,
    60,
]

def cefr_from_level(level: str) -> str:
    return level.upper()

async def seed_fake_users() -> None:
    password_hash = hash_password(PASSWORD)
    created = 0
    updated = 0

    async with AsyncSessionLocal() as db:
        today = datetime.now(timezone.utc).date()
        week_start = today - timedelta(days=today.weekday())
        elapsed_days = (today - week_start).days + 1

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

            weekly_xp = WEEKLY_XP[index - 1]
            for day_offset in range(7):
                target_date = week_start + timedelta(days=day_offset)
                if target_date > today:
                    continue
                xp_for_day = weekly_xp // elapsed_days + (1 if day_offset < weekly_xp % elapsed_days else 0)
                lessons_for_day = max(1, xp_for_day // 120) if xp_for_day > 0 else 0
                daily_stat = (
                    await db.execute(
                        select(DailyStat).where(DailyStat.user_id == user.id, DailyStat.date == target_date)
                    )
                ).scalar_one_or_none()
                if daily_stat is None:
                    db.add(
                        DailyStat(
                            user_id=user.id,
                            date=target_date,
                            xp_earned=xp_for_day,
                            lessons_completed=lessons_for_day,
                        )
                    )
                else:
                    daily_stat.xp_earned = xp_for_day
                    daily_stat.lessons_completed = lessons_for_day

        await db.commit()

    print(f"Seeded fake users and weekly XP. created={created}, updated={updated}, password={PASSWORD}")

if __name__ == "__main__":
    asyncio.run(seed_fake_users())
