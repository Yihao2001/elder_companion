import bcrypt
import argparse
from elder_companion_flask.db import get_db
from elder_companion_flask.models import User, RoleEnum

def create_super_admin(username: str, password: str):
    """
    Function to create a new super admin account
    """
    db = next(get_db())
    existing = db.query(User).filter_by(username=username).first()
    if existing:
        print(f"Super admin '{username}' already exists")
        db.close()
        return existing

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    admin = User(username=username, password_hash=hashed_password, role=RoleEnum.super_admin)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    print(f"Super admin '{username}' created successfully!")
    return admin

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create super admin user")
    parser.add_argument("--username", required=True, help="Super admin username")
    parser.add_argument("--password", required=True, help="Super admin password")
    args = parser.parse_args()

    create_super_admin(args.username, args.password)

# username = super_admin
# password = 1234567890