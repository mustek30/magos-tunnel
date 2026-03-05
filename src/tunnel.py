"""
Single reverse SSH tunnel with automatic reconnection.

Equivalent to:  ssh -N -R 0.0.0.0:<remote_port>:<local_host>:<local_port> user@ssh_server

Flow:
  radar web service  ←TCP←  this machine  ←SSH reverse tunnel→  MAGOS server:remote_port
"""
import socket
import threading
import time
import logging
from typing import Callable, Optional

import paramiko

log = logging.getLogger(__name__)

# Status constants
CONNECTING = "conectando"
CONNECTED  = "conectado"
ERROR      = "error"
STOPPED    = "detenido"

RETRY_DELAY    = 15   # seconds between reconnect attempts
KEEPALIVE_SECS = 30   # SSH keepalive interval
ACCEPT_TIMEOUT = 1.0  # seconds for transport.accept()


class ReverseTunnel:
    """
    Manages a persistent reverse SSH tunnel for one radar endpoint.
    Runs in a background thread; restarts the tunnel on any failure.
    """

    def __init__(
        self,
        *,
        radar_id:     str,
        nombre:       str,
        ssh_host:     str,
        ssh_port:     int,
        ssh_user:     str,
        ssh_key_path: str,
        remote_port:  int,
        local_host:   str,
        local_port:   int,
        on_status: Optional[Callable[[str, str], None]] = None,
    ):
        self.radar_id     = radar_id
        self.nombre       = nombre
        self.ssh_host     = ssh_host
        self.ssh_port     = ssh_port
        self.ssh_user     = ssh_user
        self.ssh_key_path = ssh_key_path
        self.remote_port  = remote_port
        self.local_host   = local_host
        self.local_port   = local_port
        self.on_status    = on_status

        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name=f"tunnel-{self.radar_id}",
        )
        self._thread.start()

    def stop(self):
        self._running = False

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _notify(self, status: str):
        log.info("[%s] %s", self.nombre, status)
        if self.on_status:
            try:
                self.on_status(self.radar_id, status)
            except Exception:
                pass

    def _loop(self):
        """Outer reconnect loop."""
        while self._running:
            try:
                self._connect_and_serve()
            except Exception as exc:
                log.error("[%s] %s", self.nombre, exc)
            if self._running:
                self._notify(ERROR)
                time.sleep(RETRY_DELAY)
        self._notify(STOPPED)

    def _connect_and_serve(self):
        """Connect to SSH server, request remote port-forward, serve channels."""
        self._notify(CONNECTING)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            self.ssh_host,
            port=self.ssh_port,
            username=self.ssh_user,
            key_filename=self.ssh_key_path,
            timeout=30,
            banner_timeout=30,
            auth_timeout=30,
            look_for_keys=False,
            allow_agent=False,
        )

        transport = client.get_transport()
        transport.set_keepalive(KEEPALIVE_SECS)

        # Request the server to forward connections on remote_port back to us
        transport.request_port_forward("", self.remote_port)
        self._notify(CONNECTED)

        try:
            while self._running and transport.is_active():
                channel = transport.accept(timeout=ACCEPT_TIMEOUT)
                if channel is not None:
                    threading.Thread(
                        target=self._handle_channel,
                        args=(channel,),
                        daemon=True,
                    ).start()
        finally:
            try:
                transport.cancel_port_forward("", self.remote_port)
            except Exception:
                pass
            client.close()

    def _handle_channel(self, channel: paramiko.Channel):
        """Bridge an incoming SSH channel to the local radar TCP port."""
        try:
            sock = socket.create_connection(
                (self.local_host, self.local_port), timeout=10
            )
        except OSError as exc:
            log.warning(
                "[%s] No se puede conectar a %s:%d — %s",
                self.nombre, self.local_host, self.local_port, exc,
            )
            channel.close()
            return

        def pipe(src, dst):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
            except Exception:
                pass
            finally:
                for obj in (src, dst):
                    try:
                        obj.close()
                    except Exception:
                        pass

        threading.Thread(target=pipe, args=(channel, sock), daemon=True).start()
        threading.Thread(target=pipe, args=(sock, channel), daemon=True).start()
