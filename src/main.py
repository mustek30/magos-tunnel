"""
MAGOS Tunnel — entry point.

Modes:
  (no args)               → system-tray app  (normal use)
  --install-service       → register Windows service (run as admin)
  --uninstall-service     → remove Windows service   (run as admin)
  --service               → internal: called by Windows SCM
  --config                → open config window only (no tray)
"""
import sys
import logging
import config as cfg_module


def _setup_logging():
    cfg_module.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(cfg_module.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    _setup_logging()
    args = set(sys.argv[1:])

    if "--install-service" in args:
        from service import install
        install()
        return

    if "--uninstall-service" in args:
        from service import uninstall
        uninstall()
        return

    if "--service" in args:
        # Launched by Windows SCM
        from service import run_as_service
        run_as_service()
        return

    if "--config" in args:
        from gui import open_config
        open_config()
        return

    # Default: system-tray mode
    from tray import run_tray
    run_tray()


if __name__ == "__main__":
    main()
