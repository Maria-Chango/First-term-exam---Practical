from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from passlib.context import CryptContext
import uuid


app = FastAPI(
    titulo="API de Usuarios CRUD + Login",
    descripcion="Implementación de operaciones CRUD para usuarios con un endpoint de login.",
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_contraseña(plain_password, hashed_password):
    """Verifica si la contraseña plana coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)

def generar_contraseña_hash(password):
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password)

# --- Estructura ---

# Creación de usuario (recibe la contraseña en texto)
class Crearusuario(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6) # Nota: Se hashea antes de almacenar.
    email: Optional[EmailStr] = None
    is_active: bool = True

# Actualización de usuario (no permite cambiar la contraseña)
class Actualizarusuario(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

# Lectura/respuesta de usuario (NO expone el hash de la contraseña)
class UserInDB(BaseModel):
    id: uuid.UUID
    username: str
    password_hash: str # Almacena el hash en la "Base de datos"
    email: Optional[EmailStr] = None
    is_active: bool

# Simplificado para la respuesta pública (sin hash)
class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: Optional[EmailStr] = None
    is_active: bool

# Login
class LoginRequest(BaseModel):
    username: str
    password: str

# --- Base de Datos "Quemada"  ---

basededatos: List[UserInDB] = []

# Crear una cuenta de prueba débil para el ataque de fuerza bruta
TEST_USER = "tester_brute"
TEST_PASS_HASH = generar_contraseña_hash("123456") # Contraseña débil
basededatos.append(UserInDB(
    id=uuid.uuid4(),
    username=TEST_USER,
    password_hash=TEST_PASS_HASH,
    email="test@brute.com",
    is_active=True
))
print(f"Usuario de prueba: '{TEST_USER}' con password '123456'")

# --- Endpoints CRUD de Usuarios ---

@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: Crearusuario):
    
    # Verificar unicidad de username
    if any(u.username == user.username for u in db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username ya existe."
        )

    # Hashear la contraseña
    hashed_password = generar_contraseña_hash(user.password)

    # Crear el nuevo usuario
    new_user = UserInDB(
        id=uuid.uuid4(),
        username=user.username,
        password_hash=hashed_password,
        email=user.email,
        is_active=user.is_active
    )
    db.append(new_user)
    
    # Retornar el modelo de salida (sin el hash)
    return UserOut(**new_user.model_dump())

#GET

@app.get("/users", response_model=List[UserOut], tags=["Users"])
def list_users():
    """Lista todos los usuarios activos (sin exponer el hash)."""
    return [UserOut(**u.model_dump()) for u in db if u.is_active]

@app.get("/users/{user_id}", response_model=UserOut, tags=["Users"])
def get_user(user_id: uuid.UUID):
    """Obtiene un usuario por su ID."""
    for user in db:
        if user.id == user_id:
            return UserOut(**user.model_dump())
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuario no encontrado"
    )

#PUT

@app.put("/users/{user_id}", response_model=UserOut, tags=["Users"])
def update_user(user_id: uuid.UUID, user_update: Actualizarusuario):
    """Actualiza un usuario (excepto la contraseña)."""
    for i, user in enumerate(db):
        if user.id == user_id:
            # Actualizar solo los campos que no son None
            update_data = user_update.model_dump(exclude_unset=True)
            
            # Verificar unicidad del nuevo username
            if 'username' in update_data and update_data['username'] != user.username:
                if any(u.username == update_data['username'] for u in db if u.id != user_id):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Nuevo username ya existe."
                    )
            
            # Aplicar la actualización
            updated_user_data = user.model_dump()
            updated_user_data.update(update_data)
            db[i] = UserInDB(**updated_user_data)
            
            return UserOut(**db[i].model_dump())
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Usuario no encontrado"
    )

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
def delete_user(user_id: uuid.UUID):
    """Elimina un usuario (lo remueve de la lista)."""
    global db
    initial_len = len(db)
    db = [user for user in db if user.id != user_id]
    
    if len(db) == initial_len:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return

# --- Endpoint de Autenticación ---

@app.post("/login", tags=["Auth"])
def login_user(login_data: LoginRequest):
    """Autentica un usuario con username y password."""
    for user in db:
        if user.username == login_data.username:
            # En un entorno real, usaría `time-constant comparison` para mitigar timing attacks.
            if verificar_contraseña(login_data.password, user.password_hash):
                return {"message": "Login exitoso", "user_id": str(user.id)}
            else:
                # Simula un fallo de credenciales: **NO revelar qué falló (user o pass)**
                pass
    
    # Respuesta genérica para evitar enumeración de usuarios
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Login fallido: Credenciales inválidas"
    )