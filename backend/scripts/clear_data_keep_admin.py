"""
backend/scripts/clear_data_keep_admin.py

This script deletes all application data while preserving any existing admin user(s).
If no admin user remains after the wipe it will call seed_single_admin() to recreate
an admin from values set in backend/.env (settings.admin_login_id and settings.admin_password).

RUN THIS ONLY AFTER YOU BACKUP YOUR DATABASE.
Usage (from repository root):
  python backend/scripts/clear_data_keep_admin.py

Make sure your virtualenv is activated and the app's .env is configured if you expect
seed_single_admin() to recreate an admin.
"""

from sqlalchemy import MetaData, text
from app.db.session import engine
from app.db.bootstrap import seed_single_admin
from app.core.config import settings


def main():
    print("Starting destructive wipe: deleting all data except admin users.")
    print("DATABASE URL:", settings.database_url)

    meta = MetaData()
    meta.reflect(bind=engine)

    # Build list of all table names except users (we will keep users table rows but remove non-admins)
    all_tables = [t.name for t in meta.sorted_tables]
    tables_to_clear = [n for n in all_tables if n.lower() != "users"]

    if not tables_to_clear:
        print("No non-user tables found to clear.")

    with engine.begin() as conn:
        dialect = engine.dialect.name
        print("DB dialect detected:", dialect)

        if dialect == "postgresql":
            # Use a single TRUNCATE ... CASCADE statement for Postgres to handle FKs efficiently
            quoted = ", ".join([f'public."{t}"' for t in tables_to_clear]) if tables_to_clear else ''
            if quoted:
                sql = f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE;"
                print("Executing:", sql)
                conn.execute(text(sql))
        else:
            # For SQLite and other DBs, disable FK checks where supported and DELETE rows table-by-table
            if dialect == "sqlite":
                try:
                    conn.execute(text("PRAGMA foreign_keys = OFF;"))
                except Exception:
                    pass

            for t in tables_to_clear:
                print("Deleting rows from table:", t)
                try:
                    conn.execute(text(f'DELETE FROM "{t}";'))
                except Exception as exc:
                    print(f"Failed to delete from {t}: {exc}")

            if dialect == "sqlite":
                # Reset sqlite autoincrement sequences where present
                try:
                    for t in tables_to_clear:
                        conn.execute(text(f"DELETE FROM sqlite_sequence WHERE name='{t}';"))
                except Exception:
                    pass
                try:
                    conn.execute(text("PRAGMA foreign_keys = ON;"))
                except Exception:
                    pass

        # Remove non-admin users from users table (keep any row with role='admin')
        print("Deleting all non-admin users...")
        try:
            conn.execute(text("DELETE FROM users WHERE COALESCE(role, '') <> 'admin';"))
        except Exception as exc:
            print("Failed to delete non-admin users:", exc)

        # For Postgres, restart users sequence as well
        if dialect == "postgresql":
            try:
                conn.execute(text("ALTER SEQUENCE IF EXISTS users_id_seq RESTART WITH 1;"))
            except Exception:
                pass

        # Verify an admin exists; if not, seed one using settings.admin_* values
        admin_count = 0
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin';"))
            admin_count = int(result.scalar() or 0)
        except Exception:
            admin_count = 0

    if admin_count == 0:
        print("No admin user found after wipe. Attempting to seed admin from backend/.env...")
        seed_single_admin()
        # Re-check
        with engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin';"))
                admin_count = int(result.scalar() or 0)
            except Exception:
                admin_count = 0

    print("Wipe complete.")
    print(f"Admin users remaining: {admin_count}")
    if admin_count == 0:
        print("WARNING: No admin user exists. Set admin_login_id/admin_password in backend/.env and run seed_single_admin().")
    else:
        print("Admin preserved. You can now restart the application.")


if __name__ == '__main__':
    main()
