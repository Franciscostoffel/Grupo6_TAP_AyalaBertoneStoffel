# Grupo6_TAP_AyalaBertoneStoffel

# Inversión Inteligente

Sistema web para comparar diferentes opciones de inversión
según el capital disponible, plazo y nivel de riesgo aceptable.

## Tecnologías

- Python
- FastAPI
- HTML
- CSS
- JavaScript
- Docker

## Organización del código

La aplicación está separada en dos capas simples:

- `backend/main.py`: API FastAPI y reglas de negocio. Dentro del archivo, los
	bloques siguen este orden: configuración y catálogos, persistencia SQLite,
	sincronización con APIs externas, normalización y reglas de riesgo, tareas
	programadas, ciclo de vida, modelos/endpoints y archivos estáticos.
- `frontend/index.html`: estructura semántica de la pantalla, agrupada en
	formulario, estados de carga, resultados y errores.
- `frontend/js/app.js`: comportamiento de la interfaz. El estado se declara al
	principio; luego aparecen navegación, consulta al backend, renderizado,
	formateo y manejo de errores.
- `frontend/css/styles.css`: estilos agrupados por base, formulario, controles,
	resultados, tarjetas, estados y responsive.

Los comentarios marcan límites entre responsabilidades. Cuando se agregue una
funcionalidad nueva, conviene colocarla en su bloque correspondiente y evitar
mezclar consultas, cálculos y presentación en la misma función.

## Fuentes de datos

- **Plazos fijos:** ArgentinaDatos (`/v1/finanzas/tasas/plazoFijo/`).
- **Fondos comunes de inversión:** CompararFondos (`/api/fondos`).

El backend guarda una copia local en SQLite para que el análisis no dependa de
una consulta externa en cada solicitud. Las dos fuentes se sincronizan al
iniciar la aplicación y luego cada hora. Si una fuente falla, se conserva la
última información válida almacenada.

Los FCI se clasifican para la recomendación usando el tipo de fondo y el
horizonte publicados por la fuente: mercado de dinero y renta fija corta como
riesgo bajo; renta fija de mayor horizonte y fondos mixtos como moderado; renta
variable como alto. La variación del último día se muestra como dato histórico.
Cuando la fuente no publica una TNA, se muestra una TNA estimada anualizando el
rendimiento de los últimos 30 días; no representa una tasa garantizada.

## Ejecutar con Docker

Desde la carpeta raíz:

```bash
docker compose up --build