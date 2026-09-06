"""
Backend startup and health verification test.
Tests: config loading, database init (SQLite), storage init, app assembly.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


async def test_backend_startup():
    print("\n" + "="*60)
    print("BACKEND STARTUP VERIFICATION")
    print("="*60)
    results = {}

    # 1. Config
    try:
        from backend.utils.config import settings
        assert settings.ENVIRONMENT in ("draft", "production", "development")
        assert len(settings.JWT_SECRET) >= 32
        assert settings.allowed_origins_list
        results["config"] = "PASS"
        print(f"  [PASS] Config loaded | env={settings.ENVIRONMENT} | origins={settings.allowed_origins_list[:1]}")
    except Exception as e:
        results["config"] = f"FAIL: {e}"
        print(f"  [FAIL] Config: {e}")

    # 2. Database (SQLite auto-init)
    try:
        from backend.database.connection import init_db, close_db, get_db, engine
        await init_db()
        from sqlalchemy import text
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1
        await close_db()
        results["database"] = "PASS"
        print(f"  [PASS] SQLite database initialised and SELECT 1 verified")
    except Exception as e:
        results["database"] = f"FAIL: {e}"
        print(f"  [FAIL] Database: {e}")

    # 3. Storage (local mode)
    try:
        from backend.storage.cos_client import verify_storage_connectivity
        status = await verify_storage_connectivity()
        assert status["status"] == "ok"
        results["storage"] = "PASS"
        print(f"  [PASS] Storage: {status}")
    except Exception as e:
        results["storage"] = f"FAIL: {e}"
        print(f"  [FAIL] Storage: {e}")

    # 4. App assembly
    try:
        from backend.main import app
        assert app is not None
        route_count = len([r for r in app.routes if hasattr(r, 'path')])
        results["app"] = "PASS"
        print(f"  [PASS] FastAPI app assembled | {len(app.routes)} total routes")
    except Exception as e:
        results["app"] = f"FAIL: {e}"
        print(f"  [FAIL] App assembly: {e}")

    # 5. Table creation check
    try:
        import pathlib
        db_path = pathlib.Path("./data/migrant_welfare.db")
        assert db_path.exists(), "SQLite DB file not found"
        import aiosqlite
        async with aiosqlite.connect(str(db_path)) as db:
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in await cursor.fetchall()]
        print(f"  [PASS] SQLite tables ({len(tables)}): {tables[:6]}{'...' if len(tables)>6 else ''}")
        results["tables"] = "PASS"
    except Exception as e:
        results["tables"] = f"FAIL: {e}"
        print(f"  [FAIL] Tables: {e}")

    # Summary
    print("\n" + "="*60)
    passed = sum(1 for v in results.values() if v == "PASS")
    total = len(results)
    print(f"RESULT: {passed}/{total} checks passed")
    for k, v in results.items():
        icon = "[PASS]" if v == "PASS" else "[FAIL]"
        print(f"  {icon} {k}: {v}")
    print("="*60)
    return passed == total


if __name__ == "__main__":
    ok = asyncio.run(test_backend_startup())
    sys.exit(0 if ok else 1)
