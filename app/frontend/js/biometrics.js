class KeystrokeDynamics {
    constructor(inputElementId, radarElementId = null) {
        this.inputElement = document.getElementById(inputElementId);
        this.radarElement = radarElementId ? document.getElementById(radarElementId) : null;
        this.keyEvents = [];
        this.vector = [];

        this.inputElement.addEventListener('input', (e) => {
            if (e.target.value.length === 0) this.reset();
        });

        this.inputElement.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.inputElement.addEventListener('keyup', (e) => this.handleKeyUp(e));
    }

    handleKeyDown(e) {
        // --- DEFESA ANTI-EVASÃO 1: BACKSPACE CIRÚRGICO ---
        if (e.key === 'Backspace') {
            // Se o usuário apagar, removemos os eventos da última tecla válida da pilha
            if (this.keyEvents.length >= 2) {
                this.keyEvents.pop(); // Remove o último 'up'
                this.keyEvents.pop(); // Remove o último 'down'
            }
            return;
        }

        // Ignora teclas de controle (Shift, Alt, CapsLock) para focar apenas em caracteres válidos
        if (e.key.length !== 1) return;

        this.keyEvents.push({
            key: e.key,
            type: 'down',
            time: performance.now()
        });
    }

    handleKeyUp(e) {
        if (e.key === 'Backspace' || e.key.length !== 1) return;

        this.keyEvents.push({
            key: e.key,
            type: 'up',
            time: performance.now()
        });

        if (this.radarElement) this.drawRadar();
    }

    generateVector() {
        this.vector = [];
        let downs = this.keyEvents.filter(e => e.type === 'down');
        let ups = this.keyEvents.filter(e => e.type === 'up');

        for (let i = 0; i < downs.length; i++) {
            if (ups[i]) {
                let holdTime = (ups[i].time - downs[i].time) / 1000.0;
                // Defesa contra trapaça de segurar tecla
                if (holdTime > 0.4) holdTime = 0.4;
                this.vector.push(holdTime);
            }

            if (i < downs.length - 1 && ups[i]) {
                let udTime = (downs[i+1].time - ups[i].time) / 1000.0;

                // --- DEFESA ANTI-EVASÃO 2: QUEBRA DE FLUIDEZ ---
                // Se o hacker esperar mais de 1.5s, ele quebrou a janela contínua.
                // Resetamos o buffer. Ele falhou em manter uma digitação humana fluida.
                if (udTime > 1.5) {
                    this.keyEvents = []; // Limpa o histórico de eventos imediatamente
                    this.vector = [];    // Destrói o vetor parcial
                    return [];           // Retorna vetor vazio para abortar o envio
                }

                this.vector.push(udTime);
            }
        }
        return this.vector;
    }

    reset() {
        this.keyEvents = [];
        this.vector = [];
        if (this.radarElement) {
            this.radarElement.innerHTML = '<span class="radar-empty-text">Radar Limpo</span>';
        }
    }

    drawRadar() {
        const vec = this.generateVector();
        this.radarElement.innerHTML = '';

        if (vec.length === 0) {
            this.radarElement.innerHTML = '<span class="radar-empty-text">Aguardando...</span>';
            return;
        }

        const maxTime = Math.max(...vec, 0.2);

        vec.forEach((timeValue, index) => {
            const bar = document.createElement('div');
            const isHold = index % 2 === 0;
            bar.className = `radar-bar ${isHold ? 'bar-hold' : 'bar-flight'}`;
            const heightPercent = (timeValue / maxTime) * 100;
            bar.style.height = `${heightPercent}%`;
            bar.title = `${isHold ? 'Hold' : 'Voo'}: ${timeValue.toFixed(3)}s`;
            this.radarElement.appendChild(bar);
        });
    }
}