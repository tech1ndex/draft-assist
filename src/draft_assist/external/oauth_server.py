from __future__ import annotations

import datetime
import ssl
import tempfile
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

if TYPE_CHECKING:
    import socket

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate_self_signed_cert() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False
        )
        .sign(key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return cert_pem.decode(), key_pem.decode()


def wrap_socket_ssl(sock: socket.socket) -> ssl.SSLSocket:
    cert_pem, key_pem = generate_self_signed_cert()
    cert_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w", suffix=".pem", delete=False
    )
    key_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w", suffix=".pem", delete=False
    )
    try:
        cert_file.write(cert_pem)
        cert_file.close()
        key_file.write(key_pem)
        key_file.close()
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert_file.name, key_file.name)
        return ctx.wrap_socket(sock, server_side=True)
    finally:
        Path(cert_file.name).unlink(missing_ok=True)
        Path(key_file.name).unlink(missing_ok=True)


def wait_for_auth_code(port: int = 8888, timeout: int = 120) -> str:
    auth_code: str | None = None
    error: str | None = None

    class CallbackHandler(BaseHTTPRequestHandler):
        def __init__(
            self,
            request: socket.socket | tuple[bytes, socket.socket],
            client_address: tuple[str, int],
            http_server: HTTPServer,
        ) -> None:
            super().__init__(request, client_address, http_server)

        def do_GET(self) -> None:  # noqa: N802
            nonlocal auth_code, error
            query = parse_qs(urlparse(self.path).query)
            auth_code = query.get("code", [None])[0]
            error = query.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html = b"<html><body><h2>Authorization complete. You can close this window.</h2></body></html>"
            self.wfile.write(html)

    server = HTTPServer(("localhost", port), CallbackHandler)
    server.socket = wrap_socket_ssl(server.socket)
    server.timeout = 2
    deadline = time.monotonic() + timeout

    while auth_code is None and error is None and time.monotonic() < deadline:
        server.handle_request()

    server.server_close()

    if error:
        msg = f"OAuth error: {error}"
        raise RuntimeError(msg)
    if not auth_code:
        msg = "No authorization code received (timed out)"
        raise RuntimeError(msg)

    return auth_code
