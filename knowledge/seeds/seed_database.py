"""
Knowledge base database seeder.
Seeds the SQLite (dev) or PostgreSQL (prod) database with initial verified knowledge records.
Run once after database initialization.
Usage: python -m knowledge.seeds.seed_database
"""
import asyncio
import sys
import os
import uuid
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


async def seed_knowledge():
    from backend.database import connection as db_module
    from backend.database.models import KnowledgeRecord, KnowledgeCategory, KnowledgeStatus
    from knowledge.seeds.initial_knowledge import KNOWLEDGE_SEEDS
    from sqlalchemy import select

    await db_module.init_db()

    async with db_module.AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(
            select(KnowledgeRecord).where(KnowledgeRecord.is_current == True).limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"Knowledge base already seeded. Skipping.")
            return

        count = 0
        for seed in KNOWLEDGE_SEEDS:
            try:
                category = KnowledgeCategory(seed["category"])
            except ValueError:
                print(f"  WARN: Unknown category '{seed['category']}' — skipping")
                continue

            record = KnowledgeRecord(
                id=uuid.uuid4(),
                version_number=seed["version_number"],
                category=category,
                title=seed["title"],
                content=seed["content"],
                content_en=seed.get("content_en") or seed["content"],
                content_hi=seed.get("content_hi"),
                content_gu=seed.get("content_gu"),
                source_name=seed["source_name"],
                source_url=seed.get("source_url"),
                source_type=seed["source_type"],
                source_active=True,
                status=KnowledgeStatus.LIVE,
                is_current=True,
                structured_data=seed.get("structured_data"),
                tags=seed.get("tags", []),
                confidence_level=0.9,
                valid_from=date.today(),
            )
            db.add(record)
            count += 1
            print(f"  Added: [{seed['category'].upper()}] {seed['title'][:60]}")

        await db.commit()
        print(f"\nSeeded {count} knowledge records successfully.")


if __name__ == "__main__":
    asyncio.run(seed_knowledge())
