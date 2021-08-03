from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Union

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError


class PasswordBearerBase:
    SECRET_KEY: str = None
    ALGORITHM: Literal["HS256"] = None
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        to_encode = data.copy()
        expires_delta = timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt

    @classmethod
    def decode_token(cls, jwt_token: str) -> Dict[Any, Any]:
        payload = jwt.decode(jwt_token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
        return payload

    @classmethod
    def get_oauth2_schema(cls, token_url: str) -> OAuth2PasswordBearer:
        assert token_url
        assert cls.SECRET_KEY
        assert cls.ALGORITHM
        return OAuth2PasswordBearer(
            tokenUrl=token_url,
            scopes={
                "me": "Read information about the current user.",
                "items": "Read items.",
            },
        )

    @classmethod
    def verify_password(cls, plain_password, hashed_password):
        return cls.PWD_CONTEXT.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, password):
        return cls.PWD_CONTEXT.hash(password)


class PasswordBearer(PasswordBearerBase):
    # to get a string like this run:
    # openssl rand -hex 32
    # TOKEN_URL = "auth/token"
    PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30


PasswordHasher = CryptContext(schemes=["bcrypt"], deprecated="auto")


TOKEN_URL = "auth/token"

DUMMY_USER = "dummy"
DUMMY_PASS = "password"

fake_users_db = {
    "dummy": {
        "username": DUMMY_USER,
        "email": "dummy@example.com",
        "hashed_password": PasswordHasher.hash(DUMMY_PASS),
        # "hashed_password": "$2b$12$F.aimW3OCx4Dj9mvZxNOyOmWQpcP5bp6YzwY/lVpd9gadt0SHpmcW",  # password
    },
}


class UserDb:
    def get_user(self, username: Union[str, None]):
        global fake_users_db
        if username in fake_users_db:
            user_dict = fake_users_db[username]
            return user_dict.copy()

    def authenticate_user(self, username: str, password: str):
        user = self.get_user(username)
        if not user:
            return False
        # if not self.verify_password(password, user["hashed_password"]):
        if not PasswordHasher.verify(password, user["hashed_password"]):
            return False
        return user

    # @staticmethod
    # def verify_password(plain_password, hashed_password):
    #     return pwd_context.verify(plain_password, hashed_password)

    # @staticmethod
    # def get_password_hash(password):
    #     return pwd_context.hash(password)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []


class User(BaseModel):
    username: str
    email: Optional[str] = None


# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl="token",
#     scopes={"me": "Read information about the current user.", "items": "Read items."},
# )

router = APIRouter()

"""
token_urlが必要
の前にそのendopointの実装が必要
そのendpointはBarerが必要
user dbなどの依存もある

"""


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: UserDb = Depends()
):
    user = db.authenticate_user(
        username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = PasswordBearer.create_access_token(
        data={"sub": user["username"], "scopes": form_data.scopes},
    )
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(PasswordBearer.get_oauth2_schema(token_url=TOKEN_URL)),
    db: UserDb = Depends(),
) -> User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = PasswordBearer.decode_token(token)
        username: str = payload.get("sub")  # type: ignore
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    user = db.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return User(**user)


# async def get_current_active_user(
#     current_user: User = Security(get_current_user, scopes=["me"])
# ):
#     if current_user.disabled:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user


# @router.get("/me/", response_model=User)
# async def read_users_me(current_user: User = Depends(get_current_active_user)):
#     return current_user


# @app.get("/users/me/items/")
# async def read_own_items(
#     current_user: User = Security(get_current_active_user, scopes=["items"])
# ):
#     return [{"item_id": "Foo", "owner": current_user.username}]


# @app.get("/status/")
# async def read_system_status(current_user: User = Depends(get_current_user)):
#     return {"status": "ok"}


import secrets


def authenticate_basic_credential(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
):
    correct_username = secrets.compare_digest(credentials.username, DUMMY_USER)
    correct_password = secrets.compare_digest(credentials.password, DUMMY_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/basic")
def login_for_basic_auth(username: str = Depends(authenticate_basic_credential)):
    return {"username": username}
