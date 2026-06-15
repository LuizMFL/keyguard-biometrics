import hashlib
import random
from typing import Optional, List
from dataclasses import dataclass
import numpy as np

from app.domain.interfaces import IUserRepository, IEmailService
from app.domain.entities import User, DeviceBiometricState
from app.domain.value_objects import KeystrokeVector
from app.infrastructure.ai_engine import BiometricAIService


@dataclass
class AuthResult:
    is_authenticated: bool
    require_mfa: bool
    message: str
    distance: Optional[float] = None


class AuthenticationUseCase:
    def __init__(self, repository: IUserRepository, ai_service: BiometricAIService, email_service: IEmailService):
        self.repository = repository
        self.ai_service = ai_service
        self.email_service = email_service

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _calculate_anchor(self, vectors: List[List[float]]) -> KeystrokeVector:
        min_len = min(len(v) for v in vectors)
        vetores_alinhados = [v[:min_len] for v in vectors]
        matriz_vetores = np.array(vetores_alinhados)
        vetor_medio = np.mean(matriz_vetores, axis=0).tolist()
        return KeystrokeVector(features=vetor_medio)

    def register(self, email: str, password: str, initial_vectors: List[List[float]], device_id: str) -> User:
        if self.repository.get_by_email(email):
            raise ValueError("Utilizador já cadastrado com este e-mail.")
        if len(initial_vectors) < 5:
            raise ValueError("São necessárias exatamente 5 digitações para o registo biométrico.")

        # Cria o estado biométrico para a máquina atual
        initial_anchor = self._calculate_anchor(initial_vectors)
        initial_device_state = {device_id: DeviceBiometricState(anchor=initial_anchor)}

        novo_usuario = User(
            email=email,
            password_hash=self._hash_password(password),
            device_biometrics=initial_device_state
        )
        user_salvo = self.repository.save(novo_usuario)
        self.email_service.send_welcome_email(user_salvo.email)
        return user_salvo

    def login(self, email: str, password_raw: str, current_vector: List[float], device_id: str) -> AuthResult:
        user = self.repository.get_by_email(email)
        if not user or user.password_hash != self._hash_password(password_raw):
            return AuthResult(False, False, "Credenciais inválidas.")

        is_trusted_device = user.is_device_trusted(device_id)

        # 1. BLOQUEIO DE HARDWARE (Máquina Nova)
        if not is_trusted_device:
            codigo_mfa = f"{random.randint(100000, 999999)}"

            # Grava no banco de dados
            user.current_mfa_code = codigo_mfa
            self.repository.update(user)

            self.email_service.send_mfa_code(user.email, codigo_mfa)
            print(
                f"====== SECURITY ALERT ======\nCódigo MFA (Novo Dispositivo) enviado para {user.email}: {codigo_mfa}\n============================")

            return AuthResult(
                is_authenticated=False,
                require_mfa=True,
                message="Máquina Desconhecida. Digite o código enviado para o seu e-mail."
            )

        # 2. BLOQUEIO BIOMÉTRICO (Máquina Conhecida, Ritmo Diferente)
        device_state = user.device_biometrics[device_id]
        vector_obj = KeystrokeVector(features=current_vector)

        ai_result = self.ai_service.verify_attempt(
            anchor_features=device_state.anchor.features,
            attempt_features=vector_obj.features
        )

        if not ai_result["is_authentic"]:
            codigo_mfa = f"{random.randint(100000, 999999)}"

            # Grava no banco de dados
            user.current_mfa_code = codigo_mfa
            self.repository.update(user)

            self.email_service.send_mfa_code(user.email, codigo_mfa)
            print(
                f"====== SECURITY ALERT ======\nCódigo MFA (Anomalia Biométrica) enviado para {user.email}: {codigo_mfa}\n============================")

            return AuthResult(
                is_authenticated=False,
                require_mfa=True,
                message="Anomalia Biométrica. Digite o código enviado para o seu e-mail.",
                distance=ai_result["distance"]
            )

        # 3. SUCESSO E EVOLUÇÃO (Tudo Perfeito)
        message = "Autenticado com sucesso."
        if ai_result["qualifies_for_evolution"]:
            device_state.history.append(vector_obj)
            if device_state.can_evolve():
                nova_ancora = self._calculate_anchor([h.features for h in device_state.history])
                device_state.anchor = nova_ancora
                device_state.history = []
                message = "Autenticado. A âncora DESTE hardware evoluiu com sucesso!"

        self.repository.update(user)
        return AuthResult(True, False, message, ai_result["distance"])

    def verify_mfa(self, email: str, mfa_code: str, rejected_vector: List[float], device_id: str) -> AuthResult:
        user = self.repository.get_by_email(email)

        # A Validação Real via Banco de Dados
        if not user or user.current_mfa_code != mfa_code:
            return AuthResult(False, False, "Código MFA inválido ou expirado.")

        # Limpa o código imediatamente para evitar ataques de reutilização
        user.current_mfa_code = None

        vector_obj = KeystrokeVector(features=rejected_vector)

        if not user.is_device_trusted(device_id):
            # Máquina Nova: Usa este primeiro vetor estranho como a âncora provisória do hardware novo
            user.device_biometrics[device_id] = DeviceBiometricState(anchor=vector_obj)
            message = "MFA validado. Novo hardware autorizado e registado!"
        else:
            # Máquina Conhecida, mas utilizador digitou esquisito (ex: com sono). Adiciona ao histórico do hardware atual.
            device_state = user.device_biometrics[device_id]
            device_state.history.append(vector_obj)
            if device_state.can_evolve():
                device_state.anchor = self._calculate_anchor([h.features for h in device_state.history])
                device_state.history = []
            message = "MFA validado. Padrão anómalo aprendido neste hardware!"

        self.repository.update(user)
        return AuthResult(True, False, message)

    def update_password(self, email: str, current_password_raw: str, current_vector: List[float], new_password_raw: str,
                        new_initial_vectors: List[List[float]], device_id: str) -> bool:
        auth_check = self.login(email, current_password_raw, current_vector, device_id)
        if not auth_check.is_authenticated:
            raise ValueError(f"Não autorizado. {auth_check.message}")

        if len(new_initial_vectors) < 5:
            raise ValueError("São necessárias 5 digitações da NOVA senha.")

        user = self.repository.get_by_email(email)
        user.password_hash = self._hash_password(new_password_raw)

        # ATENÇÃO ARQUITETÓNICA: Mudar a senha destrói as assinaturas de TODOS os teclados,
        # pois a geometria física das teclas mudou. O utilizador terá de validar a primeira
        # digitação via MFA nas outras máquinas.
        nova_ancora = self._calculate_anchor(new_initial_vectors)
        user.device_biometrics = {device_id: DeviceBiometricState(anchor=nova_ancora)}

        self.repository.update(user)
        return True
