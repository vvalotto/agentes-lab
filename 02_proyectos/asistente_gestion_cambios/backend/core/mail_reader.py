"""Adaptador de lectura de mail vía IMAP — el humano dispara, no el buzón.

Solo lee. No manda mails, no marca nada como leído (BODY.PEEK + select en
modo readonly), no crea nada en GitHub. Lo que este módulo produce (texto
plano de un correo) se manda tal cual al mismo POST /chat/mensaje que ya
existe para el canal chat — ver routers/mail.py. Ningún dato de acá llega
directo a SolicitudIn ni a GithubTracker.

Deliberadamente scoped a una sola etiqueta de Gmail (config.IMAP_ETIQUETA),
no a todo INBOX, para no mezclar mail personal real con las pruebas del
POC."""

from __future__ import annotations

import email
import imaplib
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime

from .. import config
from .models import CorreoResumen


class ImapNoConfiguradoError(Exception):
    """Faltan IMAP_USER / IMAP_APP_PASSWORD en el .env."""


def _conectar() -> imaplib.IMAP4_SSL:
    if not config.IMAP_USER or not config.IMAP_APP_PASSWORD:
        raise ImapNoConfiguradoError(
            "Falta IMAP_USER y/o IMAP_APP_PASSWORD en el .env del proyecto "
            "— ver .env.example para cómo generar la contraseña de aplicación."
        )
    # timeout explícito: IMAP4_SSL no tiene uno por default y puede colgarse
    # indefinidamente si algo en el camino (red, firewall) no responde.
    conexion = imaplib.IMAP4_SSL(config.IMAP_HOST, timeout=15)
    conexion.login(config.IMAP_USER, config.IMAP_APP_PASSWORD)
    resultado, _ = conexion.select(f'"{config.IMAP_ETIQUETA}"', readonly=True)
    if resultado != "OK":
        raise ValueError(
            f"No se pudo seleccionar la etiqueta '{config.IMAP_ETIQUETA}' — "
            f"¿existe con ese nombre exacto en Gmail?"
        )
    return conexion


def _decodificar(valor: str) -> str:
    partes = decode_header(valor or "")
    return "".join(
        texto.decode(codificacion or "utf-8") if isinstance(texto, bytes) else texto
        for texto, codificacion in partes
    )


def listar_recientes(limite: int = 10) -> list[CorreoResumen]:
    conexion = _conectar()
    try:
        _, datos = conexion.uid("search", None, "ALL")
        uids = datos[0].split()[-limite:]
        uids.reverse()  # más reciente primero

        resumenes = []
        for uid in uids:
            _, datos_msg = conexion.uid(
                "fetch", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
            )
            if not datos_msg or datos_msg[0] is None:
                continue
            mensaje = email.message_from_bytes(datos_msg[0][1])
            fecha_raw = mensaje.get("Date", "")
            try:
                fecha = parsedate_to_datetime(fecha_raw).strftime("%Y-%m-%d %H:%M")
            except (TypeError, ValueError):
                fecha = fecha_raw

            resumenes.append(
                CorreoResumen(
                    uid=uid.decode(),
                    remitente=_decodificar(mensaje.get("From", "(desconocido)")),
                    asunto=_decodificar(mensaje.get("Subject", "(sin asunto)")),
                    fecha=fecha,
                )
            )
        return resumenes
    finally:
        conexion.logout()


def leer_correo(uid: str) -> str:
    conexion = _conectar()
    try:
        _, datos = conexion.uid("fetch", uid, "(BODY.PEEK[])")
        if not datos or datos[0] is None:
            raise ValueError(f"No se encontró el correo con uid={uid}")
        mensaje = email.message_from_bytes(datos[0][1])
        asunto = _decodificar(mensaje.get("Subject", "(sin asunto)"))
        cuerpo = _extraer_texto_plano(mensaje)
        return f"Asunto: {asunto}\n\n{cuerpo}"
    finally:
        conexion.logout()


def _extraer_texto_plano(mensaje: Message) -> str:
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            if parte.get_content_type() == "text/plain" and not parte.get_filename():
                return _decodificar_payload(parte)
        for parte in mensaje.walk():
            if parte.get_content_type() == "text/html" and not parte.get_filename():
                return _decodificar_payload(parte)
        return "(no se encontró contenido de texto en el correo)"
    return _decodificar_payload(mensaje)


def _decodificar_payload(parte: Message) -> str:
    payload = parte.get_payload(decode=True) or b""
    charset = parte.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, TypeError):
        return payload.decode("utf-8", errors="replace")
