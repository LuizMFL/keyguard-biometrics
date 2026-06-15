from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class UserRegisterDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    initial_vectors: List[List[float]] = Field(..., min_length=5, max_length=5)
    device_id: str

class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str
    current_vector: List[float]
    device_id: str

class MFAVerifyDTO(BaseModel):
    email: EmailStr
    mfa_code: str = Field(..., description="Código recebido via SMS/Email")
    rejected_vector: List[float] = Field(..., description="O vetor que foi rejeitado no login para ser aprendido após MFA")
    device_id: str

class PasswordUpdateDTO(BaseModel):
    email: EmailStr
    current_password: str
    current_vector: List[float]
    new_password: str = Field(..., min_length=8)
    new_initial_vectors: List[List[float]] = Field(..., min_length=5, max_length=5, description="5 digitações da nova senha")

class LoginResponseDTO(BaseModel):
    authenticated: bool
    require_mfa: bool
    message: str
    distance: Optional[float] = None