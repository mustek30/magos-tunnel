"""
Configuration window — tkinter.

Opens a dark-themed window with:
  · Company name
  · SSH server settings + SSH key generation
  · Radar list (add / edit / remove)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from pathlib import Path

import config as cfg_module
from config import Config, RadarEntry, ServidorSSH

# ─── Colour palette ───────────────────────────────────────────────────────────
BG       = "#0d1117"
BG2      = "#161b22"
BG3      = "#21262d"
ACCENT   = "#00d4aa"
FG       = "#e6edf3"
FG_DIM   = "#8b949e"
BORDER   = "#30363d"
RED      = "#f85149"
GREEN    = "#3fb950"


def _style(root: tk.Tk):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".",           background=BG,  foreground=FG,  bordercolor=BORDER)
    s.configure("TFrame",      background=BG)
    s.configure("TLabel",      background=BG,  foreground=FG)
    s.configure("TLabelframe", background=BG,  foreground=FG_DIM, bordercolor=BORDER)
    s.configure("TLabelframe.Label", background=BG, foreground=ACCENT)
    s.configure("TEntry",      fieldbackground=BG3, foreground=FG, bordercolor=BORDER,
                insertcolor=FG)
    s.configure("TButton",     background=BG3, foreground=FG, bordercolor=BORDER,
                focuscolor=ACCENT)
    s.map("TButton", background=[("active", BG2)])
    s.configure("TCheckbutton", background=BG, foreground=FG)
    s.configure("Treeview",    background=BG3, foreground=FG,
                fieldbackground=BG3, bordercolor=BORDER, rowheight=24)
    s.configure("Treeview.Heading", background=BG2, foreground=ACCENT,
                bordercolor=BORDER)
    s.map("Treeview", background=[("selected", "#1f6feb")])
    s.configure("TScrollbar",  background=BG3, troughcolor=BG, bordercolor=BORDER)


# ─── Main Config Window ───────────────────────────────────────────────────────

class ConfigWindow:
    def __init__(self, cfg: Config, on_save: Optional[Callable] = None):
        self.cfg     = cfg
        self.on_save = on_save
        self._build()

    def _build(self):
        self.root = tk.Tk()
        self.root.title("MAGOS Tunnel — Configuración")
        self.root.geometry("740x580")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        _style(self.root)

        # Header
        hdr = tk.Frame(self.root, bg="#0f3460", height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="MAGOS  TUNNEL", bg="#0f3460", fg=ACCENT,
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=20, pady=14)
        tk.Label(hdr, text="Configuración de túneles SSH seguros",
                 bg="#0f3460", fg=FG_DIM, font=("Segoe UI", 9)).pack(side="left")

        body = ttk.Frame(self.root, padding=16)
        body.pack(fill="both", expand=True)

        # ── Empresa ──────────────────────────────────────────────────────────
        fr_emp = ttk.LabelFrame(body, text=" Empresa ", padding=10)
        fr_emp.pack(fill="x", pady=(0, 10))
        ttk.Label(fr_emp, text="Nombre de la empresa:").grid(row=0, column=0, sticky="w")
        self.e_empresa = ttk.Entry(fr_emp, width=48)
        self.e_empresa.insert(0, self.cfg.empresa)
        self.e_empresa.grid(row=0, column=1, padx=10)

        # ── Servidor SSH ─────────────────────────────────────────────────────
        fr_srv = ttk.LabelFrame(body, text=" Servidor SSH (MAGOS) ", padding=10)
        fr_srv.pack(fill="x", pady=(0, 10))

        fields_srv = [("Host:", "host", 26), ("Puerto:", "puerto", 7), ("Usuario SSH:", "usuario", 16)]
        self._srv_entries = {}
        for col, (lbl, key, w) in enumerate(fields_srv):
            ttk.Label(fr_srv, text=lbl).grid(row=0, column=col * 2, sticky="w", padx=(8 if col else 0, 4))
            e = ttk.Entry(fr_srv, width=w)
            e.insert(0, str(getattr(self.cfg.servidor, key)))
            e.grid(row=0, column=col * 2 + 1, padx=(0, 12))
            self._srv_entries[key] = e

        btn_row = ttk.Frame(fr_srv)
        btn_row.grid(row=1, column=0, columnspan=6, pady=(10, 0), sticky="w")
        ttk.Button(btn_row, text="⚙  Generar clave SSH",    command=self._gen_key).pack(side="left")
        ttk.Button(btn_row, text="🔑  Ver clave pública",   command=self._show_pubkey).pack(side="left", padx=8)

        # ── Radares ──────────────────────────────────────────────────────────
        fr_rad = ttk.LabelFrame(body, text=" Radares ", padding=10)
        fr_rad.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("nombre", "ip", "p_local", "p_remoto", "estado")
        self.tree = ttk.Treeview(fr_rad, columns=cols, show="headings", height=7,
                                  selectmode="browse")
        for col, hdr_text, width in [
            ("nombre",   "Nombre del centro", 180),
            ("ip",       "IP del radar",      130),
            ("p_local",  "Puerto local",      100),
            ("p_remoto", "Puerto remoto",     110),
            ("estado",   "Estado",             80),
        ]:
            self.tree.heading(col, text=hdr_text)
            self.tree.column(col, width=width, anchor="center")

        sb = ttk.Scrollbar(fr_rad, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._refresh_tree()

        # Buttons below tree
        btn_rad = ttk.Frame(body)
        btn_rad.pack(fill="x")
        ttk.Button(btn_rad, text="＋  Agregar radar", command=self._add).pack(side="left")
        ttk.Button(btn_rad, text="✏  Editar",         command=self._edit).pack(side="left", padx=6)
        ttk.Button(btn_rad, text="🗑  Eliminar",       command=self._delete).pack(side="left")
        ttk.Button(btn_rad, text="💾  Guardar configuración",
                   command=self._save).pack(side="right")

    # ── Radar list helpers ────────────────────────────────────────────────────

    def _refresh_tree(self, statuses: dict = None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in self.cfg.radares:
            st = (statuses or {}).get(r.id, "—")
            tag = "ok" if st == "conectado" else "err" if st == "error" else ""
            self.tree.insert("", "end", iid=r.id, tags=(tag,),
                             values=(r.nombre, r.ip, r.puerto_local, r.puerto_remoto, st))
        self.tree.tag_configure("ok",  foreground=GREEN)
        self.tree.tag_configure("err", foreground=RED)

    def update_statuses(self, statuses: dict):
        self._refresh_tree(statuses)

    def _selected_radar(self) -> Optional[RadarEntry]:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione un radar de la lista.")
            return None
        return next((r for r in self.cfg.radares if r.id == sel[0]), None)

    def _add(self):
        RadarDialog(self.root, RadarEntry(), self._on_radar_saved)

    def _edit(self):
        r = self._selected_radar()
        if r:
            RadarDialog(self.root, r, self._on_radar_saved)

    def _delete(self):
        r = self._selected_radar()
        if r and messagebox.askyesno("Confirmar", f"¿Eliminar el radar «{r.nombre}»?"):
            self.cfg.radares = [x for x in self.cfg.radares if x.id != r.id]
            self._refresh_tree()

    def _on_radar_saved(self, radar: RadarEntry):
        idx = next((i for i, r in enumerate(self.cfg.radares) if r.id == radar.id), None)
        if idx is not None:
            self.cfg.radares[idx] = radar
        else:
            self.cfg.radares.append(radar)
        self._refresh_tree()

    # ── Save ─────────────────────────────────────────────────────────────────

    def _save(self):
        try:
            puerto = int(self._srv_entries["puerto"].get().strip())
        except ValueError:
            messagebox.showerror("Error", "El puerto SSH debe ser un número entero.")
            return

        self.cfg.empresa            = self.e_empresa.get().strip()
        self.cfg.servidor.host      = self._srv_entries["host"].get().strip()
        self.cfg.servidor.puerto    = puerto
        self.cfg.servidor.usuario   = self._srv_entries["usuario"].get().strip()

        if not self.cfg.servidor.host:
            messagebox.showerror("Error", "El host del servidor SSH es requerido.")
            return

        cfg_module.save(self.cfg)
        if self.on_save:
            self.on_save()
        messagebox.showinfo("Guardado", "Configuración guardada correctamente.\n"
                                         "Los túneles se actualizarán automáticamente.")

    # ── SSH key management ────────────────────────────────────────────────────

    def _gen_key(self):
        from paramiko import RSAKey
        key_path = Path(self.cfg.servidor.ruta_clave)
        if key_path.exists():
            if not messagebox.askyesno(
                "Confirmar",
                "Ya existe una clave SSH.\n"
                "¿Generar una nueva? Deberá volver a autorizar el acceso al servidor."
            ):
                return

        key_path.parent.mkdir(parents=True, exist_ok=True)
        k = RSAKey.generate(bits=4096)
        k.write_private_key_file(str(key_path))
        with open(str(key_path) + ".pub", "w") as f:
            f.write(f"ssh-rsa {k.get_base64()} magos-tunnel\n")

        messagebox.showinfo(
            "Clave generada",
            f"Clave RSA 4096 generada correctamente.\n\n"
            f"Archivo: {key_path}\n\n"
            "Haga clic en «Ver clave pública» para copiarla al servidor."
        )
        self._show_pubkey()

    def _show_pubkey(self):
        pub_path = Path(self.cfg.servidor.ruta_clave + ".pub")
        if not pub_path.exists():
            messagebox.showerror("Error", "No hay clave pública.\nUse «Generar clave SSH» primero.")
            return

        with open(pub_path) as f:
            pubkey = f.read().strip()

        win = tk.Toplevel(self.root)
        win.title("Clave pública SSH")
        win.geometry("620x220")
        win.configure(bg=BG)
        win.grab_set()

        tk.Label(win, bg=BG, fg=FG,
                 text="Agregue esta línea al archivo  ~/.ssh/authorized_keys  del servidor MAGOS:",
                 wraplength=580, justify="left", pady=8).pack(padx=16)

        txt = tk.Text(win, height=4, wrap="word", bg=BG3, fg=ACCENT,
                      insertbackground=FG, relief="flat", bd=4,
                      font=("Consolas", 9))
        txt.insert("1.0", pubkey)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True, padx=16)

        def _copy():
            win.clipboard_clear()
            win.clipboard_append(pubkey)
            messagebox.showinfo("Copiado", "Clave copiada al portapapeles.", parent=win)

        tk.Button(win, text="📋  Copiar al portapapeles", command=_copy,
                  bg=BG3, fg=FG, relief="flat", padx=10, pady=6).pack(pady=10)

    def run(self):
        self.root.mainloop()


# ─── Radar Dialog ─────────────────────────────────────────────────────────────

class RadarDialog:
    def __init__(self, parent, radar: RadarEntry, on_save: Callable):
        self._radar  = RadarEntry(**radar.__dict__)   # copy
        self.on_save = on_save
        self._build(parent)

    def _build(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Configurar radar")
        self.win.geometry("400x290")
        self.win.resizable(False, False)
        self.win.configure(bg=BG)
        self.win.grab_set()
        _style(self.win)

        frm = ttk.Frame(self.win, padding=20)
        frm.pack(fill="both", expand=True)

        fields = [
            ("Nombre del centro:",          "nombre",        self._radar.nombre,       32),
            ("IP del radar:",               "ip",            self._radar.ip,           20),
            ("Puerto local (servicio radar):", "puerto_local",  str(self._radar.puerto_local), 10),
            ("Puerto remoto (servidor):",   "puerto_remoto", str(self._radar.puerto_remoto), 10),
        ]
        self._entries: dict = {}
        for i, (lbl, key, val, w) in enumerate(fields):
            ttk.Label(frm, text=lbl).grid(row=i, column=0, sticky="w", pady=6)
            e = ttk.Entry(frm, width=w)
            e.insert(0, val)
            e.grid(row=i, column=1, padx=12, pady=6)
            self._entries[key] = e

        self._activo = tk.BooleanVar(value=self._radar.activo)
        ttk.Checkbutton(frm, text="Túnel activo", variable=self._activo).grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(10, 0)
        )

        btn = ttk.Frame(frm)
        btn.grid(row=len(fields) + 1, column=0, columnspan=2, pady=14)
        ttk.Button(btn, text="Guardar",   command=self._save).pack(side="left", padx=4)
        ttk.Button(btn, text="Cancelar",  command=self.win.destroy).pack(side="left")

    def _save(self):
        nombre = self._entries["nombre"].get().strip()
        ip     = self._entries["ip"].get().strip()
        if not nombre or not ip:
            messagebox.showerror("Error", "Nombre e IP son obligatorios.", parent=self.win)
            return
        try:
            p_local  = int(self._entries["puerto_local"].get())
            p_remoto = int(self._entries["puerto_remoto"].get())
        except ValueError:
            messagebox.showerror("Error", "Los puertos deben ser números enteros.", parent=self.win)
            return

        self._radar.nombre        = nombre
        self._radar.ip            = ip
        self._radar.puerto_local  = p_local
        self._radar.puerto_remoto = p_remoto
        self._radar.activo        = self._activo.get()

        self.on_save(self._radar)
        self.win.destroy()


# ─── Entry point ─────────────────────────────────────────────────────────────

def open_config(on_save: Optional[Callable] = None):
    cfg = cfg_module.load()
    ConfigWindow(cfg, on_save=on_save).run()
