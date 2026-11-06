import asyncio
import logging
import re
import sys
from decimal import Decimal, InvalidOperation
from uuid import uuid4

import httpx
from sqlalchemy import select, desc

from app.main import settings, SessionLocal
from app.telegram_models import SolicitudTelegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Evitar que httpx/httpcore impriman URLs que contienen el token de Telegram.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("prestaia.telegram")

TOKEN = settings.telegram_bot_token
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Conversaciones activas en memoria.
conversaciones = {}

PASOS = [
    ("nombres", "Escribe tus nombres:", "texto"),
    ("apellidos", "Escribe tus apellidos:", "texto"),
    ("tipo_documento", "¿Qué documento tienes? Escribe DNI o CE:", "documento"),
    ("numero_documento", "Escribe tu número de documento:", "numero_documento"),
    ("celular", "Escribe tu celular de contacto:", "celular"),
    ("correo", "Escribe tu correo electrónico o escribe - para omitirlo:", "correo"),
    ("direccion", "Escribe tu dirección o - para omitirla:", "texto"),
    ("ocupacion", "¿Cuál es tu ocupación actual?", "texto"),
    ("ingresos_mensuales", "¿Cuáles son tus ingresos mensuales en soles? Ejemplo: 1800.00", "dinero"),
    ("monto_solicitado", "¿Qué monto deseas solicitar en soles?", "dinero"),
    ("plazo_meses", "¿En cuántos meses deseas pagar? Escribe un número entre 1 y 120:", "plazo"),
    ("consentimiento_datos",
     "Para continuar debes aceptar el tratamiento de tus datos personales para gestionar esta solicitud.\n\n"
     "Escribe SI para aceptar o NO para cancelar.", "consentimiento"),
]

async def telegram(client, method, **params):
    response = await client.post(f"{BASE_URL}/{method}", json=params)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Error de Telegram"))
    return data["result"]

async def enviar(client, chat_id, texto):
    await telegram(client, "sendMessage", chat_id=chat_id, text=texto)

def validar(tipo, valor):
    valor = valor.strip()

    if tipo == "texto":
        if len(valor) < 2 or len(valor) > 120:
            raise ValueError("Escribe un texto válido de entre 2 y 120 caracteres.")
        return valor

    if tipo == "documento":
        valor = valor.upper()
        if valor not in ("DNI", "CE"):
            raise ValueError("Escribe DNI o CE.")
        return valor

    if tipo == "numero_documento":
        if not re.fullmatch(r"[A-Za-z0-9]{6,15}", valor):
            raise ValueError("El documento debe tener entre 6 y 15 caracteres alfanuméricos.")
        return valor.upper()

    if tipo == "celular":
        limpio = re.sub(r"[\s+-]", "", valor)
        if not re.fullmatch(r"\d{9,15}", limpio):
            raise ValueError("Escribe un número de celular válido, incluyendo código de país si corresponde.")
        return limpio

    if tipo == "correo":
        if valor == "-":
            return None
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
            raise ValueError("El correo no parece válido. Intenta otra vez o escribe - para omitirlo.")
        return valor.lower()

    if tipo == "dinero":
        try:
            numero = Decimal(valor.replace(",", "."))
        except InvalidOperation:
            raise ValueError("Escribe un importe numérico. Ejemplo: 1500.00")
        if not numero.is_finite() or numero <= 0 or numero > Decimal("9999999999"):
            raise ValueError("El importe debe ser mayor que cero.")
        return numero

    if tipo == "plazo":
        if not valor.isdigit() or not 1 <= int(valor) <= 120:
            raise ValueError("El plazo debe ser un número entre 1 y 120 meses.")
        return int(valor)

    raise ValueError("Respuesta no válida.")

def guardar_solicitud(datos, user, chat_id):
    if SessionLocal is None:
        raise RuntimeError("La base de datos no está configurada.")

    # El consentimiento se guarda una sola vez, como valor validado.
    campos = {k: v for k, v in datos.items() if k != "consentimiento_datos"}

    codigo = "PTG-" + uuid4().hex[:10].upper()

    with SessionLocal() as db:
        solicitud = SolicitudTelegram(
            codigo=codigo,
            telegram_user_id=str(user["id"]),
            telegram_chat_id=str(chat_id),
            telegram_username=user.get("username"),
            **campos,
            consentimiento_datos=True,
            estado="pendiente",
        )
        db.add(solicitud)
        db.commit()
        return codigo

async def procesar_mensaje(client, message):
    chat = message.get("chat", {})
    user = message.get("from", {})
    chat_id = chat.get("id")
    user_id = user.get("id")

    if not chat_id or not user_id:
        return

    # No procesar grupos: los datos financieros son privados.
    if chat.get("type") != "private":
        await enviar(client, chat_id, "Por seguridad, utiliza el bot en una conversación privada.")
        return

    texto = (message.get("text") or "").strip()
    comando = texto.split()[0].lower() if texto.startswith("/") else ""

    if comando == "/start":
        await enviar(
            client, chat_id,
            "¡Bienvenido a PRESTAIA — Asistente Financiero!\n\n"
            "Puedo ayudarte a registrar una solicitud de préstamo.\n\n"
            "Comandos disponibles:\n"
            "/solicitar - iniciar solicitud\n"
            "/estado - consultar tu última solicitud\n"
            "/asesor - solicitar atención de un asesor\n"
            "/cancelar - cancelar el formulario\n\n"
            "No compartas contraseñas ni claves bancarias."
        )
        return

    if comando == "/cancelar":
        conversaciones.pop(str(chat_id), None)
        await enviar(client, chat_id, "Formulario cancelado. Puedes iniciar otro con /solicitar.")
        return

    if comando == "/solicitar":
        conversaciones[str(chat_id)] = {"indice": 0, "datos": {}}
        await enviar(client, chat_id, "Iniciemos tu solicitud. Responde una pregunta a la vez.\n\n" + PASOS[0][1])
        return

    if comando == "/estado":
        try:
            with SessionLocal() as db:
                solicitud = db.scalar(
                    select(SolicitudTelegram)
                    .where(SolicitudTelegram.telegram_user_id == str(user_id))
                    .order_by(desc(SolicitudTelegram.creado_en))
                    .limit(1)
                )
            if not solicitud:
                await enviar(client, chat_id, "Todavía no tienes solicitudes registradas. Usa /solicitar para comenzar.")
            else:
                await enviar(
                    client, chat_id,
                    f"Tu última solicitud:\nCódigo: {solicitud.codigo}\nEstado: {solicitud.estado.upper()}\n"
                    "La evaluación final corresponde al personal autorizado de PRESTAIA."
                )
        except Exception:
            log.exception("Error consultando estado")
            await enviar(client, chat_id, "No se pudo consultar tu estado. Intenta más tarde.")
        return

    if comando == "/asesor":
        try:
            with SessionLocal() as db:
                solicitud = db.scalar(
                    select(SolicitudTelegram)
                    .where(SolicitudTelegram.telegram_user_id == str(user_id))
                    .order_by(desc(SolicitudTelegram.creado_en))
                    .limit(1)
                )
                if solicitud:
                    solicitud.requiere_asesor = True
                    db.commit()
                    respuesta = f"Tu solicitud de asesoría quedó registrada. Código: {solicitud.codigo}."
                else:
                    respuesta = "Todavía no tienes una solicitud registrada. Usa /solicitar primero."
            await enviar(client, chat_id, respuesta)
        except Exception:
            log.exception("Error solicitando asesor")
            await enviar(client, chat_id, "No se pudo registrar tu solicitud de asesoría. Intenta más tarde.")
        return

    estado = conversaciones.get(str(chat_id))
    if not estado:
        await enviar(client, chat_id, "Para comenzar escribe /solicitar. Para ver los comandos escribe /start.")
        return

    # Tras aceptar consentimiento, se permite una fotografía opcional.
    if estado.get("esperando_foto"):
        if message.get("photo"):
            estado["datos"]["foto_file_id"] = message["photo"][-1]["file_id"]
        elif texto.lower() in ("/omitir", "omitir", "no"):
            estado["datos"]["foto_file_id"] = None
        else:
            await enviar(client, chat_id, "Envía una fotografía o escribe /omitir para continuar.")
            return

        try:
            codigo = guardar_solicitud(estado["datos"], user, chat_id)
            conversaciones.pop(str(chat_id), None)
            await enviar(
                client, chat_id,
                f"¡Solicitud registrada correctamente!\n\n"
                f"Código de seguimiento: {codigo}\n"
                "Estado inicial: PENDIENTE\n\n"
                "Nuestro equipo revisará la información. Puedes consultar el estado con /estado."
            )
        except Exception:
            log.exception("No se pudo guardar la solicitud")
            await enviar(
                client, chat_id,
                "No se pudo guardar tu solicitud porque la base de datos aún no está disponible "
                "o necesita la migración de Telegram. Tus respuestas no se han confirmado como registradas. "
                "Intenta nuevamente más tarde."
            )
        return

    indice = estado["indice"]
    campo, pregunta, tipo = PASOS[indice]

    try:
        if tipo == "consentimiento":
            respuesta = texto.lower()
            if respuesta not in ("si", "sí", "no"):
                raise ValueError("Responde SI para aceptar o NO para cancelar.")
            if respuesta == "no":
                conversaciones.pop(str(chat_id), None)
                await enviar(client, chat_id, "No se registró ninguna solicitud porque no aceptaste el consentimiento.")
                return
            estado["datos"][campo] = True
            estado["esperando_foto"] = True
            await enviar(client, chat_id, "¿Deseas adjuntar una fotografía opcional? Envíala ahora o escribe /omitir.")
            return

        valor = validar(tipo, texto)
        estado["datos"][campo] = valor
        estado["indice"] += 1

        if estado["indice"] < len(PASOS):
            siguiente = PASOS[estado["indice"]][1]
            await enviar(client, chat_id, siguiente)
        else:
            await enviar(client, chat_id, "Formulario completado. Continuemos.")
    except ValueError as exc:
        await enviar(client, chat_id, str(exc))

async def main():
    if not TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en backend/.env")

    timeout = httpx.Timeout(45.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        me = await telegram(client, "getMe")
        webhook = await telegram(client, "getWebhookInfo")

        if webhook.get("url"):
            raise RuntimeError(
                "El bot tiene un webhook configurado. Desactívalo antes de usar long polling."
            )

        log.info("Bot conectado: @%s", me.get("username"))
        log.info("Iniciando recepción de mensajes. Mantén esta terminal abierta.")

        offset = None
        while True:
            try:
                params = {"timeout": 30}
                if offset is not None:
                    params["offset"] = offset

                updates = await telegram(client, "getUpdates", **params)
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if message:
                        try:
                            await procesar_mensaje(client, message)
                        except Exception:
                            log.exception("Error procesando actualización Telegram")
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Error de conexión con Telegram; reintentando en 5 segundos.")
                await asyncio.sleep(5)

if __name__ == "__main__":
    if "--check" in sys.argv:
        async def check():
            if not TOKEN:
                raise RuntimeError("TELEGRAM_BOT_TOKEN no configurado")
            async with httpx.AsyncClient(timeout=15) as client:
                me = await telegram(client, "getMe")
                webhook = await telegram(client, "getWebhookInfo")
                print("Conexión Telegram: OK")
                print("Bot:", me.get("username"))
                print("Webhook configurado:", bool(webhook.get("url")))
        asyncio.run(check())
    else:
        asyncio.run(main())
