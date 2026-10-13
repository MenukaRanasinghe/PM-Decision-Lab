"""Create tables (if missing), apply in-place additive migrations, and seed the activity
catalogue. Safe to call on every startup — it never drops or overwrites existing data."""
from database.connection import engine, session_scope
from database.models import Base, Activity
from database.migrations import run_migrations
from content.registry import activity_catalog


def init_db():
    Base.metadata.create_all(engine)       # create any missing tables (new tracking tables, etc.)
    run_migrations(engine)                  # add new columns to a pre-existing DB, in place
    seed_activities()


def seed_activities():
    rows = activity_catalog()
    with session_scope() as s:
        for r in rows:
            existing = (
                s.query(Activity)
                .filter(Activity.code == r["code"], Activity.track == r["track"])
                .one_or_none()
            )
            if existing is None:
                a = Activity(**r)
                a.activity_type = "NATIVE"
                a.status = "PUBLISHED" if r.get("available") else "DRAFT"
                a.managed = False
                s.add(a)
            else:
                # refresh display fields; don't clobber admin-managed kind/available/status
                existing.title = r["title"]
                existing.description = r["description"]
                existing.est_minutes = r["est_minutes"]
                if not existing.activity_type:
                    existing.activity_type = existing.kind or "NATIVE"


if __name__ == "__main__":
    report = init_db()
    print("Database initialised, migrated and activities seeded.")
