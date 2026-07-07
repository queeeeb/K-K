# Despliegue en DigitalOcean (sin dominio, HTTPS con sslip.io)

Orión corre con Docker Compose: `frontend-build` compila el React, `backend` (FastAPI) sirve la API, `caddy` es el reverse proxy que saca HTTPS automático y sirve el frontend.

Sin dominio propio usamos **sslip.io**: un DNS gratis que resuelve `<IP>.sslip.io` a tu IP, con lo que Caddy consigue certificado Let's Encrypt real (sin advertencias del navegador, sin registro).

## 1. Crear el Droplet

- DigitalOcean → Create → Droplet.
- Imagen: **Ubuntu 24.04 LTS**.
- Plan: **Basic Regular, 2 GB RAM / 1 CPU** (~$12/mes). Con 1 GB el build de Vite puede quedarse sin memoria.
- Autenticación: sube tu **SSH key** (recomendado) o usa contraseña.
- Crea el droplet y anota su **IP pública** (ej. `165.227.10.42`).

## 2. Abrir el firewall

En DigitalOcean → Networking → Firewalls (o con `ufw` en el droplet), permite entrantes:
- **22** (SSH), **80** (HTTP / reto de Let's Encrypt), **443** (HTTPS).

Con ufw en el droplet:
```bash
ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw enable
```

## 3. Entrar e instalar Docker

```bash
ssh root@<IP>

# Docker + plugin de compose (script oficial)
curl -fsSL https://get.docker.com | sh
docker compose version   # debe imprimir la versión
```

## 4. Traer el código

El repo es privado. Usa un **Personal Access Token** de GitHub (Settings → Developer settings → Tokens, con permiso `repo`) o una deploy key.

```bash
cd /opt
git clone https://<TU_USUARIO>:<TU_TOKEN>@github.com/queeeeb/K-K.git
cd K-K/proyectos/activos/agente-financiero-ptres
git checkout feat/interfaz-subida
```

## 5. Crear el `.env` del servidor

En `agente-financiero-ptres/.env` (este archivo NO está en git, se crea a mano en el servidor):

```env
AGENTE_JWT_SECRET=<pega aquí el resultado de: openssl rand -hex 32>
ANTHROPIC_API_KEY=sk-ant-...
SITE_ADDRESS=<IP>.sslip.io
```

- `AGENTE_JWT_SECRET`: genera uno con `openssl rand -hex 32` (mínimo 32 chars).
- `SITE_ADDRESS`: tu IP con `.sslip.io` al final, ej. `165.227.10.42.sslip.io`. **Con esto Caddy saca HTTPS solo.** Si lo dejas vacío o pones `:80`, corre en HTTP sin cifrar.

## 6. Levantar

```bash
docker compose up -d --build
```

La primera vez tarda: compila el frontend y baja imágenes. Verifica:
```bash
docker compose ps                 # backend y caddy en Up, frontend-build en Exited (normal)
docker compose logs caddy | tail  # debe mostrar que obtuvo el certificado
```

Abre `https://<IP>.sslip.io` en el navegador — candado verde, sin advertencia.

## 7. Crear los usuarios de P3

No hay registro público; los usuarios se crean por línea de comando (pide la contraseña de forma interactiva):

```bash
docker compose exec backend uv run python scripts/crear_usuario.py <usuario>
```

Repite por cada persona de P3.

## 8. Asegurar la base de datos

```bash
docker compose exec backend chmod 600 /data/agente.db
```

## Operación

- **Ver logs:** `docker compose logs -f backend`
- **Actualizar tras un cambio en git:**
  ```bash
  git pull
  docker compose up -d --build
  ```
- **Reiniciar:** `docker compose restart backend`
- **Backup de datos:** el volumen `agente_data` guarda `agente.db` y los reportes generados. Respáldalo con:
  ```bash
  docker run --rm -v agente-financiero-ptres_agente_data:/data -v $(pwd):/backup alpine tar czf /backup/agente_backup.tgz /data
  ```

## Notas

- El certificado HTTPS se renueva solo (Caddy lo gestiona) y persiste en el volumen `caddy_data`.
- Google Drive ya no interviene: las 4 fuentes y el archivo base se suben desde la interfaz. No hace falta service account ni variables de Drive.
- Si cambias de IP (recrear el droplet), actualiza `SITE_ADDRESS` en `.env` y `docker compose up -d`.
