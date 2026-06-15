from pydantic import BaseModel, Field
from typing import List

class KeystrokeVector(BaseModel):
    """
    Objeto de Valor que representa o padrão rítmico de digitação.
    Garante que os dados biométricos são estritamente uma lista de números flutuantes.
    """
    features: List[float] = Field(..., description="Vetor de tempos extraídos (Hold e Up-Down)")

    def is_valid_length(self) -> bool:
        # A nossa arquitetura com AdaptiveMaxPool1d aceita tamanhos dinâmicos,
        # mas biologicamente precisamos de entropia mínima (ex: senha com min 8 caracteres)
        # Senhas muito curtas geram vetores muito pequenos para análise fiável.
        return len(self.features) >= 15