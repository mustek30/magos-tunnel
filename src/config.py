"""
Configuration management — reads/writes config.json in AppData.
"""
import json
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List

# Storage location on Windows: %APPDATA%\MAGOS Tunnel\config.json
CONFIG_DIR  = Path.home() / "AppData" / "Roaming" / "MAGOS Tunnel"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE    = CONFIG_DIR / "magos_tunnel.log"


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ServidorSSH:
    host:       str = ""
    puerto:     int = 22
    usuario:    str = "magos"
    ruta_clave: str = str(CONFIG_DIR / "magos_tunnel_key")


@dataclass
class RadarEntry:
    id:             str  = field(default_factory=lambda: uuid.uuid4().hex[:8])
    nombre:         str  = ""
    ip:             str  = ""
    puerto_local:   int  = 80
    puerto_remoto:  int  = 9000
    activo:         bool = True


@dataclass
class Config:
    empresa:  str          = ""
    servidor: ServidorSSH  = field(default_factory=ServidorSSH)
    radares:  List[RadarEntry] = field(default_factory=list)


# ─── Load / Save ──────────────────────────────────────────────────────────────

def load() -> Config:
    if not CONFIG_FILE.exists():
        return Config()
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        srv     = ServidorSSH(**data.get("servidor", {}))
        radares = [RadarEntry(**r) for r in data.get("radares", [])]
        return Config(
            empresa=data.get("empresa", ""),
            servidor=srv,
            radares=radares,
        )
    except Exception:
        return Config()


def save(cfg: Config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "empresa":  cfg.empresa,
                "servidor": asdict(cfg.servidor),
                "radares":  [asdict(r) for r in cfg.radares],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
