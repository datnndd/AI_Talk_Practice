import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, is_sqlite
from app.models.scenario import Scenario, ScenarioVariation
from app.models.user import User

# Handle SQLite JSONB monkeypatch if necessary
if is_sqlite:
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.types import JSON
    postgresql.JSONB = JSON

async def seed_scenarios():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Scenario).limit(1))
        if result.scalar_one_or_none():
            print("Database already contains scenarios. Skipping seed.")
            return

        print("Seeding initial scenarios...")

        scenarios = [
            Scenario(
                title="Ordering Coffee at a Café",
                description="Practice basic interactions in a coffee shop setting. Learn how to order, customize your drink, and pay.",
                category="Daily Life",
                difficulty="easy",
                mode="roleplay",
                target_skills=["speaking", "vocabulary"],
                tags=["cafe", "ordering", "beginner"],
                ai_system_prompt=(
                    "You are a friendly barista at 'The Daily Brew'. Your name is Sam. "
                    "Greet the customer warmly and take their order. Ask clarifying questions "
                    "(e.g., 'What size?', 'Any milk or sugar?'). Suggest a blueberry muffin "
                    "if they only order a drink. Keep your responses short (1-2 sentences)."
                ),
                learning_objectives=["Ordering a specific drink", "Customizing options", "Handling a transaction"],
                estimated_duration=300
            ),
            Scenario(
                title="Job Interview: Marketing Specialist",
                description="A formal job interview for a mid-level marketing position. Practice talking about your experience and skills.",
                category="Business",
                difficulty="hard",
                mode="interview",
                target_skills=["fluency", "grammar", "formal"],
                tags=["career", "interview", "formal"],
                ai_system_prompt=(
                    "You are Mr. Henderson, the Hiring Manager at a tech startup called 'Vortex Solutions'. "
                    "You are interviewing the candidate for a Marketing Specialist role. "
                    "Ask challenging but fair questions about their experience with social media campaigns, "
                    "data analytics, and working in a team. Be professional and maintain a formal tone."
                ),
                learning_objectives=["Self-introduction", "Describing past achievements", "Answering behavioral questions"],
                estimated_duration=900
            ),
            Scenario(
                title="Hotel Check-in",
                description="Arriving at a hotel after a long flight. Confirm your reservation and ask about amenities.",
                category="Travel",
                difficulty="medium",
                mode="roleplay",
                target_skills=["speaking", "listening"],
                tags=["travel", "hotel", "check-in"],
                ai_system_prompt=(
                    "You are a receptionist at the 'Grand Plaza Hotel'. "
                    "A guest is checking in. Greet them, ask for their name and ID. "
                    "Confirm their stay details (3 nights, king room). Mention that "
                    "breakfast is served from 7 AM to 10 AM in the main hall."
                ),
                learning_objectives=["Providing personal details", "Clarifying room information", "Asking about services"],
                estimated_duration=450
            ),
            Scenario(
                title="At the Doctor: Flu Symptoms",
                description="Visit a clinic because you have been feeling unwell. Describe your symptoms to the doctor.",
                category="Health",
                difficulty="medium",
                mode="conversation",
                target_skills=["vocabulary", "polite"],
                tags=["medical", "health", "symptoms"],
                ai_system_prompt=(
                    "You are Dr. Elena, a general practitioner. A patient comes in feeling sick. "
                    "Ask about their symptoms (fever, sore throat, cough), when they started, "
                    "and if they have any allergies. Be empathetic but professional and thorough."
                ),
                learning_objectives=["Describing physical symptoms", "Answering medical history questions", "Understanding advice"],
                estimated_duration=600
            )
        ]

        db.add_all(scenarios)
        await db.commit()
        
        # Add a variation for the first one
        coffee_scenario = scenarios[0]
        variation = ScenarioVariation(
            scenario_id=coffee_scenario.id,
            variation_seed="café-rush-hour",
            parameters={"env": "busy", "proficiency": "B1", "formality": "casual"},
            sample_prompt="The café is really busy during rush hour. You need to order quickly and find a seat.",
            system_prompt_override=(
                coffee_scenario.ai_system_prompt + " The café is very loud and busy. You are slightly rushed but still professional."
            ),
            is_pregenerated=True,
            is_approved=True
        )
        db.add(variation)
        await db.commit()

        print("Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_scenarios())
