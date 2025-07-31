from passlib.context import CryptContext

from endpoints.helper.db_init import User, get_session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def gen_hashed_password(password: str) -> str:
    return pwd_context.hash(password)


def get_user(user_id: str) -> dict:
    session = next(get_session())
    user = session.query(User).filter(User.username == user_id).first()
    if user:
        return {
            "id": user.id,
            "username": user.username,
            "hashed_password": user.password
        }
    return None