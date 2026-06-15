from typing import Optional
from sqlalchemy.orm import Session
from app.domain.entities import User, DeviceBiometricState
from app.domain.value_objects import KeystrokeVector
from app.domain.interfaces import IUserRepository
from app.infrastructure.database import UserModel

class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, db_session: Session):
        self.db = db_session

    def _to_domain(self, model: UserModel) -> User:
        device_bio_dict = {}
        if model.device_biometrics:
            for dev_id, data in model.device_biometrics.items():
                anchor = KeystrokeVector(features=data['anchor'])
                history = [KeystrokeVector(features=h) for h in data['history']]
                device_bio_dict[dev_id] = DeviceBiometricState(anchor, history)

        return User(
            user_id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            device_biometrics=device_bio_dict,
            current_mfa_code=model.current_mfa_code
        )

    def _to_json(self, device_biometrics_dict: dict) -> dict:
        json_data = {}
        for dev_id, state in device_biometrics_dict.items():
            json_data[dev_id] = {
                "anchor": state.anchor.features,
                "history": [h.features for h in state.history]
            }
        return json_data

    def save(self, user: User) -> User:
        db_user = UserModel(
            email=user.email,
            password_hash=user.password_hash,
            device_biometrics=self._to_json(user.device_biometrics),
            current_mfa_code=user.current_mfa_code
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_domain(db_user)

    def get_by_email(self, email: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not model:
            return None
        return self._to_domain(model)

    def update(self, user: User) -> User:
        db_user = self.db.query(UserModel).filter(UserModel.id == user.user_id).first()
        if db_user:
            db_user.password_hash = user.password_hash
            db_user.device_biometrics = self._to_json(user.device_biometrics)
            db_user.current_mfa_code = user.current_mfa_code
            self.db.commit()
            self.db.refresh(db_user)
        return self._to_domain(db_user)
