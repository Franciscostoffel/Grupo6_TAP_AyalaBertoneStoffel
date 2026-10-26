# Grupo6_TAP_AyalaBertoneStoffel

# Inversión Inteligente

Sistema web para comparar diferentes opciones de inversión
según el capital disponible, plazo y nivel de riesgo aceptable.

## Aplicación en la nube

- Web: [Inversión Inteligente](https://inversion-inteligente-u4se.onrender.com/).
- API: [Documentación interactiva](https://inversion-inteligente-u4se.onrender.com/docs).

El servicio utiliza Render Free. Después de un período de inactividad, el
primer acceso puede demorar mientras el servicio arranca y reconstruye su caché.

## Tecnologías

- Python
- FastAPI
- HTML
- CSS
- JavaScript
- Docker

## Organización del código

La aplicación tiene un backend en FastAPI y un frontend sin frameworks.

### Backend en capas

```text
backend/
├── main.py                 Punto de entrada: crea la app, registra rutas y estáticos
├── core/config.py          Configuración: URLs, tiempos, caché y catálogo de bancos
├── api/routes/             Endpoints HTTP (POST /api/analyze, GET /api/bonds)
├── schemas/                Modelos Pydantic de entrada y salida de la API
├── services/               Casos de uso
│   ├── analysis_service.py       Filtra por riesgo, calcula y ordena opciones
│   ├── bond_service.py           Lista letras y bonos y calcula su ganancia
│   ├── recommendation_service.py Resumen informativo con Gemini o local
│   ├── fixed_deposit_sync.py     Sincroniza plazos fijos
│   ├── fund_sync.py              Sincroniza fondos comunes
│   ├── bond_sync.py              Sincroniza letras y bonos del Tesoro
│   └── sync_service.py           Ejecuta las sincronizaciones en paralelo
├── domain/                 Reglas puras: riesgo, rendimientos, tasas de plazo fijo, bancos, bonos
├── clients/                Consultas HTTP a ArgentinaDatos, CompararFondos y Gemini
├── db/                     Conexión, esquema y repositorios de PostgreSQL
└── tasks/scheduler.py      Sincronización programada cada hora
```

Cada capa solo usa las de abajo: `api` llama a `services`; `services` combina
`domain`, `clients` y `db`. `domain` no conoce la base de datos, HTTP ni
FastAPI, y solo los repositorios de `db/` escriben SQL. Los errores esperados
del análisis se lanzan como excepciones en `services/exceptions.py` y la ruta
los convierte en respuestas 503, 422 o 404.

Para ejecutarlo sin Docker, desde la carpeta raíz:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt
.venv/Scripts/python -m uvicorn backend.main:app --reload
```

### Frontend

Interfaz web sin frameworks ni paso de compilación.

```text
frontend/
├── index.html              Estructura de la página (encabezado, simulador, resultados, pie)
├── assets/icons/           Ícono de la pestaña del navegador
├── css/
│   ├── main.css            Punto de entrada: importa el resto en orden
│   ├── base/               Variables de diseño (tema claro/oscuro), reset y animaciones
│   ├── layout/             Contenedor, barra de navegación y pie de página
│   ├── components/         Piezas reutilizables: botones, tarjetas, formularios,
│   │                       pestañas, tooltip, mensajes y tarjetas de opciones
│   └── sections/           Estilos propios de cada sección de la página
└── js/
    ├── main.js             Punto de entrada: conecta los módulos
    ├── config.js           Bancos, enlaces oficiales y constantes
    ├── state.js            Último análisis recibido y banco/sección elegidos
    ├── services/api.js     Consultas a `/api/analyze` y `/api/bonds`
    ├── ui/                 Vistas: formulario, resultados, pestañas, panel del
    │                       banco, bonos, plantillas de tarjetas, tema y tooltip
    └── utils/              Formateo de números y escape de HTML
```

Cada archivo CSS incluye sus propias reglas para celulares, así los ajustes de
un componente quedan juntos. El JavaScript usa módulos nativos
(`<script type="module">`), por lo que la página debe abrirse desde el
servidor y no con doble clic sobre `index.html`. Para agregar un banco basta
con sumarlo a `BANKS` en `js/config.js`.

Los comentarios marcan límites entre responsabilidades. Cuando se agregue una
funcionalidad nueva, conviene colocarla en su bloque correspondiente y evitar
mezclar consultas, cálculos y presentación en la misma función.

## Fuentes de datos

- **Plazos fijos:** ArgentinaDatos (`/v1/finanzas/tasas/plazoFijo/`).
- **Fondos comunes de inversión:** CompararFondos (`/api/fondos`).
- **Billeteras virtuales:** Mercado Pago y Ualá. El dinero que se deja en la
	cuenta de estas billeteras rinde a través de fondos comunes que administran
	ellas mismas, por eso se obtienen de la misma fuente de fondos.
- **Bonos del Tesoro:** ArgentinaDatos, con precios de BYMA.
	- `/v1/finanzas/letras`: LECAP y BONCAP a tasa fija en pesos, con TNA y TEA.
	- `/v1/finanzas/bonos-cer`: bonos que ajustan por inflación, con su TIR real.

Cada fondo se asocia al banco o billetera dueño de su sociedad gerente (la
empresa que lo administra), según la lista `SOCIEDADES_GERENTES` de
`backend/core/config.py`. No se usa el banco depositario, porque un mismo banco
custodia fondos de muchas empresas distintas.

Para el plazo fijo se usa la tasa que el banco publica para el plazo elegido.
Si no publica una para ese plazo exacto, se usa la del plazo publicado más
cercano por debajo (la tasa general cuenta como la de 30 días) y la tarjeta
aclara qué tasa se tomó.

Los bonos se muestran en su propio apartado y no entran en el análisis por
riesgo. Para los de tasa fija, la ganancia supone comprarlos hoy al precio de
mercado y mantenerlos hasta el vencimiento: capital x ((1 + TEA) ^ (días / 365) - 1),
sin comisiones. Se descartan las letras sin una tasa positiva (por ejemplo los
duales) y las que vencen en más de un año, el mismo horizonte máximo del
simulador: a ese plazo la fuente incluye bonos que pagan cupones (como el
TY30P) y el cálculo de ganancia al vencimiento deja de ser válido. En los
CER solo se muestra la TIR real, porque la ganancia en pesos depende de la
inflación futura.

El backend guarda una copia local en PostgreSQL para que el análisis no dependa de
una consulta externa en cada solicitud. Las fuentes se sincronizan al iniciar la aplicación y luego cada hora.
Los análisis reutilizan la copia local y no consultan las APIs externas. Si
los datos tienen menos de una hora, la sincronización también se salta para
evitar llamadas repetidas. Si una fuente falla, se conserva la última
información válida almacenada.

Los FCI se clasifican por riesgo usando el tipo de fondo y el
horizonte publicados por la fuente: mercado de dinero y renta fija corta como
riesgo bajo; renta fija de mayor horizonte y fondos mixtos como moderado; renta
variable como alto. La variación del último día se muestra como dato histórico.
Cuando la fuente no publica una TNA, se muestra una TNA estimada anualizando el
rendimiento de los últimos 30 días; no representa una tasa garantizada.

## Configurar Gemini

El resumen informativo se genera con Gemini usando las opciones que primero
filtra y calcula el backend. Se le indica que solo describa los resultados y
que no recomiende ni aconseje invertir, porque eso sería asesoramiento
financiero. En la página, el resumen siempre va acompañado de un aviso
destacado que aclara que no es una recomendación de inversión ni garantiza
rendimientos. La clave nunca se escribe en el código.

Si alguna clave fue escrita en `docker-compose.yml` o publicada en Git, revocala
desde Google AI Studio y generá otra antes de continuar.

Para que otra persona pueda usar la aplicación:

```powershell
Copy-Item .env.example .env
```

Después deben abrir `.env` y pegar su clave después de `GEMINI_API_KEY=`:

```env
GEMINI_API_KEY=tu_clave_de_google_ai_studio
```

Con eso alcanza: la clave se toma del `.env` tanto con Docker
(`docker compose up --build`) como sin Docker (`uvicorn backend.main:app`).
Para ejecutar sin Docker también es obligatorio configurar `DATABASE_URL`.
El archivo `.env` está en `.gitignore`, así que cada integrante usa su propia
clave y nunca se sube a GitHub. En Render, la clave se carga en el panel del
servicio, en **Environment**, con el nombre `GEMINI_API_KEY`.

El modelo predeterminado es `gemini-3.5-flash-lite`, porque esta aplicación
solo necesita redactar un resumen breve. Si no se configura la clave,
la aplicación continúa funcionando con un resumen local.

Para comprobar que una solicitud llegó a Gemini, revisá los logs del contenedor:

```powershell
docker compose logs -f app
```

Después de enviar un análisis desde la web, debe aparecer una línea
`[GEMINI OK]` con el modelo utilizado y los metadatos de uso. Si Gemini falla,
aparecerá una línea `[GEMINI ERROR]`. Los logs nunca muestran la API key.

## Ejecutar con Docker

Desde la carpeta raíz:

```bash
docker compose up --build
```

Abrir http://localhost:8000. La documentación de la API está en
http://localhost:8000/docs. Para detener el servicio, usar `Ctrl+C`.

## Deploy en Render con Docker

El backend y el frontend se publican juntos como un único Web Service.
Render construye el Dockerfile; no ejecuta docker-compose.yml.

1. Subir los cambios de Dockerfile, .dockerignore y README.md a GitHub.
2. En Render, elegir **New > Web Service**, seleccionar **Git Provider**
   y conectar GitHub con acceso a este repositorio.
3. Seleccionar el repositorio y configurar:

   | Campo | Valor |
   | --- | --- |
   | Name | Un nombre disponible, por ejemplo `inversion-inteligente` |
   | Branch | `main` |
   | Language / Runtime | `Docker` |
   | Root Directory | Vacío (raíz del repositorio) |
   | Dockerfile Path | `./Dockerfile` |
   | Docker Build Context | `.` (si aparece el campo) |
   | Docker Command | Vacío; utilizar el CMD de la imagen |
   | Instance Type | `Free` para una demostración con las limitaciones indicadas abajo |
   | Health Check Path | `/` |
   | Auto-Deploy | `On Commit` |

4. Crear el servicio y revisar el build y los logs de ejecución.
5. Abrir la URL HTTPS asignada por Render y realizar las pruebas siguientes.

Render proporciona la variable `PORT`, que utiliza el comando del Dockerfile.
En Docker local, si no se define esa variable, se utiliza el puerto 8000.
`PYTHONUNBUFFERED=1` está definido en la imagen para mostrar los logs de Python
inmediatamente. Configurar `DATABASE_URL`, `APP_ENV=production` y
`AUTH_ALLOWED_ORIGINS` con el origen HTTPS público, sin rutas ni barra final.
`GEMINI_API_KEY` es opcional para el resumen con IA.
Mantener un único worker y una instancia para evitar duplicar el scheduler.

El health check en `/` comprueba que la web responde, pero no verifica la
disponibilidad de datos en PostgreSQL ni el éxito de las consultas externas.

### Caché y ejecución del job en el plan gratuito

PostgreSQL contiene catálogos de tasas, fondos y bonos, usuarios y sesiones; no almacena
los inputs del simulador. En Docker local, el servicio `db` conserva la información en el volumen
`postgres_data`. La aplicación reconstruye la caché consultando las fuentes si
la base todavía no tiene datos.

El servicio gratuito se suspende después de 15 minutos sin tráfico entrante.
Mientras está suspendido, el job no se ejecuta. Al volver a arrancar, se lanza
una sincronización inicial; las siguientes se ejecutan cada hora mientras
el proceso permanezca activo. Este plan no garantiza consultas horarias
continuas. Si ese requisito es obligatorio, utilizar una instancia siempre
activa de pago. Un disco persistente por sí solo no configura una conexión a
PostgreSQL; el servicio debe tener definida la variable `DATABASE_URL`.

### Verificar el deploy

- Abrir `/`, registrar una cuenta o iniciar sesión y comprobar el simulador.
- Desde el frontend autenticado ejecutar un análisis. Las llamadas POST manuales
  necesitan la cookie de sesión, `Origin` con el origen configurado y
  `X-Requested-With: fetch`, además del cuerpo JSON:

  ```json
  {"capital": 500000, "plazo": 30, "riesgo": "bajo"}
  ```

- Esperar una respuesta 200 con opciones y resumen después de cargar
  la caché. Un 503 inicial indica que todavía no hay datos utilizables.
- Revisar los logs de sincronización y los mensajes `[JOB ERROR]`.
  El mensaje "Sincronización completada" por sí solo no confirma que ambas
  fuentes hayan funcionado. Verificar que los resultados incluyan datos de
  ArgentinaDatos y CompararFondos usando un perfil de riesgo adecuado.
- Comprobar que el análisis funciona en solicitudes sucesivas: el endpoint
  lee los catálogos almacenados en PostgreSQL.
- Con el servicio activo durante una hora, comprobar una nueva ejecución
  del background job en los logs.
- Subir o mergear un cambio autorizado a `main` y comprobar el deploy
  automático del nuevo commit y la recuperación de la caché.
- Antes de presentar el TP, abrir la URL con anticipación y comprobar un
  análisis completo, ya que el arranque desde suspensión puede demorar.

La integración con GitHub permite build y deploy automático sin agregar
GitHub Actions. Estas instrucciones preparan el despliegue; la URL pública
y el resultado de las pruebas deben registrarse una vez realizado.

Documentación oficial: [Web Services](https://render.com/docs/web-services),
[Health Checks](https://render.com/docs/health-checks),
[Deploys](https://render.com/docs/deploys) y
[Free instances](https://render.com/docs/free).

## Registro y autenticación

La autenticación sigue `api/routes/auth.py → services/auth_service.py →
db/repositories/`. `core/security.py` usa Argon2id para contraseñas. El usuario
tiene un UUID estable para futuras relaciones; esta feature no guarda favoritos
ni cambia los cálculos de inversiones.

`schema.py` crea `users` y `user_sessions` al iniciar. Usuario y sesión se crean
en una transacción. La cookie HttpOnly contiene un token aleatorio; PostgreSQL
guarda solamente su SHA-256. Las sesiones duran siete días sin renovación
automática y se conservan ante reinicios. Cada solicitud verifica el vencimiento;
el scheduler elimina filas vencidas cada 24 horas. Logout invalida la sesión
actual; otros dispositivos mantienen sus propias sesiones.

| Método | Endpoint | Resultado |
| --- | --- | --- |
| POST | `/api/auth/register` | Email y contraseña; crea cuenta y sesión, devuelve 201. |
| POST | `/api/auth/login` | Email y contraseña; inicia sesión. |
| GET | `/api/auth/me` | UUID, email y fecha de creación; 401 sin sesión vigente. |
| POST | `/api/auth/logout` | Invalida sesión y borra cookie; 204 incluso sin sesión. |
| POST | `/api/analyze` | Requiere una sesión vigente. |
| GET | `/api/bonds` | Requiere una sesión vigente. Con `?capital=` calcula la ganancia de cada bono a tasa fija. |

La contraseña de registro debe tener entre 8 y 128 caracteres; los espacios
se conservan. El email se normaliza a minúsculas y es único. Un registro
duplicado devuelve 409, lo que permite saber que ese email ya está registrado.
El login devuelve el mismo error para email inexistente y contraseña incorrecta.
No se verifica propiedad del email y no hay recuperación de contraseña.

### Configuración local

Copiar `.env.example` a `.env`. Con Docker Compose, dejar `DATABASE_URL` vacío
para usar `db`, y ejecutar `docker compose up --build`. Para Uvicorn sin Docker,
configurar una URL PostgreSQL accesible, por ejemplo
`postgresql://inversion:inversion@localhost:5432/investments` si se dispone de esa
base local. Las credenciales de Compose son solo para desarrollo.

`APP_ENV=development` usa una cookie `session` sin Secure para HTTP local.
`AUTH_ALLOWED_ORIGINS` contiene orígenes completos separados por comas, por
defecto `http://localhost:8000,http://127.0.0.1:8000`. Ajustarlo si se cambia el
puerto. El frontend debe abrirse desde FastAPI, sin Live Server ni otro origen.

### Render y Supabase

Configurar en Environment, sin subir secretos al repositorio:

- `DATABASE_URL`: conexión PostgreSQL de Supabase con TLS, usando los parámetros
  y certificados indicados por el proveedor; no desactivar la validación TLS.
- `APP_ENV=production`: obligatorio en Render; no copiar el valor de desarrollo.
- `AUTH_ALLOWED_ORIGINS`: el origen HTTPS real, por ejemplo
  `https://inversion-inteligente-u4se.onrender.com`. Agregar el dominio propio
  separado por coma si se utiliza.

En producción la cookie es `__Host-session`, HttpOnly, Secure, SameSite=Lax,
Path=/ y sin Domain. No se requiere un secreto de JWT. El frontend nunca recibe
hashes de contraseñas ni tokens en JSON y no guarda credenciales en localStorage.
Los POST requieren Origin permitido y `X-Requested-With: fetch`; no habilitar
CORS entre orígenes sin revisar este mecanismo de protección CSRF.

La conexión del backend debe ser dueña de las tablas o tener permisos y acceso
RLS adecuados. El esquema activa RLS sin políticas públicas y revoca acceso a
PUBLIC y a los roles `anon` y `authenticated` cuando existen. Verificar en
Supabase que sus APIs públicas no puedan leer ni escribir estas tablas. No se
utiliza Supabase Auth. Mantener respaldos: los usuarios no son caché reconstruible.

El límite de intentos es por IP: 20 logins cada 15 minutos y 10 registros por
hora, incluyendo intentos exitosos. Es local a un proceso, acotado a 10.000
entradas y se reinicia con el servicio. Antes de escalar a varias instancias,
usar un límite compartido. Verificar que Uvicorn reciba la IP correcta detrás
del proxy de Render; configurar `FORWARDED_ALLOW_IPS` solo para proxies
confiables de la infraestructura. El código no confía manualmente en
`X-Forwarded-For`. Un proxy sin configurar puede hacer que varias personas
compartan el mismo límite.

### Pruebas

```powershell
.venv/Scripts/python -m unittest discover -s backend/tests -v
```

Las pruebas unitarias no conectan a la base del `.env`. Las pruebas PostgreSQL
solo corren si se define `TEST_DATABASE_URL` apuntando a una base exclusiva de
pruebas cuyo nombre contenga `test`; crean el esquema de la aplicación y
eliminan únicamente los usuarios generados por las pruebas. Nunca usar la URL
de producción. Para pruebas de navegador opcionales, instalar Playwright en el
entorno de desarrollo y seguir las instrucciones de `test_auth_browser.py`.
