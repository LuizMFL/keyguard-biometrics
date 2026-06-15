from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dtos import UserRegisterDTO, UserLoginDTO, PasswordUpdateDTO, MFAVerifyDTO, LoginResponseDTO, \
    ContinuousVerifyDTO
from app.infrastructure.database import SessionLocal
from app.infrastructure.email_service import SmtpEmailService
from app.infrastructure.repositories import SQLAlchemyUserRepository
from app.infrastructure.ai_engine import BiometricAIService
from app.application.auth_usecases import AuthenticationUseCase

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_usecase(db: Session = Depends(get_db)):
    repository = SQLAlchemyUserRepository(db)

    # 1. Descobre o caminho absoluto da pasta 'app/api' onde este ficheiro está
    current_dir = Path(__file__).resolve().parent

    # 2. Sobe duas pastas (para sair de api/ e depois de app/) e entra em data/
    model_path = current_dir.parent.parent / "data" / "keyguard_siamese_weights.pth"

    # 3. Injeta o caminho absoluto e seguro no serviço de IA
    ai_service = BiometricAIService(model_path=str(model_path))

    email_service = SmtpEmailService()

    return AuthenticationUseCase(repository, ai_service, email_service)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: UserRegisterDTO, usecase: AuthenticationUseCase = Depends(get_auth_usecase)):
    try:
        user = usecase.register(data.email, data.password, data.initial_vectors, data.device_id)
        return {"status": "success", "message": f"Utilizador {user.email} registado."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponseDTO)
def login(data: UserLoginDTO, usecase: AuthenticationUseCase = Depends(get_auth_usecase)):
    result = usecase.login(data.email, data.password, data.current_vector, data.device_id)

    # Se falhou e NÃO pede MFA, devolve 401 puro (Senha Errada ou Fraude Absoluta s/ MFA)
    if not result.is_authenticated and not result.require_mfa:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.message)

    # Se falhou mas PEDE MFA (Senha correta, Biometria estranha), devolve 202 Accepted/403 com a flag
    return LoginResponseDTO(
        authenticated=result.is_authenticated,
        require_mfa=result.require_mfa,
        message=result.message,
        distance=result.distance
    )


@router.post("/mfa-verify", response_model=LoginResponseDTO)
def mfa_verify(data: MFAVerifyDTO, usecase: AuthenticationUseCase = Depends(get_auth_usecase)):
    result = usecase.verify_mfa(data.email, data.mfa_code, data.rejected_vector, data.device_id)
    if not result.is_authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.message)
    return LoginResponseDTO(
        authenticated=result.is_authenticated,
        require_mfa=False,
        message=result.message
    )


@router.put("/update-password")
def update_password(data: PasswordUpdateDTO, usecase: AuthenticationUseCase = Depends(get_auth_usecase)):
    try:
        usecase.update_password(
            data.email, data.current_password, data.current_vector,
            data.new_password, data.new_initial_vectors, data.device_id
        )
        return {"status": "success", "message": "Senha modificada e âncora recalibrada com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/continuous-verify")
def continuous_verify(data: ContinuousVerifyDTO, usecase: AuthenticationUseCase = Depends(get_auth_usecase)):
    # Buscamos o utilizador
    user = usecase.repository.get_by_email(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Sessão inválida.")

    # Puxamos a âncora do dispositivo atual
    if data.device_id not in user.device_biometrics:
        raise HTTPException(status_code=401, detail="Hardware não autorizado.")

    device_state = user.device_biometrics[data.device_id]

    # Injetamos o vetor de texto livre direto no nosso motor PyTorch
    ai_result = usecase.ai_service.verify_attempt(
        anchor_features=device_state.anchor.features,
        attempt_features=data.current_vector
    )

    return {
        "authenticated": ai_result["is_authentic"],
        "distance": ai_result["distance"]
    }