import torch
import torch.nn as nn
import torch.nn.functional as F

OPERATIONAL_THRESHOLD = 0.500
EVOLUTION_THRESHOLD = 0.300

# --- NÚMEROS DE OURO UNIVERSAIS (Substitua pelos valores do Notebook 01) ---
GLOBAL_HOLD_MEAN = 0.0891
GLOBAL_HOLD_STD = 0.0288
GLOBAL_FLIGHT_MEAN = 0.1494
GLOBAL_FLIGHT_STD = 0.1739


# --------------------------------------------------------------------------

class KeyGuardSiameseDynamic(nn.Module):
    # ... (Mantenha a sua classe de arquitetura exatamente igual)
    def __init__(self):
        super(KeyGuardSiameseDynamic, self).__init__()
        self.cnn = nn.Sequential(
            nn.Conv1d(1, 16, 3, padding=1),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(16, 32, 3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(5)
        )
        self.fc = nn.Sequential(
            nn.Linear(160, 64),
            nn.ReLU(),
            nn.Linear(64, 16)
        )

    def forward_once(self, x):
        x = self.cnn(x)
        x = x.view(x.size()[0], -1)
        return self.fc(x)

    def forward(self, input1, input2):
        return self.forward_once(input1), self.forward_once(input2)


class BiometricAIService:
    def __init__(self, model_path: str):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = KeyGuardSiameseDynamic().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def _normalize_dynamic_vector(self, vector: list) -> list:
        """
        Aplica a Regra Universal de Z-Score respeitando a biologia da digitação.
        Índices pares sofrem Z-Score de Hold. Índices ímpares sofrem Z-Score de Voo.
        """
        norm_vec = []
        for i, val in enumerate(vector):
            if i % 2 == 0:
                z = (val - GLOBAL_HOLD_MEAN) / GLOBAL_HOLD_STD
            else:
                z = (val - GLOBAL_FLIGHT_MEAN) / GLOBAL_FLIGHT_STD
            norm_vec.append(z)
        return norm_vec

    def verify_attempt(self, anchor_features: list, attempt_features: list) -> dict:

        # 1. Normalização Universal
        norm_anchor = self._normalize_dynamic_vector(anchor_features)
        norm_attempt = self._normalize_dynamic_vector(attempt_features)

        # 2. Construção dos Tensores
        tensor_anchor = torch.tensor([norm_anchor], dtype=torch.float32).unsqueeze(1).to(self.device)
        tensor_attempt = torch.tensor([norm_attempt], dtype=torch.float32).unsqueeze(1).to(self.device)

        with torch.no_grad():
            out_anchor, out_attempt = self.model(tensor_anchor, tensor_attempt)
            distance = F.pairwise_distance(out_anchor, out_attempt).item()

        is_authentic = distance <= OPERATIONAL_THRESHOLD
        qualifies_for_evolution = distance <= EVOLUTION_THRESHOLD

        return {
            "is_authentic": is_authentic,
            "distance": distance,
            "qualifies_for_evolution": qualifies_for_evolution
        }