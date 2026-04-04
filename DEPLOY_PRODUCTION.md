# Deploy de Produccion con Docker Swarm - Tickets Nova

Objetivo: desplegar de forma profesional con Swarm, optimizar recursos, evitar errores de CORS, dejar creado el primer usuario administrador cuando la BD inicia en cero y publicar SEO correctamente para Google.

---

## 0) Resumen ejecutivo

Que se usa en produccion:

1. `docker-compose.production.yml` como archivo de stack para Swarm.
2. Servicios: `frontend`, `backend`, `mysql`, `redis`.
3. Rolling updates con rollback automatico en `frontend` y `backend`.
4. Limites y reservas de CPU/RAM para uso eficiente.
5. Bootstrap seguro del primer admin con script operativo.
6. Metadatos SEO, `robots.txt` y `sitemap.xml` generados en build para facilitar indexacion.

Archivos clave:

- `docker-compose.production.yml`
- `Frontend/Dockerfile`
- `Frontend/nginx.conf`
- `Backend/Dockerfile`
- `Backend/.env.example`
- `Backend/app/scripts/bootstrap_admin.py`

---

## 1) Requisitos previos

En el/los servidor(es):

1. Docker Engine 24+.
2. Swarm habilitado.
3. Acceso a un registry de imagenes (Docker Hub, GHCR o privado).
4. DNS y TLS configurados para frontend y API.

Comandos de verificacion:

```bash
docker --version
docker info | grep -i swarm
```

Si Swarm no esta activo:

```bash
docker swarm init
```

---

## 2) Variables de entorno

## 2.1 Backend/.env (obligatorio)

Usa `Backend/.env.example` como base y completa secretos reales.

Variables criticas:

```env
DATABASE_URL=mysql+pymysql://root:TU_PASSWORD@mysql:3306/tickets_db
MYSQL_ROOT_PASSWORD=TU_PASSWORD
MYSQL_DATABASE=tickets_db

APP_NAME=tickets_api
ENV=production
DEBUG=false
FRONTEND_PUBLIC_URL=https://tickets.tudominio.com
UVICORN_WORKERS=2

JWT_SECRET_KEY=MINIMO_32_CARACTERES
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

REDIS_URL=redis://tickets_redis:6379
REDIS_CONNECT_RETRY_SECONDS=30

ALLOWED_ORIGINS=["https://tickets.tudominio.com","https://www.tickets.tudominio.com"]
CORS_ALLOW_ORIGIN_REGEX=

DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT_SECONDS=30
DB_POOL_RECYCLE_SECONDS=1800
DB_POOL_PRE_PING=true

GZIP_ENABLED=true
GZIP_MINIMUM_SIZE_BYTES=1024
GZIP_COMPRESSLEVEL=6
```

## 2.2 Frontend/.env (obligatorio para SEO y marca)

Configura `Frontend/.env` con valores reales de produccion.

Plantilla recomendada:

```env
VITE_API_BASE_URL=https://api.tudominio.com
VITE_SITE_URL=https://tickets.tudominio.com
VITE_SITE_LANGUAGE=es
VITE_SITE_LOCALE=es_DO

VITE_BRAND_NAME=Tickets Nova
VITE_BRAND_LEGAL_NAME=Tickets Nova
VITE_BRAND_LOGO_PATH=/assets/tickets-nova-logo.png
VITE_BRAND_FAVICON_PATH=/assets/tickets-nova-logo.png
VITE_BRAND_OG_IMAGE_PATH=/assets/tickets-nova-logo.png

VITE_SUPPORT_EMAIL=soporte@ticketsnova.com
VITE_SUPPORT_WHATSAPP_DISPLAY=+1 (628) 465-7863
VITE_SUPPORT_WHATSAPP_DIGITS=16284657863
VITE_FACEBOOK_URL=

VITE_SEO_DEFAULT_TITLE=Tickets Nova | Compra segura de tickets
VITE_SEO_DEFAULT_DESCRIPTION=Plataforma profesional para compra segura de tickets, seguimiento de pagos y soporte especializado.
VITE_SEO_ROBOTS=index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1
VITE_SEO_THEME_COLOR=#0b2f4f
VITE_SEO_TWITTER_SITE=
VITE_SEO_TWITTER_CREATOR=

# Se completa cuando Google/Bing entreguen el codigo de verificacion
VITE_SEO_GOOGLE_SITE_VERIFICATION=
VITE_SEO_BING_SITE_VERIFICATION=
```

Reglas simples para no romper SEO:

1. `VITE_SITE_URL` siempre debe ser el dominio real publico (no localhost).
2. Usa `https://` en frontend y API.
3. Si cambias `VITE_SITE_URL`, debes reconstruir imagen frontend.

## 2.3 Variables de imagen para el stack

Antes del deploy, exporta las imagenes a usar:

```bash
export BACKEND_IMAGE=registry.tudominio.com/tickets/backend:2026-04-04
export FRONTEND_IMAGE=registry.tudominio.com/tickets/frontend:2026-04-04
```

---

## 3) Build y push de imagenes

Desde la raiz del repo:

```bash
# Backend
docker build -t "$BACKEND_IMAGE" ./Backend
docker push "$BACKEND_IMAGE"

# Frontend
docker build -t "$FRONTEND_IMAGE" ./Frontend
docker push "$FRONTEND_IMAGE"
```

Nota: en Swarm, lo profesional es desplegar imagenes versionadas desde registry (no depender de build en caliente).

Nota SEO importante: el build frontend ejecuta `seo:generate` automaticamente y genera `robots.txt` y `sitemap.xml` con el dominio de `VITE_SITE_URL`.

---

## 4) Deploy con Swarm (stack)

Desde la raiz del repo:

```bash
docker stack deploy -c docker-compose.production.yml tickets
```

Ver estado:

```bash
docker stack services tickets
docker stack ps tickets
```

Ver logs:

```bash
docker service logs -f tickets_backend
docker service logs -f tickets_frontend
docker service logs -f tickets_mysql
docker service logs -f tickets_redis
```

Health checks rapidos:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1/
```

---

## 5) CORS sin errores (clave)

Regla simple:

- En `ALLOWED_ORIGINS` va el dominio del frontend, no el de la API.

Ejemplo correcto:

```env
ALLOWED_ORIGINS=["https://tickets.tudominio.com"]
CORS_ALLOW_ORIGIN_REGEX=
```

Buenas practicas:

1. No usar `*` en produccion.
2. Usar `https` siempre.
3. Si usas `www` y no `www`, agrega ambos.
4. Tras cambiar CORS, fuerza update del backend:

```bash
docker service update --force tickets_backend
```

---

## 6) Optimizacion de recursos en Swarm

El `docker-compose.production.yml` ya incluye:

1. `deploy.resources.limits` y `reservations` por servicio.
2. `deploy.update_config` con rolling update.
3. `deploy.rollback_config` para volver atras si falla.
4. `replicas: 2` en frontend y backend para alta disponibilidad.

Escalar manualmente:

```bash
docker service scale tickets_backend=3
docker service scale tickets_frontend=3
```

Sugerencia practica:

1. Si tienes 1 solo nodo pequeno, usa backend=1 y frontend=1.
2. Si tienes 2+ nodos y buen CPU/RAM, mantén backend=2 y frontend=2.

---

## 7) BD en cero: crear schema + primer admin

Cuando la base esta vacia, no existe admin inicial y la ruta `/usuarios` requiere admin.

Se agrega script oficial:

- `Backend/app/scripts/bootstrap_admin.py`

Que hace:

1. Verifica/crea tablas (`Base.metadata.create_all`).
2. Crea admin si no existe.
3. Si el usuario ya existe, lo promueve a admin activo.
4. Opcionalmente resetea password del admin existente.

## 7.1 Ejecutar bootstrap del admin

1. Toma un contenedor activo del backend:

```bash
BACKEND_CID=$(docker ps --filter "label=com.docker.swarm.service.name=tickets_backend" --format "{{.ID}}" | head -n 1)
```

2. Ejecuta el bootstrap:

```bash
docker exec -it "$BACKEND_CID" python /app/app/scripts/bootstrap_admin.py \
  --email admin@tudominio.com \
  --password 'Admin2026!ClaveSuperSegura#01' \
  --nombre Admin \
  --apellido Principal \
  --pais DO
```

3. Si ese correo ya existia y quieres reset de clave:

```bash
docker exec -it "$BACKEND_CID" python /app/app/scripts/bootstrap_admin.py \
  --email admin@tudominio.com \
  --password 'Admin2026!NuevaClave#99' \
  --reset-password-if-exists
```

Politica de password exigida por el backend:

1. Minimo 20 caracteres.
2. Al menos una minuscula.
3. Al menos una mayuscula.
4. Al menos un numero.
5. Al menos un simbolo.

---

## 8) Validacion final de salida a produccion

Checklist go/no-go:

1. `docker stack services tickets` sin replicas caidas.
2. `GET /health` responde 200.
3. Frontend carga catalogo sin error CORS.
4. Login funciona con admin bootstrap.
5. Operaciones de panel/admin responden correctamente.
6. Logs sin `5xx` repetitivos.
7. `https://tu-dominio/robots.txt` responde 200.
8. `https://tu-dominio/sitemap.xml` responde 200 y contiene tu dominio real.

---

## 9) SEO + Google Search Console (paso a paso para principiantes)

Esta seccion esta pensada literal para "hacer clic y ejecutar".

## 9.1 Elige tu dominio final

Define una sola version canonica (ejemplo: `https://tickets.tudominio.com`).

No mezcles versiones:

1. con `www` y sin `www` al mismo tiempo;
2. con `http` y `https` al mismo tiempo.

## 9.2 Configura el frontend para SEO

1. Edita `Frontend/.env`.
2. Verifica que `VITE_SITE_URL` tenga el dominio final.
3. Guarda.

## 9.3 Reconstruye y publica frontend

Cada cambio de `.env` requiere rebuild:

```bash
# en tu maquina de build
docker build -t "$FRONTEND_IMAGE" ./Frontend
docker push "$FRONTEND_IMAGE"

# en el manager de Swarm
docker stack deploy -c docker-compose.production.yml tickets
```

## 9.4 Comprueba que SEO esta publicado

Abre en navegador:

1. `https://tu-dominio/robots.txt`
2. `https://tu-dominio/sitemap.xml`

Si ambas URLs cargan, Google ya puede leerlas.

## 9.5 Valida propiedad en Google (metodo recomendado: DNS)

1. Ve a `https://search.google.com/search-console`.
2. Clic en "Agregar propiedad".
3. Elige "Dominio".
4. Google te da un registro TXT.
5. Ve al panel DNS de tu dominio (Cloudflare/Namecheap/GoDaddy/etc).
6. Crea registro TXT exactamente como lo entrega Google.
7. Espera propagacion (5 a 30 min, a veces mas).
8. Vuelve a Search Console y pulsa "Verificar".

Ventaja: este metodo cubre subdominios y es mas estable.

## 9.6 Metodo alterno (si no puedes tocar DNS): meta tag

1. En Search Console usa propiedad de "Prefijo de URL".
2. Copia el valor de verificacion que da Google.
3. Pegalo en:

```env
VITE_SEO_GOOGLE_SITE_VERIFICATION=valor_que_te_da_google
```

4. Rebuild + deploy de frontend.
5. Pulsa "Verificar" en Search Console.

## 9.7 Envia el sitemap a Google

1. En Search Console entra a "Sitemaps".
2. En "Añadir sitemap" escribe: `sitemap.xml`.
3. Enviar.

## 9.8 Pide indexacion de paginas clave

Usa "Inspeccion de URL" y solicita indexacion para:

1. `/`
2. `/contact`
3. `/terms`
4. `/privacy`
5. `/refunds`

## 9.9 Que NO debe indexarse

No indexar rutas privadas:

1. `/admin`
2. `/user`
3. `/login`
4. `/payment/*`

Esto ya esta contemplado en metadatos y `robots.txt`.

## 9.10 Verificacion rapida post-configuracion

1. Search Console: propiedad validada.
2. Sitemap: estado "Correcto".
3. Coverage/Pages: sin bloqueos inesperados en paginas publicas.
4. Navegador: ver fuente HTML y confirmar meta robots/canonical.

---

## 10) Operacion diaria (comandos utiles)

```bash
# redespliegue del stack
docker stack deploy -c docker-compose.production.yml tickets

# ver servicios
docker stack services tickets

# ver tareas
docker stack ps tickets

# escalar backend
docker service scale tickets_backend=3

# forzar reinicio backend
docker service update --force tickets_backend

# rollback backend
docker service rollback tickets_backend

# eliminar stack
docker stack rm tickets
```

---

## 11) Recomendacion profesional para hoy

Secuencia recomendada:

1. Cargar `Backend/.env` con valores reales.
2. Cargar `Frontend/.env` con `VITE_SITE_URL` y datos SEO.
3. Build + push de imagenes versionadas.
4. `docker stack deploy`.
5. Ejecutar bootstrap del primer admin.
6. Validar CORS, login, compra y panel.
7. Validar Google Search Console + sitemap.
8. Monitorear 30-60 minutos.

Con esto sales a produccion con Swarm, control de recursos, rollback, SEO listo para indexacion y procedimiento formal de arranque desde cero.
