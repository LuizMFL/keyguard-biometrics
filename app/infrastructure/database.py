from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# Para MVP rápido local, usamos SQLite. Para produção, basta trocar por:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@aws-sa-east-1.pooler.supabase.com:6543/postgres"
SQLALCHEMY_DATABASE_URL = "sqlite:///./keyguard.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# --- MODELO ORM (Como os dados ficam salvos fisicamente) ---
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # O Cofre Biométrico por Dispositivo. Formato esperado:
    # { "device_123": { "anchor": [0.1...], "history": [[0.1...], [0.1...]] } }
    device_biometrics = Column(JSON, nullable=True)

    current_mfa_code = Column(String, nullable=True)

# Cria as tabelas automaticamente no banco
Base.metadata.create_all(bind=engine)