"""
Manages the full set of reverse tunnels — one per active radar.
Reconciles running tunnels against the current configuration on demand.
"""
import logging
from typing import Callable, Dict, Optional

from config import Config, RadarEntry
from tunnel import ReverseTunnel, STOPPED

log = logging.getLogger(__name__)


class TunnelManager:
    def __init__(self, on_status: Optional[Callable[[str, str], None]] = None):
        # radar_id → ReverseTunnel
        self._tunnels: Dict[str, ReverseTunnel] = {}
        self.on_status = on_status

    # ── Public ────────────────────────────────────────────────────────────────

    def apply_config(self, cfg: Config):
        """
        Start / stop / restart tunnels to match cfg.
        Called on startup and whenever the user saves new settings.
        """
        desired_ids = {r.id for r in cfg.radares if r.activo}

        # Stop tunnels removed from config or deactivated
        for rid in list(self._tunnels):
            if rid not in desired_ids:
                self._stop(rid)

        # Start or restart tunnels that need it
        for radar in cfg.radares:
            if not radar.activo:
                self._stop(radar.id)
                continue

            existing = self._tunnels.get(radar.id)
            if existing and existing.is_alive:
                # Restart only if connection params changed
                if self._params_changed(existing, radar, cfg):
                    self._stop(radar.id)
                else:
                    continue   # already running correctly

            self._start(radar, cfg)

    def stop_all(self):
        for rid in list(self._tunnels):
            self._stop(rid)

    def statuses(self) -> Dict[str, str]:
        """Return latest status for each tunnel (for the tray icon)."""
        return {rid: t._last_status for rid, t in self._tunnels.items()}

    # ── Private ───────────────────────────────────────────────────────────────

    def _start(self, radar: RadarEntry, cfg: Config):
        t = ReverseTunnel(
            radar_id=radar.id,
            nombre=radar.nombre,
            ssh_host=cfg.servidor.host,
            ssh_port=cfg.servidor.puerto,
            ssh_user=cfg.servidor.usuario,
            ssh_key_path=cfg.servidor.ruta_clave,
            remote_port=radar.puerto_remoto,
            local_host=radar.ip,
            local_port=radar.puerto_local,
            on_status=self._on_status,
        )
        t._last_status = "iniciando"
        self._tunnels[radar.id] = t
        t.start()
        log.info("Túnel iniciado: %s (%s:%d → :%d)",
                 radar.nombre, radar.ip, radar.puerto_local, radar.puerto_remoto)

    def _stop(self, radar_id: str):
        t = self._tunnels.pop(radar_id, None)
        if t:
            t.stop()
            if self.on_status:
                self.on_status(radar_id, STOPPED)
            log.info("Túnel detenido: %s", radar_id)

    def _on_status(self, radar_id: str, status: str):
        if radar_id in self._tunnels:
            self._tunnels[radar_id]._last_status = status
        if self.on_status:
            self.on_status(radar_id, status)

    @staticmethod
    def _params_changed(t: ReverseTunnel, radar: RadarEntry, cfg: Config) -> bool:
        return (
            t.ssh_host    != cfg.servidor.host   or
            t.ssh_port    != cfg.servidor.puerto  or
            t.ssh_user    != cfg.servidor.usuario or
            t.local_host  != radar.ip             or
            t.local_port  != radar.puerto_local   or
            t.remote_port != radar.puerto_remoto
        )
