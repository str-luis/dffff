from contextlib import asynccontextmanager
from hashlib import sha256

from fastapi import Depends, FastAPI, HTTPException, status
from sqlmodel import Field, Session, SQLModel, create_engine, select


DATABASE_URL = "sqlite:///./login_app.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    full_name: str


class LoginRequest(SQLModel):
    username: str
    password: str


class LoginResponse(SQLModel):
    success: bool
    message: str
    username: str | None = None
    full_name: str | None = None


class HealthResponse(SQLModel):
    status: str


def hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()



def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)



def seed_example_user() -> None:
    with Session(engine) as session:
        statement = select(User).where(User.username == "admin")
        user = session.exec(statement).first()

        if user is None:
            example_user = User(
                username="admin",
                password_hash=hash_password("admin123"),
                full_name="Usuario de Prueba",
            )
            session.add(example_user)
            session.commit()



def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_example_user()
    yield


app = FastAPI(
    title="API sencilla de Login con FastAPI",
    description="API mínima para validar usuario y contraseña con FastAPI + SQLModel.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_model=HealthResponse)
def read_root() -> HealthResponse:
    return HealthResponse(status="API de login activa")


@app.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)) -> LoginResponse:
    statement = select(User).where(User.username == data.username)
    user = session.exec(statement).first()

    if user is None or user.password_hash != hash_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )

    return LoginResponse(
        success=True,
        message="Login correcto",
        username=user.username,
        full_name=user.full_name,
    )