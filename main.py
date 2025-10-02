from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from passlib.context import CryptContext
import uuid
import time

app = FastAPI(
    title="API de Usuarios CRUD + Login",
    description="Implementación de operaciones CRUD para usuarios con un endpoint de login (entorno de laboratorio)."
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_contraseña(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generar_contraseña_hash(password: str) -> str:
    return pwd_context.hash(password)

class CrearUsuario(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    is_active: bool = True

class ActualizarUsuario(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserInDB(BaseModel):
    id: uuid.UUID
    username: str
    password_hash: str
    email: Optional[EmailStr] = None
    is_active: bool

class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: Optional[EmailStr] = None
    is_active: bool

class LoginRequest(BaseModel):
    username: str
    password: str

# "DB" en memoria 
db: List[UserInDB] = []

# Contador simple de intentos (username -> {count, last_attempt_ts, locked_until})
attempts: Dict[str, Dict] = {}
MAX_ATTEMPTS = 11
LOCK_SECONDS = 60  # bloqueo temporal de 60s después de MAX_ATTEMPTS fallidos

# Usuario de prueba débil 
TEST_USER = "tester_brute"
TEST_PASS = "123456"
db.append(UserInDB(
    id=uuid.uuid4(),
    username=TEST_USER,
    password_hash=generar_contraseña_hash(TEST_PASS),
    email="test@brute.com",
    is_active=True
))

@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: CrearUsuario):
    if any(u.username == user.username for u in db):
        raise HTTPException(status_code=400, detail="Username ya existe.")
    hashed = generar_contraseña_hash(user.password)
    new_user = UserInDB(id=uuid.uuid4(), username=user.username, password_hash=hashed, email=user.email, is_active=user.is_active)
    db.append(new_user)
    # Excluir password_hash al devolver
    return UserOut(**new_user.model_dump(exclude={"password_hash"}))

@app.get("/users", response_model=List[UserOut], tags=["Users"])
def list_users():
    return [UserOut(**u.model_dump(exclude={"password_hash"})) for u in db if u.is_active]

@app.get("/users/{user_id}", response_model=UserOut, tags=["Users"])
def get_user(user_id: uuid.UUID):
    for u in db:
        if u.id == user_id:
            return UserOut(**u.model_dump(exclude={"password_hash"}))
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.put("/users/{user_id}", response_model=UserOut, tags=["Users"])
def update_user(user_id: uuid.UUID, user_update: ActualizarUsuario):
    for i, u in enumerate(db):
        if u.id == user_id:
            data = user_update.model_dump(exclude_unset=True)
            if "username" in data and data["username"] != u.username:
                if any(x.username == data["username"] for x in db if x.id != user_id):
                    raise HTTPException(status_code=400, detail="Nuevo username ya existe.")
            updated = u.model_dump()
            updated.update(data)
            db[i] = UserInDB(**updated)
            return UserOut(**db[i].model_dump(exclude={"password_hash"}))
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
def delete_user(user_id: uuid.UUID):
    global db
    new_db = [u for u in db if u.id != user_id]
    if len(new_db) == len(db):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db = new_db
    return

@app.post("/login", tags=["Auth"])
def login_user(login: LoginRequest):
    # bloqueo simple por username (memoria)
    info = attempts.get(login.username, {"count": 0, "last": 0, "locked_until": 0})
    now = time.time()
    if info.get("locked_until", 0) > now:
        raise HTTPException(status_code=429, detail="Cuenta temporalmente bloqueada por demasiados intentos. Intenta más tarde.")
    # buscar usuario
    for u in db:
        if u.username == login.username:
            if verificar_contraseña(login.password, u.password_hash):
                # reset attempts
                attempts[login.username] = {"count": 0, "last": now, "locked_until": 0}
                return {"message": "Login exitoso", "user_id": str(u.id)}
            else:
                # fallo: incrementar contador
                info["count"] = info.get("count", 0) + 1
                info["last"] = now
                if info["count"] >= MAX_ATTEMPTS:
                    info["locked_until"] = now + LOCK_SECONDS
                attempts[login.username] = info
                break
    # respuesta genérica
    raise HTTPException(status_code=401, detail="Login fallido: Credenciales inválidas")
