# MAGOS Tunnel

Servicio Windows que establece **túneles SSH reversos** seguros entre cada radar y el servidor MAGOS.

```
  Radar (Windows)          Internet / Red           Servidor MAGOS (Linux)
  ┌──────────────┐         ┌──────────┐             ┌────────────────────┐
  │  MAGOSTunnel ├─SSH──►──┤ Firewall ├─────────────►  sshd :22          │
  │  (este .exe) │         └──────────┘             │  localhost:9001 ───►  radar web
  └──────────────┘                                  └────────────────────┘
```

---

## 1 · Preparación del servidor MAGOS

### 1.1 Crear usuario de túnel (sin shell)

```bash
sudo adduser --system --no-create-home --shell /usr/sbin/nologin tunnel_magos
sudo mkdir -p /home/tunnel_magos/.ssh
sudo touch /home/tunnel_magos/.ssh/authorized_keys
sudo chown -R tunnel_magos: /home/tunnel_magos/.ssh
sudo chmod 700 /home/tunnel_magos/.ssh
sudo chmod 600 /home/tunnel_magos/.ssh/authorized_keys
```

### 1.2 Habilitar GatewayPorts en sshd

En `/etc/ssh/sshd_config`, agregar o descomentar:

```
GatewayPorts yes
AllowTcpForwarding yes
```

Reiniciar SSH:

```bash
sudo systemctl restart sshd
```

### 1.3 Nginx — proxy por radar

Cada radar ocupará un puerto diferente en el servidor (ej. 9001, 9002, …).
Agréguelo en la configuración de Nginx de MAGOS:

```nginx
# /etc/nginx/conf.d/magos_radares.conf
location /magos/radar_norte/ {
    proxy_pass http://127.0.0.1:9001/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

---

## 2 · Instalación en Windows

### 2.1 Requisitos

- Python 3.10+ (64-bit) — https://python.org
- Git (opcional)

### 2.2 Instalar dependencias y compilar

```bat
pip install -r requirements.txt
build.bat
```

El ejecutable quedará en `dist\MAGOSTunnel.exe`.

### 2.3 Primera ejecución

1. Doble-clic en `MAGOSTunnel.exe`
2. Aparece el ícono en la bandeja del sistema
3. Click derecho → **Configuración**

### 2.4 Configurar

| Campo | Valor |
|---|---|
| Nombre de la empresa | Su empresa |
| Host SSH | IP o dominio del servidor MAGOS |
| Puerto SSH | 22 (o el personalizado) |
| Usuario SSH | `tunnel_magos` |

Haga clic en **Generar clave SSH** y luego **Ver clave pública**.
Copie la clave y agréguela al servidor:

```bash
echo "ssh-rsa AAAA...clave... magos-tunnel" | \
  sudo tee -a /home/tunnel_magos/.ssh/authorized_keys
```

### 2.5 Agregar radares

Por cada radar:

| Campo | Descripción |
|---|---|
| Nombre del centro | Nombre descriptivo (ej. "Radar Norte") |
| IP del radar | IP local del equipo radar (ej. 192.168.1.50) |
| Puerto local | Puerto del servicio web del radar (ej. 80) |
| Puerto remoto | Puerto en el servidor MAGOS (ej. 9001) |

Haga clic en **Guardar configuración**.

### 2.6 Instalar como servicio Windows (recomendado)

Ejecute como Administrador:

```bat
install_service.bat
```

El servicio `MAGOSTunnel` quedará configurado para iniciar automáticamente con Windows, incluso sin usuario conectado.

---

## 3 · Mantenimiento

| Acción | Método |
|---|---|
| Ver estado | Ícono bandeja → click derecho → Estado de túneles |
| Ver logs | `%APPDATA%\MAGOS Tunnel\magos_tunnel.log` |
| Cambiar configuración | Ícono bandeja → Configuración |
| Desinstalar servicio | `uninstall_service.bat` (como admin) |

---

## 4 · Reconexión automática

El cliente reintenta la conexión **cada 15 segundos** ante cualquier falla:
- Corte de red
- Reinicio del servidor SSH
- Error en el radar
- Timeout de keepalive

Los túneles operan de forma independiente: si un radar falla, los demás siguen funcionando.
