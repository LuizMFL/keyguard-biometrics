class KeystrokeDynamics {
    // Adicionámos o parâmetro radarElementId para conectar a classe ao ecrã visual
    constructor(inputElementId, radarElementId = null) {
        this.inputElement = document.getElementById(inputElementId);
        this.radarElement = radarElementId ? document.getElementById(radarElementId) : null;

        this.keyEvents = [];
        this.vector = [];

        this.inputElement.addEventListener('input', (e) => {
            if (e.target.value.length === 0) {
                this.reset();
            }
        });

        this.inputElement.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.inputElement.addEventListener('keyup', (e) => this.handleKeyUp(e));
    }

    handleKeyDown(e) {
        if (e.key.length !== 1) return;

        this.keyEvents.push({
            key: e.key,
            type: 'down',
            time: performance.now()
        });
    }

    handleKeyUp(e) {
        if (e.key.length !== 1) return;

        this.keyEvents.push({
            key: e.key,
            type: 'up',
            time: performance.now()
        });

        // A CADA TECLA LEVANTADA, ATUALIZAMOS O RADAR VISUAL
        if (this.radarElement) {
            this.drawRadar();
        }
    }

    generateVector() {
        this.vector = [];
        let downs = this.keyEvents.filter(e => e.type === 'down');
        let ups = this.keyEvents.filter(e => e.type === 'up');

        for (let i = 0; i < downs.length; i++) {
            if (ups[i]) {
                let holdTime = (ups[i].time - downs[i].time) / 1000.0;
                this.vector.push(holdTime);
            }

            if (i < downs.length - 1 && ups[i]) {
                let udTime = (downs[i+1].time - ups[i].time) / 1000.0;
                this.vector.push(udTime);
            }
        }
        return this.vector;
    }

    drawRadar() {
        const vec = this.generateVector();
        this.radarElement.innerHTML = ''; // Limpa o radar anterior

        if (vec.length === 0) {
            this.radarElement.innerHTML = '<span class="radar-empty-text">Aguardando...</span>';
            return;
        }

        // Descobre o tempo mais longo para definir o teto do gráfico (100% de altura)
        // Adicionamos 0.2 como mínimo absoluto para barras muito pequenas não sumirem
        const maxTime = Math.max(...vec, 0.2);

        vec.forEach((timeValue, index) => {
            const bar = document.createElement('div');

            // Índices Pares (0, 2, 4...) são o Tempo de Hold (Azul)
            // Índices Ímpares (1, 3, 5...) são o Tempo de Voo (Vermelho)
            const isHold = index % 2 === 0;
            bar.className = `radar-bar ${isHold ? 'bar-hold' : 'bar-flight'}`;

            // Calcula a altura da barra proporcionalmente ao maior tempo digitado
            const heightPercent = (timeValue / maxTime) * 100;
            bar.style.height = `${heightPercent}%`;

            // Acessibilidade: Se passar o rato por cima, mostra os segundos exatos!
            bar.title = `${isHold ? 'Hold' : 'Voo'}: ${timeValue.toFixed(3)}s`;

            this.radarElement.appendChild(bar);
        });
    }

    reset() {
        this.keyEvents = [];
        this.vector = [];
        if (this.radarElement) {
            this.radarElement.innerHTML = '<span class="radar-empty-text">Radar Limpo</span>';
        }
    }
}