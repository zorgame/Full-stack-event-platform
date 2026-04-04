from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validar_password_robusta(password: str) -> str:
    value = str(password or "")
    if len(value) < 20:
        raise ValueError("La contraseña debe tener al menos 20 caracteres")
    if not any(char.islower() for char in value):
        raise ValueError("La contraseña debe incluir al menos una letra minúscula")
    if not any(char.isupper() for char in value):
        raise ValueError("La contraseña debe incluir al menos una letra mayúscula")
    if not any(char.isdigit() for char in value):
        raise ValueError("La contraseña debe incluir al menos un número")
    if not any(not char.isalnum() for char in value):
        raise ValueError("La contraseña debe incluir al menos un símbolo")
    return value


class UsuarioBase(BaseModel):
    email: EmailStr
    telefono: str | None = Field(default=None, max_length=30)
    nombre: str | None = Field(default=None, max_length=120)
    apellido: str | None = Field(default=None, max_length=120)
    pais: str | None = Field(default=None, max_length=100)


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=20, max_length=128)
    is_admin: bool = False

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validar_password_robusta(value)


class UsuarioUpdate(BaseModel):
    telefono: str | None = Field(default=None, max_length=30)
    nombre: str | None = Field(default=None, max_length=120)
    apellido: str | None = Field(default=None, max_length=120)
    pais: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    is_admin: bool | None = None
    password: str | None = Field(default=None, min_length=20, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validar_password_robusta(value)


class UsuarioResponse(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    tickets: list["UsuarioTicketResponse"] = Field(default_factory=list)


class UsuarioListResponse(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime


class UsuarioPublic(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UsuarioTicketBase(BaseModel):
    categoria_id: int
    cantidad: int = Field(..., ge=1)
    nota: str | None = Field(default=None, max_length=255)


class UsuarioTicketCreate(UsuarioTicketBase):
    pass


class UsuarioTicketUpdate(BaseModel):
    cantidad: int | None = Field(default=None, ge=1)
    nota: str | None = Field(default=None, max_length=255)


class UsuarioTicketTransferRequest(BaseModel):
    usuario_ticket_id: int = Field(..., ge=1)
    destinatario_email: EmailStr
    cantidad: int = Field(..., ge=1)
    password: str = Field(..., min_length=20, max_length=128)
    confirmacion_expresa: bool = Field(...)
    nota: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validar_password_robusta(value)


class UsuarioTicketTransferResponse(BaseModel):
    transferencia_id: str
    usuario_origen_id: int
    usuario_destino_id: int
    usuario_ticket_origen_id: int
    usuario_ticket_destino_id: int
    categoria_id: int
    cantidad_transferida: int
    destinatario_email: EmailStr
    estado: str
    fecha: datetime
    nota: str | None = None


class UsuarioTicketCategoriaInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    nombre: str
    precio: float
    moneda: str


class UsuarioTicketResponse(UsuarioTicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    created_at: datetime
    updated_at: datetime
    categoria: UsuarioTicketCategoriaInfo


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str | None = None
    exp: int | None = None


UsuarioResponse.model_rebuild()
