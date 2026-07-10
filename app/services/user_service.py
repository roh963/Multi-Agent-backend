from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User

class UserService:
    def get_by_id(self, db: Session, user_id: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def update_profile(self, db: Session, user: User, name: str = None, picture: str = None) -> User:
        if name is not None:
            user.name = name
        if picture is not None:
            user.picture = picture
        db.commit()
        db.refresh(user)
        return user

    def deactivate(self, db: Session, user: User) -> User:
        user.is_active = False
        db.commit()
        db.refresh(user)
        return user

user_service = UserService()