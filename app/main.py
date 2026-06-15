import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="KeyGuard Biometric API",
    description="Servidor de autenticação passiva e contínua baseado em dinâmica de digitação (Rede Siamesa Convolucional 1D).",
    version="1.0.0"
)

# Configuração de CORS para comunicação fluida com o Frontend HTML/JS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, substitua pelo domínio real da aplicação
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Acopla as rotas do ecossistema de autenticação
app.include_router(router)

frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def serve_frontend():
    # Quando entrar na raiz, carrega o HTML
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/")
def health_check():
    return {"status": "online", "system": "KeyGuard Biometric Core"}

if __name__ == "__main__":
    import uvicorn
    # Inicializa o servidor local na porta 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)