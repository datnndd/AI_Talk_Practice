"""
Seed the database with default scenarios and an admin user.
Run: python -m app.seed
"""

import asyncio

from sqlalchemy import select
from app.db.session import engine, AsyncSessionLocal
from app.db.base_class import Base
from app.modules.scenarios.models.scenario import Scenario
from app.modules.users.models.user import User

SCENARIO_LOGO_URL = "https://rgpmptospjqospitmcqw.supabase.co/storage/v1/object/public/images/site/logos/d1154b7d833048a2b6b3d9f43d1eb6b7.png"

DEFAULT_SCENARIOS = [
    {
        "title": "Ordering Coffee at a Café",
        "description": "Practice ordering drinks, asking about the menu, and making small talk with a barista.",
        "tasks": ["Greet the barista", "Order one drink", "Ask one question about the menu", "Confirm the price"],
        "category": "daily_life",
        "difficulty": "easy",
    },
    {
        "title": "Job Interview – Tell Me About Yourself",
        "description": "Simulate a professional job interview where you practice answering common interview questions.",
        "tasks": ["Introduce yourself", "Describe one relevant experience", "Explain one strength", "Ask one question about the role"],
        "category": "business",
        "difficulty": "medium",
    },
    {
        "title": "Checking In at a Hotel",
        "description": "Practice the hotel check-in process: confirming reservations, asking about amenities, and handling issues.",
        "tasks": ["Say your name", "Confirm your reservation", "Ask about breakfast or Wi-Fi", "Ask for your room details"],
        "category": "travel",
        "difficulty": "easy",
    },
    {
        "title": "Visiting the Doctor",
        "description": "Practice describing symptoms, understanding medical advice, and asking questions at a doctor's office.",
        "tasks": ["Describe your symptoms", "Say how long you have felt sick", "Answer one follow-up question", "Ask what you should do next"],
        "category": "daily_life",
        "difficulty": "medium",
    },
    {
        "title": "Debating Climate Change Solutions",
        "description": "Engage in a structured debate about climate change, presenting arguments and counter-arguments.",
        "tasks": ["State your opinion", "Give one reason", "Respond to a counterpoint", "Suggest one practical solution"],
        "category": "academic",
        "difficulty": "hard",
    },
    {
        "title": "Shopping for Clothes",
        "description": "Browse a clothing store, ask about sizes, colors, prices, and deal with returns/exchanges.",
        "tasks": ["Say what item you need", "Ask for a size or color", "Ask about the price", "Ask about returns or exchanges"],
        "category": "daily_life",
        "difficulty": "easy",
    },
    {
        "title": "VIP: Returning a Wrong Online Order",
        "description": "Practice contacting customer support after receiving the wrong product and requesting a clear solution.",
        "image_url": SCENARIO_LOGO_URL,
        "ai_role": "Online store customer support agent",
        "user_role": "Customer who received the wrong item",
        "tasks": [
            "Explain what you ordered and what you received",
            "Give your order number",
            "Ask for a replacement or refund",
            "Confirm the next step and timeline",
        ],
        "category": "daily_life",
        "difficulty": "easy",
        "tags": ["vip", "customer_support", "online_shopping", "problem_solving"],
        "is_pro": True,
    },
    {
        "title": "VIP: Negotiating a Project Deadline",
        "description": "Practice a workplace conversation where you explain a delay, negotiate a realistic deadline, and keep trust with your manager.",
        "image_url": SCENARIO_LOGO_URL,
        "ai_role": "Project manager",
        "user_role": "Team member responsible for a delayed task",
        "tasks": [
            "Explain why the task is delayed",
            "Describe what has already been completed",
            "Suggest a new deadline",
            "Offer one way to reduce risk",
        ],
        "category": "business",
        "difficulty": "medium",
        "tags": ["vip", "workplace", "deadline", "negotiation"],
        "is_pro": True,
    },
    {
        "title": "VIP: Apartment Viewing with a Landlord",
        "description": "Practice viewing an apartment, asking practical questions, and deciding whether the place fits your needs.",
        "image_url": SCENARIO_LOGO_URL,
        "ai_role": "Landlord showing an apartment",
        "user_role": "Potential tenant",
        "tasks": [
            "Describe what kind of apartment you need",
            "Ask about rent and deposit",
            "Ask about utilities or building rules",
            "Request time to decide or schedule next steps",
        ],
        "category": "daily_life",
        "difficulty": "medium",
        "tags": ["vip", "housing", "renting", "questions"],
        "is_pro": True,
    },
    {
        "title": "VIP: Airport Baggage Problem",
        "description": "Practice reporting a missing or damaged bag at an airport service counter and asking for support.",
        "image_url": SCENARIO_LOGO_URL,
        "ai_role": "Airline baggage service agent",
        "user_role": "Passenger with a baggage problem",
        "tasks": [
            "Describe your baggage problem",
            "Provide your flight and baggage details",
            "Ask what the airline can do now",
            "Confirm how you will receive updates",
        ],
        "category": "travel",
        "difficulty": "medium",
        "tags": ["vip", "airport", "baggage", "travel_problem"],
        "is_pro": True,
    },
    {
        "title": "VIP: Handling a Client Complaint",
        "description": "Practice responding professionally to an unhappy client, clarifying the issue, and proposing a recovery plan.",
        "image_url": SCENARIO_LOGO_URL,
        "ai_role": "Upset business client",
        "user_role": "Account manager",
        "tasks": [
            "Acknowledge the client's concern",
            "Ask clarifying questions about the issue",
            "Explain what you can investigate or fix",
            "Propose a follow-up plan with a deadline",
        ],
        "category": "business",
        "difficulty": "hard",
        "tags": ["vip", "client_management", "complaint", "professional"],
        "is_pro": True,
    },
    {
        "title": "VIP: Academic Panel Discussion",
        "description": "Practice joining an academic panel where you present a viewpoint, respond to disagreement, and support your ideas with examples.",
        "image_url": SCENARIO_LOGO_URL,
        "ai_role": "Panel moderator",
        "user_role": "Panel speaker",
        "tasks": [
            "State your main viewpoint clearly",
            "Support it with one concrete example",
            "Respond politely to a challenging question",
            "Summarize your final position",
        ],
        "category": "academic",
        "difficulty": "hard",
        "tags": ["vip", "academic", "discussion", "critical_thinking"],
        "is_pro": True,
    },
]
ADMIN_USER = {
    "email": "admin@aitalk.dev",
    "password": "Admin@12345",
    "display_name": "Admin",
    "role": "admin",
    "preferences": {"role": "admin"},
    "is_onboarding_completed": True,
}


async def seed():
    # Import all models to register them
    import app.db.models  # noqa: F401
    from app.core.security import hash_password

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # ── Seed admin user ───────────────────────────────────────────────
        admin_result = await db.execute(select(User).where(User.email == ADMIN_USER["email"]))
        existing_admin = admin_result.scalar_one_or_none()
        if existing_admin is None:
            admin = User(
                email=ADMIN_USER["email"],
                password_hash=hash_password(ADMIN_USER["password"]),
                display_name=ADMIN_USER["display_name"],
                role=ADMIN_USER["role"],
                preferences=ADMIN_USER["preferences"],
                is_onboarding_completed=ADMIN_USER["is_onboarding_completed"],
            )
            db.add(admin)
            await db.commit()
            print(f"✅ Seeded admin user: {ADMIN_USER['email']} / {ADMIN_USER['password']}")
        else:
            # Ensure existing admin has admin role in preferences
            prefs = existing_admin.preferences or {}
            if existing_admin.role != "admin" or prefs.get("role") != "admin":
                existing_admin.role = "admin"
                prefs["role"] = "admin"
                existing_admin.preferences = prefs
                await db.commit()
                print(f"✅ Upgraded {ADMIN_USER['email']} to admin role.")
            else:
                print(f"⚠️  Admin user already exists: {ADMIN_USER['email']}")

        # ── Seed scenarios ────────────────────────────────────────────────
        result = await db.execute(select(Scenario.title))
        existing_titles = set(result.scalars().all())
        created_count = 0
        for data in DEFAULT_SCENARIOS:
            if data["title"] in existing_titles:
                continue
            db.add(Scenario(**data))
            created_count += 1
        await db.commit()
        if created_count:
            print(f"✅ Seeded {created_count} scenarios successfully!")
        else:
            print("⚠️  All default scenarios already exist. Skipping scenario seed.")


if __name__ == "__main__":
    asyncio.run(seed())


