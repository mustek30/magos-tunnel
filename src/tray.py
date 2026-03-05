"""
System-tray application.
Icon colour reflects tunnel health:
  🟢 green  — all connected
  🟡 yellow — connecting / partial
  🔴 red    — at least one error
  ⚫ grey   — no radars configured
"""
import os
import threading
import logging
from typing import Dict

import pystray
from PIL import Image, ImageDraw

import config as cfg_module
from tunnel_manager import TunnelManager
from tunnel import CONNECTED, ERROR, STOPPED

log = logging.getLogger(__name__)


# ─── Icon generation ──────────────────────────────────────────────────────────

_COLORS = {
    "green":  (63, 185, 80),
    "yellow": (210, 153, 34),
    "red":    (248, 81, 73),
    "grey":   (110, 118, 129),
}


def _make_icon(color_name: str = "grey") -> Image.Image:
    size   = 64
    margin = 6
    color  = _COLORS.get(color_name, _COLORS["grey"])
    img    = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw   = ImageDraw.Draw(img)
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill=color + (255,))
    # Inner "M" hint
    draw.rectangle([24, 22, 28, 44], fill=(0, 0, 0, 180))
    draw.rectangle([36, 22, 40, 44], fill=(0, 0, 0, 180))
    draw.rectangle([24, 22, 40, 28], fill=(0, 0, 0, 180))
    return img


def _overall_color(statuses: Dict[str, str]) -> str:
    if not statuses:
        return "grey"
    vals = set(statuses.values())
    if vals == {CONNECTED}:
        return "green"
    if ERROR in vals or STOPPED in vals:
        return "red"
    return "yellow"


# ─── Tray App ─────────────────────────────────────────────────────────────────

class TrayApp:
    def __init__(self):
        self._cfg       = cfg_module.load()
        self._statuses: Dict[str, str] = {}
        self._manager   = TunnelManager(on_status=self._on_status)
        self._icon: pystray.Icon = None
        self._config_win = None   # keep reference so it's not GC'd

    def run(self):
        self._manager.apply_config(self._cfg)
        self._icon = pystray.Icon(
            name="MAGOS Tunnel",
            icon=_make_icon("grey"),
            title="MAGOS Tunnel",
            menu=pystray.Menu(
                pystray.MenuItem("Configuración",        self._open_config, default=True),
                pystray.MenuItem("Estado de túneles",    self._show_status),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Instalar servicio Windows",   self._install_service),
                pystray.MenuItem("Desinstalar servicio Windows", self._uninstall_service),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Descargar última versión", self._open_download),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Salir", self._quit),
            ),
        )
        self._icon.run()

    # ── Status handling ───────────────────────────────────────────────────────

    def _on_status(self, radar_id: str, status: str):
        self._statuses[radar_id] = status
        if self._icon:
            self._icon.icon  = _make_icon(_overall_color(self._statuses))
            self._icon.title = f"MAGOS Tunnel — {self._summary()}"

    def _summary(self) -> str:
        total = len(self._statuses)
        ok    = sum(1 for s in self._statuses.values() if s == CONNECTED)
        return f"{ok}/{total} conectados"

    # ── Menu actions ──────────────────────────────────────────────────────────

    def _open_config(self):
        threading.Thread(target=self._launch_config, daemon=True).start()

    def _launch_config(self):
        import gui
        gui.open_config(on_save=self._reload)

    def _reload(self):
        self._cfg = cfg_module.load()
        self._manager.apply_config(self._cfg)

    def _show_status(self):
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        lines = [f"Empresa: {self._cfg.empresa or '(sin configurar)'}", ""]
        for r in self._cfg.radares:
            st   = self._statuses.get(r.id, "—")
            dot  = "●" if st == CONNECTED else "○"
            lines.append(f"  {dot}  {r.nombre}   {r.ip}:{r.puerto_local} → :{r.puerto_remoto}   [{st}]")
        if not self._cfg.radares:
            lines.append("  (sin radares configurados)")
        messagebox.showinfo("Estado de túneles MAGOS", "\n".join(lines), parent=root)
        root.destroy()

    def _install_service(self):
        import subprocess, sys
        subprocess.run([sys.executable, "--install-service"], check=False)

    def _uninstall_service(self):
        import subprocess, sys
        subprocess.run([sys.executable, "--uninstall-service"], check=False)

    def _open_download(self):
        import webbrowser
        webbrowser.open("https://github.com/mustek30/magos-tunnel/releases/latest/download/MAGOSTunnel.exe")

    def _quit(self):
        self._manager.stop_all()
        if self._icon:
            self._icon.stop()
        os._exit(0)


def run_tray():
    TrayApp().run()
