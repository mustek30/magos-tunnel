"""
Windows Service wrapper for MAGOS Tunnel.

Usage (from an elevated prompt):
    MAGOSTunnel.exe --install-service    → registers auto-start service
    MAGOSTunnel.exe --uninstall-service  → removes the service
    net start MAGOSTunnel                → manual start
    net stop  MAGOSTunnel                → manual stop
"""
import sys
import logging
import servicemanager
import win32event
import win32service
import win32serviceutil

import config as cfg_module
from tunnel_manager import TunnelManager

SERVICE_NAME    = "MAGOSTunnel"
SERVICE_DISPLAY = "MAGOS Tunnel"
SERVICE_DESC    = "Gestiona los túneles SSH seguros para los radares MAGOS"


class MAGOSTunnelService(win32serviceutil.ServiceFramework):
    _svc_name_         = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY
    _svc_description_  = SERVICE_DESC

    def __init__(self, args):
        super().__init__(args)
        self._stop_event = win32event.CreateEvent(None, 0, 0, None)
        self._manager    = TunnelManager()

        # Log to file (no console in service mode)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            filename=str(cfg_module.LOG_FILE),
            encoding="utf-8",
        )

    # ── SCM callbacks ─────────────────────────────────────────────────────────

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self._stop_event)
        self._manager.stop_all()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        cfg = cfg_module.load()
        self._manager.apply_config(cfg)
        # Block until SvcStop sets the event
        win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)


# ── Helpers called from main.py ───────────────────────────────────────────────

def install():
    """Register the service to start automatically."""
    sys.argv = [sys.argv[0], "--startup", "auto", "install"]
    win32serviceutil.HandleCommandLine(MAGOSTunnelService)


def uninstall():
    """Remove the service registration."""
    sys.argv = [sys.argv[0], "remove"]
    win32serviceutil.HandleCommandLine(MAGOSTunnelService)


def run_as_service():
    """Entry point when launched by the Windows SCM."""
    win32serviceutil.HandleCommandLine(MAGOSTunnelService)
