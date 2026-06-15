from typing import List, Optional, Dict
from app.domain.value_objects import KeystrokeVector

class DeviceBiometricState:
    """
    Sub-entidade que guarda o estado biométrico de uma máquina específica.
    """
    def __init__(self, anchor: KeystrokeVector, history: Optional[List[KeystrokeVector]] = None):
        self.anchor = anchor
        self.history = history or []

    def can_evolve(self) -> bool:
        return len(self.history) >= 5

class User:
    """
    Entidade de Domínio principal com suporte a Multi-Hardware (Device-Bound Biometrics).
    """
    def __init__(
        self,
        email: str,
        password_hash: str,
        user_id: Optional[int] = None,
        device_biometrics: Optional[Dict[str, DeviceBiometricState]] = None,
        current_mfa_code: Optional[str] = None
    ):
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash
        # Dicionário: { "device_id_X": DeviceBiometricState(...) }
        self.device_biometrics = device_biometrics or {}
        self.current_mfa_code = current_mfa_code

    def is_device_trusted(self, device_id: str) -> bool:
        return device_id in self.device_biometrics

    def get_device_anchor(self, device_id: str) -> Optional[KeystrokeVector]:
        if self.is_device_trusted(device_id):
            return self.device_biometrics[device_id].anchor
        return None