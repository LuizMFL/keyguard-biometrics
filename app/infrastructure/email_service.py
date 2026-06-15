import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.domain.interfaces import IEmailService

# --- CONFIGURAÇÃO DO SERVIDOR SMTP ---
# Dica: Pode usar o Mailtrap (SaaS gratuito de testes) ou o Gmail com "Palavra-passe de app"
SMTP_SERVER = "smtp.gmail.com"  # Altere para o seu provedor se necessário
SMTP_PORT = 587
SMTP_USER = "joingames.m.miguel@gmail.com"
SMTP_PASSWORD = "qssd heef vgpk ohyv"

class SmtpEmailService(IEmailService):
    def _send(self, to_email: str, subject: str, html_content: str):
        # Se as credenciais não estiverem configuradas, apenas loga no terminal para não quebrar
        if "AQUI" in SMTP_USER:
            print(f"\n[MOCK EMAIL] Para: {to_email} | Assunto: {subject}\nConteúdo: {html_content}\n")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"KeyGuard Core <security@keyguard.io>"
        msg["To"] = to_email

        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()  # Ativa criptografia de transporte TLS
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(msg["From"], to_email, msg.as_string())
        except Exception as e:
            print(f"Erro crítico ao enviar e-mail via SMTP: {str(e)}")

    def send_welcome_email(self, to_email: str) -> None:
        subject = "🛡️ Conta Ativada com Sucesso - KeyGuard"
        html = f"""
        <html>
            <body style="font-family: sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
                <h2 style="color: #3b82f6;">Bem-vindo ao KeyGuard Core!</h2>
                <p>A sua conta foi registada com sucesso.</p>
                <p style="color: #94a3b8; font-size: 0.9rem;">A sua assinatura biométrica rítmica foi consolidada e está a proteger o seu acesso.</p>
            </body>
        </html>
        """
        self._send(to_email, subject, html)

    def send_mfa_code(self, to_email: str, code: str) -> None:
        subject = "⚠️ Código de Verificação MFA - KeyGuard"
        html = f"""
        <html>
            <body style="font-family: sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
                <h2 style="color: #ef4444;">Tentativa de Login Incomum</h2>
                <p>Detetámos um acesso a partir de um novo dispositivo ou com um ritmo rítmico diferente do seu padrão.</p>
                <p>Utilize o código de segurança abaixo para autorizar o acesso:</p>
                <div style="background-color: #1e293b; padding: 15px; text-align: center; font-size: 2rem; font-weight: bold; letter-spacing: 5px; color: #3b82f6; border-radius: 6px; margin: 20px 0;">
                    {code}
                </div>
                <p style="color: #94a3b8; font-size: 0.8rem;">Se não tentou fazer login, altere a sua senha imediatamente.</p>
            </body>
        </html>
        """
        self._send(to_email, subject, html)