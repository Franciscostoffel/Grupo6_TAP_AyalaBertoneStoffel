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
├── api/routes/             Endpoints HTTP (POST /api/analyze)
├── schemas/                Modelos Pydantic de entrada y salida de la API
├── services/               Casos de uso
│   ├── analysis_service.py       Filtra por riesgo, calcula y ordena opciones
│   ├── recommendation_service.py Recomendación con Gemini o local
│   ├── fixed_deposit_sync.py     Sincroniza plazos fijos
│   ├── fund_sync.py              Sincroniza fondos comunes
│   └── sync_service.py           Ejecuta ambas sincronizaciones en paralelo
├── domain/                 Reglas puras: riesgo, rendimientos, tasas de plazo fijo, bancos
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
    ├── services/api.js     Consulta a `/api/analyze`
    ├── ui/                 Vistas: formulario, resultados, pestañas, panel del
    │                       banco, plantillas de tarjetas, tema y tooltip
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

Cada fondo se asocia al banco o billetera dueño de su sociedad gerente (la
empresa que lo administra), según la lista `SOCIEDADES_GERENTES` de
`backend/core/config.py`. No se usa el banco depositario, porque un mismo banco
custodia fondos de muchas empresas distintas.

Para el plazo fijo se usa la tasa que el banco publica para el plazo elegido.
Si no publica una para ese plazo exacto, se usa la del plazo publicado más
cercano por debajo (la tasa general cuenta como la de 30 días) y la tarjeta
aclara qué tasa se tomó.

El backend guarda una copia local en PostgreSQL para que el análisis no dependa de
una consulta externa en cada solicitud. Las dos fuentes se sincronizan al iniciar la aplicación y luego cada hora.
Los análisis reutilizan la copia local y no consultan las APIs externas. Si
los datos tienen menos de una hora, la sincronización también se salta para
evitar llamadas repetidas. Si una fuente falla, se conserva la última
información válida almacenada.

Los FCI se clasifican para la recomendación usando el tipo de fondo y el
horizonte publicados por la fuente: mercado de dinero y renta fija corta como
riesgo bajo; renta fija de mayor horizonte y fondos mixtos como moderado; renta
variable como alto. La variación del último día se muestra como dato histórico.
Cuando la fuente no publica una TNA, se muestra una TNA estimada anualizando el
rendimiento de los últimos 30 días; no representa una tasa garantizada.

## Configurar Gemini

La recomendación textual se genera con Gemini usando las opciones que primero
filtra y calcula el backend. La clave nunca se escribe en el código.

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
El archivo `.env` está en `.gitignore`, así que cada integrante usa su propia
clave y nunca se sube a GitHub. En Render, la clave se carga en el panel del
servicio, en **Environment**, con el nombre `GEMINI_API_KEY`.

El modelo predeterminado es `gemini-3.5-flash-lite`, porque esta aplicación
solo necesita redactar una recomendación breve. Si no se configura la clave,
la aplicación continúa funcionando con una recomendación local.

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
inmediatamente. La aplicación actual no requiere API keys ni otras variables.
Mantener un único worker y una instancia para evitar duplicar el scheduler.

El health check en `/` comprueba que la web responde, pero no verifica la
disponibilidad de datos en PostgreSQL ni el éxito de las consultas externas.

### Caché y ejecución del job en el plan gratuito

PostgreSQL contiene catálogos de tasas y fondos; no almacena los inputs del
usuario. En Docker local, el servicio `db` conserva la información en el volumen
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

- Abrir `/` y comprobar que se muestran el formulario, estilos y resultados.
- Abrir `/docs` y ejecutar `POST /api/analyze` con este cuerpo:

  ```json
  {"capital": 500000, "plazo": 30, "riesgo": "bajo"}
  ```

- Esperar una respuesta 200 con opciones y recomendación después de cargar
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
