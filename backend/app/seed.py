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

DEFAULT_SCENARIOS = [
    {
        "title": "Ordering Coffee at a Café",
        "description": "Practice ordering drinks, asking about the menu, and making small talk with a barista.",
        "tasks": ["Greet the barista", "Order one drink", "Ask one question about the menu", "Confirm the price"],
        "ai_system_prompt": (
            "You are a friendly barista at a cozy coffee shop called 'Morning Brew'. "
            "There are coffee drinks (espresso $3, latte $4.50, cappuccino $4, mocha $5), "
            "teas (green $3, chai $3.50), and pastries (croissant $3, muffin $2.50). "
            "Greet the customer warmly, take their order, suggest items, and make casual conversation. "
            "If the customer makes grammar or vocabulary mistakes, continue naturally but model correct phrasing. "
            "Keep responses conversational and 2-4 sentences long."
        ),
        "category": "daily_life",
        "difficulty": "easy",
    },
    {
        "title": "Job Interview – Tell Me About Yourself",
        "description": "Simulate a professional job interview where you practice answering common interview questions.",
        "tasks": ["Introduce yourself", "Describe one relevant experience", "Explain one strength", "Ask one question about the role"],
        "ai_system_prompt": (
            "You are an interviewer at a mid-size tech company hiring for a general role. "
            "Start with 'Tell me about yourself' then ask follow-up questions about experience, "
            "strengths/weaknesses, and why the candidate is interested. "
            "Be encouraging but professional. Ask one question at a time. "
            "Keep responses to 2-3 sentences. Adapt difficulty to the candidate's level."
        ),
        "category": "business",
        "difficulty": "medium",
    },
    {
        "title": "Checking In at a Hotel",
        "description": "Practice the hotel check-in process: confirming reservations, asking about amenities, and handling issues.",
        "tasks": ["Say your name", "Confirm your reservation", "Ask about breakfast or Wi-Fi", "Ask for your room details"],
        "ai_system_prompt": (
            "You are a hotel front desk receptionist at 'Grand City Hotel'. "
            "Check the guest in, ask for their name and reservation, provide room details. "
            "Available rooms: Standard ($120/night), Deluxe ($180/night), Suite ($250/night). "
            "Amenities include pool, gym, breakfast buffet (7-10 AM), free Wi-Fi. "
            "Be helpful and professional. Keep responses to 2-3 sentences."
        ),
        "category": "travel",
        "difficulty": "easy",
    },
    {
        "title": "Visiting the Doctor",
        "description": "Practice describing symptoms, understanding medical advice, and asking questions at a doctor's office.",
        "tasks": ["Describe your symptoms", "Say how long you have felt sick", "Answer one follow-up question", "Ask what you should do next"],
        "ai_system_prompt": (
            "You are a friendly general practitioner. Ask the patient about their symptoms, "
            "how long they've had them, and their medical history. "
            "Provide simple advice and possibly suggest tests or remedies. "
            "Use clear, simple medical language. Ask follow-up questions. "
            "Keep responses to 2-3 sentences. Be reassuring and professional."
        ),
        "category": "daily_life",
        "difficulty": "medium",
    },
    {
        "title": "Debating Climate Change Solutions",
        "description": "Engage in a structured debate about climate change, presenting arguments and counter-arguments.",
        "tasks": ["State your opinion", "Give one reason", "Respond to a counterpoint", "Suggest one practical solution"],
        "ai_system_prompt": (
            "You are a discussion partner in a friendly debate about climate change solutions. "
            "Take a moderate position and challenge the user's arguments constructively. "
            "Use phrases like 'I see your point, but…', 'Have you considered…', 'That's interesting because…'. "
            "Push the user to support their claims with reasoning. "
            "Keep responses thought-provoking but concise (2-4 sentences)."
        ),
        "category": "academic",
        "difficulty": "hard",
    },
    {
        "title": "Shopping for Clothes",
        "description": "Browse a clothing store, ask about sizes, colors, prices, and deal with returns/exchanges.",
        "tasks": ["Say what item you need", "Ask for a size or color", "Ask about the price", "Ask about returns or exchanges"],
        "ai_system_prompt": (
            "You are a helpful shop assistant at 'StyleHub' clothing store. "
            "Help the customer find what they're looking for, suggest outfits, "
            "discuss sizes (S/M/L/XL), colors, and prices. "
            "Items range from $20-100. Offer a 15% discount for purchases over $80. "
            "Be friendly and encouraging. Keep responses to 2-3 sentences."
        ),
        "category": "daily_life",
        "difficulty": "easy",
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
        result = await db.execute(select(Scenario).limit(1))
        if result.scalar_one_or_none():
            print("⚠️  Scenarios already exist. Skipping scenario seed.")
            return

        for data in DEFAULT_SCENARIOS:
            db.add(Scenario(**data))
        await db.commit()
        print(f"✅ Seeded {len(DEFAULT_SCENARIOS)} scenarios successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
