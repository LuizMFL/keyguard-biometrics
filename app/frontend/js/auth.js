// ==========================================
// CONFIGURAÇÕES E ESTADO GLOBAL
// ==========================================
const API_BASE_URL = "http://127.0.0.1:8000/api/auth";

let deviceId = localStorage.getItem('device_id');
if (!deviceId) {
    deviceId = crypto.randomUUID();
    localStorage.setItem('device_id', deviceId);
}

const state = {
    currentUserEmail: null,
    registrationVectors: [],
    updateVectors: [],
    mfaRejectedVector: null
};

// ==========================================
// FUNÇÃO AUXILIAR: TRATAMENTO DE ERROS DO FASTAPI
// ==========================================
// Converte os erros complexos do FastAPI 422 em texto legível
function parseApiError(data) {
    if (!data.detail) return "Erro desconhecido no servidor.";
    if (Array.isArray(data.detail)) {
        // Pega no nome do campo que faltou e na mensagem de erro
        return data.detail.map(err => `Campo '${err.loc[err.loc.length-1]}': ${err.msg}`).join('\n');
    }
    return data.detail; // Erros normais (400, 401) vêm como string
}

// ==========================================
// INICIALIZAÇÃO DOS SENSORES BIOMÉTRICOS
// ==========================================
const loginBiometrics = new KeystrokeDynamics('login-password', 'radar-login');
const regCalibrationBiometrics = new KeystrokeDynamics('reg-calibration-input', 'radar-register');
const updCurrentBiometrics = new KeystrokeDynamics('upd-current-password');
const updCalibrationBiometrics = new KeystrokeDynamics('upd-calibration-input');

// ==========================================
// CONTROLO DE VISTAS (SPA)
// ==========================================
function showView(viewId) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));
    document.getElementById(viewId).classList.remove('hidden');
}

document.getElementById('link-to-register').addEventListener('click', (e) => { e.preventDefault(); showView('view-register'); });
document.getElementById('link-to-login').addEventListener('click', (e) => { e.preventDefault(); showView('view-login'); });
document.getElementById('btn-email-ok').addEventListener('click', () => showView('view-login'));
document.getElementById('btn-cancel-mfa').addEventListener('click', () => {
    state.mfaRejectedVector = null;
    showView('view-login');
});
document.getElementById('btn-logout').addEventListener('click', () => {
    state.currentUserEmail = null;
    loginBiometrics.reset();
    document.getElementById('form-login').reset();
    showView('view-login');
});

// ==========================================
// FLUXO 1: REGISTO COM CALIBRAÇÃO
// ==========================================
const regPasswordInput = document.getElementById('reg-password');
const regCalibrationInput = document.getElementById('reg-calibration-input');
const btnRegister = document.getElementById('btn-register');

regCalibrationInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        const basePassword = regPasswordInput.value;
        const currentAttempt = regCalibrationInput.value;

        if (basePassword.length < 8) return alert("A senha principal deve ter pelo menos 8 caracteres.");
        if (basePassword !== currentAttempt) {
            alert("A senha digitada não coincide com a principal. Tente novamente.");
            regCalibrationInput.value = '';
            regCalibrationBiometrics.reset();
            return;
        }

        const vector = regCalibrationBiometrics.generateVector();
        const expectedVectorLength = (basePassword.length * 2) - 1;
        if (vector.length !== expectedVectorLength) {
            alert("⚠️ Anomalia detetada (uso de Backspace ou correção rápida). Por favor, digite a senha de forma contínua e natural.");
            regCalibrationInput.value = '';
            regCalibrationBiometrics.reset();
            return;
        }

        state.registrationVectors.push(vector);
        let count = state.registrationVectors.length;
        document.getElementById('reg-count').innerText = count;
        document.getElementById('reg-progress').style.width = `${(count / 5) * 100}%`;

        regCalibrationInput.value = '';
        regCalibrationBiometrics.reset();

        if (count === 5) {
            regCalibrationInput.disabled = true;
            btnRegister.disabled = false;
        }
    }
});

document.getElementById('form-register').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                password: password,
                initial_vectors: state.registrationVectors,
                device_id: deviceId // <--- CORREÇÃO AQUI
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(parseApiError(data)); // <--- CORREÇÃO AQUI

        showView('view-email-confirm');
        document.getElementById('form-register').reset();
        state.registrationVectors = [];
    } catch (error) {
        alert(`❌ Erro no Registo:\n${error.message}`);
    }
});

// ==========================================
// FLUXO 2: LOGIN E MFA
// ==========================================
document.getElementById('form-login').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const vector = loginBiometrics.generateVector();

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                password: password,
                current_vector: vector,
                device_id: deviceId // <--- CORREÇÃO AQUI
            })
        });

        const data = await response.json();

        if (response.ok && data.authenticated) {
            state.currentUserEmail = email;
            document.getElementById('profile-email-display').innerText = email;
            showView('view-profile');
        } else if (response.status === 200 && data.require_mfa) {
            state.currentUserEmail = email;
            state.mfaRejectedVector = vector;
            showView('view-mfa');
        } else {
            throw new Error(parseApiError(data) || data.message || "Acesso Negado.");
        }
    } catch (error) {
        alert(`❌ Erro no Login:\n${error.message}`);
        loginBiometrics.reset();
        document.getElementById('login-password').value = '';
    }
});

// ==========================================
// FLUXO 3: VALIDAÇÃO MFA
// ==========================================
document.getElementById('form-mfa').addEventListener('submit', async (e) => {
    e.preventDefault();
    const code = document.getElementById('mfa-code').value;

    try {
        const response = await fetch(`${API_BASE_URL}/mfa-verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: state.currentUserEmail,
                mfa_code: code,
                rejected_vector: state.mfaRejectedVector,
                device_id: deviceId // <--- CORREÇÃO AQUI
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(parseApiError(data));

        alert(`✅ ${data.message}`);
        document.getElementById('profile-email-display').innerText = state.currentUserEmail;
        showView('view-profile');
        document.getElementById('mfa-code').value = '';
        state.mfaRejectedVector = null;
    } catch (error) {
        alert(`❌ MFA Falhou:\n${error.message}`);
    }
});

// ==========================================
// FLUXO 4: ALTERAÇÃO DE SENHA PROTEGIDA
// ==========================================
const updNewPasswordInput = document.getElementById('upd-new-password');
const updCalibrationInput = document.getElementById('upd-calibration-input');
const btnUpdatePass = document.getElementById('btn-update-pass');

updCalibrationInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        const newPassword = updNewPasswordInput.value;
        const currentAttempt = updCalibrationInput.value;

        if (newPassword.length < 8) return alert("A nova senha deve ter mín. 8 caracteres.");
        if (newPassword !== currentAttempt) {
            alert("A senha não coincide. Tente novamente.");
            updCalibrationInput.value = '';
            updCalibrationBiometrics.reset();
            return;
        }

        const vector = updCalibrationBiometrics.generateVector();
        const expectedVectorLength = (newPassword.length * 2) - 1;
        if (vector.length !== expectedVectorLength) {
            alert("⚠️ Anomalia detetada (uso de Backspace ou correção). Por favor, digite a senha de forma contínua.");
            updCalibrationInput.value = '';
            updCalibrationBiometrics.reset();
            return;
        }

        state.updateVectors.push(vector);
        let count = state.updateVectors.length;
        document.getElementById('upd-count').innerText = count;
        document.getElementById('upd-progress').style.width = `${(count / 5) * 100}%`;

        updCalibrationInput.value = '';
        updCalibrationBiometrics.reset();

        if (count === 5) {
            updCalibrationInput.disabled = true;
            btnUpdatePass.disabled = false;
        }
    }
});

document.getElementById('form-update-password').addEventListener('submit', async (e) => {
    e.preventDefault();
    const currentPassword = document.getElementById('upd-current-password').value;
    const currentVector = updCurrentBiometrics.generateVector();
    const newPassword = updNewPasswordInput.value;

    try {
        const response = await fetch(`${API_BASE_URL}/update-password`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: state.currentUserEmail,
                current_password: currentPassword,
                current_vector: currentVector,
                new_password: newPassword,
                new_initial_vectors: state.updateVectors,
                device_id: deviceId // <--- CORREÇÃO AQUI
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(parseApiError(data));

        alert(`✅ ${data.message}`);
        document.getElementById('form-update-password').reset();
        updCurrentBiometrics.reset();
        updCalibrationInput.disabled = false;
        btnUpdatePass.disabled = true;
        state.updateVectors = [];
        document.getElementById('upd-count').innerText = '0';
        document.getElementById('upd-progress').style.width = '0%';

    } catch (error) {
        alert(`❌ Erro de Segurança:\n${error.message}`);
        updCurrentBiometrics.reset();
        document.getElementById('upd-current-password').value = '';
    }
});