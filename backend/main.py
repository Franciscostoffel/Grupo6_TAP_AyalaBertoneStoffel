"""API principal de Inversion Inteligente.

El archivo esta organizado por responsabilidad: configuracion, persistencia,
fuentes externas, dominio, ciclo de vida, API y archivos estaticos.
"""

import asyncio
import re
import sqlite3
import unicodedata
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ============================================================================
# CONFIGURACION Y CATALOGOS
# ============================================================================

# URLs de las fuentes que alimentan la aplicacion.
FIXED_DEPOSIT_API_URL = (
    "https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo/"
)
FUNDS_API_URL = "https://compararfondos.com.ar/api/fondos"
DB_PATH = "investments.db"

BANCOS_SELECCIONADOS = {
    "NACION": "Banco Nación",
    "PROVINCIA DE BUENOS AIRES": "Banco Provincia",
    "GALICIA": "Banco Galicia",
    "BBVA": "BBVA",
    "SANTANDER": "Banco Santander",
    "INDUSTRIAL AND COMMERCIAL BANK OF CHINA": "ICBC",
    "MACRO": "Banco Macro",
    "CIUDAD": "Banco Ciudad",
    "CREDICOOP": "Banco Credicoop",
    "BANCO DE LA CIUDAD DE BUENOS AIRES": "Banco Ciudad",
    "PATAGONIA": "Banco Patagonia",
    "SUPERVIELLE": "Banco Supervielle",
    "HIPOTECARIO": "Banco Hipotecario",
    "COMAFI": "Banco Comafi",
    "BICA": "Banco Bica",
    "CMF": "Banco CMF",
}

FUND_BANK_ALIASES = {
    "ICBC": "ICBC",
    "BANCO NACION": "Banco Nación",
    "BANCO GALICIA": "Banco Galicia",
    "BANCO SANTANDER": "Banco Santander",
    "BBVA": "BBVA",
}


# ============================================================================
# PERSISTENCIA LOCAL (SQLITE)
# ============================================================================

def init_db():
    """Create the local cache used by the API and migrate older columns."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            nombre TEXT PRIMARY KEY,
            tipo TEXT,
            tna REAL,
            garantizado INTEGER NOT NULL DEFAULT 1,
            fuente TEXT NOT NULL DEFAULT 'ArgentinaDatos',
            fecha_datos TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fixed_deposit_terms (
            banco TEXT NOT NULL,
            plazo_min_dias INTEGER NOT NULL,
            plazo_max_dias INTEGER NOT NULL,
            tna REAL NOT NULL,
            fecha_datos TEXT,
            PRIMARY KEY (banco, plazo_min_dias, plazo_max_dias)
        )
    """)
    cursor.execute("PRAGMA table_info(rates)")
    rate_columns = {row[1] for row in cursor.fetchall()}
    for column, definition in (
        ("garantizado", "INTEGER NOT NULL DEFAULT 1"),
        ("fuente", "TEXT NOT NULL DEFAULT 'ArgentinaDatos'"),
        ("fecha_datos", "TEXT"),
    ):
        if column not in rate_columns:
            cursor.execute(f"ALTER TABLE rates ADD COLUMN {column} {definition}")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fci_funds (
            nombre TEXT PRIMARY KEY,
            banco TEXT,
            tipo TEXT NOT NULL,
            horizonte TEXT,
            tna_estimada REAL,
            rendimiento_1d REAL,
            rendimiento_30d REAL,
            vcp REAL,
            fecha_datos TEXT,
            fecha_vcp TEXT,
            depositaria TEXT,
            gerente TEXT,
            gestora TEXT,
            minimo REAL,
            plazo_liq INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("PRAGMA table_info(fci_funds)")
    fci_columns = {row[1] for row in cursor.fetchall()}
    if "banco" not in fci_columns:
        cursor.execute("ALTER TABLE fci_funds ADD COLUMN banco TEXT")
    for column, definition in (
        ("rendimiento_30d", "REAL"),
        ("rendimiento_1d", "REAL"),
        ("fecha_vcp", "TEXT"),
        ("depositaria", "TEXT"),
        ("gerente", "TEXT"),
        ("gestora", "TEXT"),
        ("minimo", "REAL"),
        ("plazo_liq", "INTEGER"),
    ):
        if column not in fci_columns:
            cursor.execute(f"ALTER TABLE fci_funds ADD COLUMN {column} {definition}")
    conn.commit()
    conn.close()

def save_rate_to_db(
    nombre: str,
    tipo: str,
    tna: float,
    fecha_datos: str | None = None,
):
    """Persist one bank's general fixed-deposit rate."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rates (
            nombre, tipo, tna, garantizado, fuente, fecha_datos, updated_at
        )
        VALUES (?, ?, ?, 1, 'ArgentinaDatos', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(nombre) DO UPDATE SET
            tipo = excluded.tipo,
            tna = excluded.tna,
            fecha_datos = excluded.fecha_datos,
            updated_at = CURRENT_TIMESTAMP
    """, (nombre, tipo, tna, fecha_datos))
    conn.commit()
    conn.close()

def save_fci_to_db(
    nombre: str,
    banco: str | None,
    tipo: str,
    horizonte: str | None,
    tna_estimada: float | None,
    rendimiento_1d: float | None,
    rendimiento_30d: float | None,
    vcp: float | None,
    fecha_datos: str | None,
    fecha_vcp: str | None,
    depositaria: str | None,
    gerente: str | None,
    gestora: str | None,
    minimo: float | None,
    plazo_liq: int | None,
):
    """Persist one normalized fund, using one row per base fund name."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO fci_funds (
            nombre, banco, tipo, horizonte, tna_estimada, rendimiento_1d,
            rendimiento_30d, vcp,
            fecha_datos, fecha_vcp, depositaria, gerente, gestora, minimo,
            plazo_liq, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(nombre) DO UPDATE SET
            banco = excluded.banco,
            tipo = excluded.tipo,
            horizonte = excluded.horizonte,
            tna_estimada = excluded.tna_estimada,
            rendimiento_1d = excluded.rendimiento_1d,
            rendimiento_30d = excluded.rendimiento_30d,
            vcp = excluded.vcp,
            fecha_datos = excluded.fecha_datos,
            fecha_vcp = excluded.fecha_vcp,
            depositaria = excluded.depositaria,
            gerente = excluded.gerente,
            gestora = excluded.gestora,
            minimo = excluded.minimo,
            plazo_liq = excluded.plazo_liq,
            updated_at = CURRENT_TIMESTAMP
    """, (
        nombre, banco, tipo, horizonte, tna_estimada, rendimiento_1d,
        rendimiento_30d, vcp,
        fecha_datos, fecha_vcp, depositaria, gerente, gestora, minimo, plazo_liq
    ))
    conn.commit()
    conn.close()

def clear_fci_data():
    """Replace the cached FCI catalog only after a successful API response."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM fci_funds")
    conn.commit()
    conn.close()

def clear_plazo_fijo_data():
    """Replace all fixed-deposit data during the next successful sync."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM rates WHERE tipo = 'Plazo Fijo'")
    conn.execute("DELETE FROM fixed_deposit_terms")
    conn.commit()
    conn.close()

def save_fixed_deposit_term(
    banco: str, plazo_min: int, plazo_max: int, tna: float
):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO fixed_deposit_terms
            (banco, plazo_min_dias, plazo_max_dias, tna, fecha_datos)
        VALUES (?, ?, ?, ?, CURRENT_DATE)
        ON CONFLICT(banco, plazo_min_dias, plazo_max_dias) DO UPDATE SET
            tna = excluded.tna,
            fecha_datos = excluded.fecha_datos
    """, (banco, plazo_min, plazo_max, tna))
    conn.commit()
    conn.close()

def get_investment_data() -> tuple[list[dict], list[dict], list[dict]]:
    """Read cached rates, official terms, and normalized funds for analysis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nombre, tipo, tna, garantizado, fuente, fecha_datos
        FROM rates
        WHERE tna > 0
    """)
    rates = [
        {
            "nombre": row[0],
            "banco": row[0] if row[1] == "Plazo Fijo" else None,
            "tipo": row[1],
            "tna": row[2],
            "garantizado": bool(row[3]),
            "fuente": row[4],
            "fecha_datos": row[5],
        }
        for row in cursor.fetchall()
    ]
    cursor.execute("""
        SELECT banco, plazo_min_dias, plazo_max_dias, tna, fecha_datos
        FROM fixed_deposit_terms
        ORDER BY banco, plazo_min_dias
    """)
    fixed_terms = [
        {
            "banco": row[0],
            "plazo_min": row[1],
            "plazo_max": row[2],
            "tna": row[3],
            "fecha_datos": row[4],
        }
        for row in cursor.fetchall()
    ]
    cursor.execute("""
        SELECT nombre, banco, tipo, horizonte, tna_estimada, rendimiento_1d,
               rendimiento_30d, vcp,
               fecha_datos, fecha_vcp, depositaria, gerente, gestora, minimo,
               plazo_liq
        FROM fci_funds
        WHERE rendimiento_30d IS NOT NULL
        ORDER BY rendimiento_30d DESC
    """)
    funds = [
        {
            "nombre": row[0],
            "banco": row[1],
            "tipo": row[2],
            "horizonte": row[3],
            "tna": row[4],
            "rendimiento_1d": row[5],
            "rendimiento_30d": row[6],
            "vcp": row[7],
            "fecha_datos": row[8],
            "fecha_vcp": row[9],
            "depositaria": row[10],
            "gerente": row[11],
            "gestora": row[12],
            "minimo": row[13],
            "plazo_liq": row[14],
            "garantizado": False,
            "fuente": "CompararFondos / CAFCI",
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return rates, fixed_terms, funds

# ============================================================================
# SINCRONIZACION CON FUENTES EXTERNAS
# ============================================================================

async def sync_fixed_deposits(client: httpx.AsyncClient):
    """Sync official bank rates and terms from ArgentinaDatos."""
    url = FIXED_DEPOSIT_API_URL
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        if resp.status_code == 200:
            clear_plazo_fijo_data()
            for item in resp.json():
                entidad = str(item.get("entidad", "")).strip()
                entidad_mayuscula = entidad.upper()
                nombre = next(
                    (
                        nombre_banco
                        for clave, nombre_banco in BANCOS_SELECCIONADOS.items()
                        if clave in entidad_mayuscula
                    ),
                    None,
                )
                raw_tna = float(
                    item.get("tnaClientes", 0) or item.get("tnaNoClientes", 0)
                )
                tna = raw_tna * 100 if 0 < raw_tna < 1 else raw_tna
                if nombre and tna > 0:
                    save_rate_to_db(nombre, "Plazo Fijo", round(tna, 2))
                    for term in item.get("tasas", []):
                        plazo_min = term.get("plazoMinDias")
                        plazo_max = term.get("plazoMaxDias")
                        raw_term_tna = term.get("tna")
                        if plazo_min and plazo_max and raw_term_tna:
                            term_tna = (
                                float(raw_term_tna) * 100
                                if 0 < float(raw_term_tna) < 1
                                else float(raw_term_tna)
                            )
                            save_fixed_deposit_term(
                                nombre, int(plazo_min), int(plazo_max),
                                round(term_tna, 2)
                            )
    except Exception as e:
        print(f"[JOB ERROR] Plazos Fijos: {e}")

async def sync_fci(client: httpx.AsyncClient):
    """Sync and normalize FCI data from CompararFondos/CAFCI."""
    url = FUNDS_API_URL
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        fondos = resp.json().get("funds", [])
        clear_fci_data()
        fondos_por_nombre: dict[str, dict] = {}
        for item in fondos:
            nombre = str(item.get("nombre") or "").strip()
            nombre_base = str(item.get("nombreBase") or nombre).strip()
            rendimiento_30d = item.get("r30")
            if not nombre or rendimiento_30d is None:
                continue

            actual = fondos_por_nombre.get(nombre_base)
            es_clase_a = bool(re.search(r"\bCLASE\s+A\b", nombre.upper()))
            actual_es_clase_a = bool(
                actual and re.search(
                    r"\bCLASE\s+A\b", str(actual.get("nombre", "")).upper()
                )
            )
            if actual is None or (es_clase_a and not actual_es_clase_a):
                fondos_por_nombre[nombre_base] = item

        for item in fondos_por_nombre.values():
            banco = bank_for_fund(item)
            rendimiento_30d = item.get("r30")
            nombre_base = str(
                item.get("nombreBase") or item.get("nombre")
            ).strip()
            save_fci_to_db(
                nombre=nombre_base,
                banco=banco,
                tipo=f"FCI {item.get('tipo') or 'Otros'}",
                horizonte=item.get("horizonte"),
                tna_estimada=(
                    float(item["tna"])
                    if item.get("tna") is not None and float(item["tna"]) > 0
                    else annualized_return_from_30d(float(rendimiento_30d))
                ),
                rendimiento_1d=(
                    float(item["variacionDia"])
                    if item.get("variacionDia") is not None
                    else None
                ),
                rendimiento_30d=float(rendimiento_30d),
                vcp=item.get("vcpHoy"),
                fecha_datos=item.get("fechaVcp"),
                fecha_vcp=item.get("fechaVcp"),
                depositaria=item.get("depositaria"),
                gerente=item.get("gerente"),
                gestora=item.get("gestora"),
                minimo=item.get("minimo"),
                plazo_liq=item.get("plazoLiq"),
            )
    except Exception as e:
        print(f"[JOB ERROR] FCI: {e}")


# ============================================================================
# REGLAS DE NEGOCIO Y NORMALIZACION
# ============================================================================

def bank_for_fund(item: dict) -> str | None:
    text = unicodedata.normalize(
        "NFKD",
        " ".join(
            str(item.get(field, "")) for field in
            ("nombre", "administradora", "depositaria")
        )
    ).encode("ascii", "ignore").decode().upper()
    text += " " + " ".join(
        str(item.get(field, "")) for field in ("gerente", "gestora")
    ).upper()
    for key, bank in {**BANCOS_SELECCIONADOS, **FUND_BANK_ALIASES}.items():
        normalized_key = unicodedata.normalize(
            "NFKD", key
        ).encode("ascii", "ignore").decode().upper()
        if normalized_key in text:
            return bank
    return None

def annualized_return_from_30d(rendimiento_30d: float | None) -> float | None:
    if rendimiento_30d is None or rendimiento_30d <= -100:
        return None
    return ((1 + rendimiento_30d / 100) ** 12 - 1) * 100

def fund_risk(tipo: str, horizonte: str | None) -> str:
    """Classifies funds from the published asset type and investment horizon."""
    tipo = tipo.upper()
    horizonte = (horizonte or "").lower()
    if tipo == "MM" or (tipo == "RFP" and horizonte == "corto"):
        return "bajo"
    if tipo in {"RFP", "MIX", "MULTI", "USD"}:
        return "moderado"
    return "alto"

def risk_matches(selected: str, category: str) -> bool:
    levels = {"bajo": 0, "moderado": 1, "alto": 2}
    return levels.get(category, 2) <= levels.get(selected, 0)

async def background_sync_all():
    """Refresh both data sources concurrently and keep the previous cache on errors."""
    print("[BACKGROUND JOB] Sincronizando plazos fijos y fondos...")
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        resultados = await asyncio.gather(
            sync_fixed_deposits(client),
            sync_fci(client),
            return_exceptions=True
        )
        for resultado in resultados:
            if isinstance(resultado, Exception):
                print(f"[JOB ERROR] Sincronización: {resultado}")
    print("[BACKGROUND JOB] Sincronización completada.")

# ============================================================================
# TAREAS PROGRAMADAS Y CICLO DE VIDA
# ============================================================================

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the cache and schedule hourly source refreshes."""
    init_db()
    asyncio.create_task(background_sync_all())
    scheduler.add_job(background_sync_all, "interval", hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(
    title="Inversión Inteligente",
    description="Comparador Concurrente con SQLite, APIs y Money Market",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# MODELOS DE LA API Y ENDPOINTS
# ============================================================================

class InvestmentRequest(BaseModel):
    capital: float = Field(gt=0)
    plazo: int = Field(gt=0)
    riesgo: str

class EntityResult(BaseModel):
    nombre: str
    banco: str | None
    tipo: str
    categoria: str
    instrumento: str    # "Renta Fija (Plazo Fijo)" o "FCI Money Market"
    horizonte: str      # "Corto / Inmediato" o "Medio (>= 30 días)"
    perfil_riesgo: str
    tna: float | None
    rendimiento_ultimo_dia_pct: float | None
    rendimiento_periodo_pct: float | None
    garantizado: bool
    fuente: str
    fecha_datos: str | None
    rendimiento: float
    monto_final: float
    liquidez: str
    acceso_app: str | None

class InvestmentResponse(BaseModel):
    capital: float
    plazo: int
    riesgo: str
    opciones: list[EntityResult]
    recomendacion: str
    plazos_fijos: list[dict]

@app.post("/api/analyze", response_model=InvestmentResponse)
async def analyze_investment(data: InvestmentRequest):
    """Build recommendations from the two cached product catalogs."""
    rates, fixed_terms, funds = get_investment_data()
    rates = [rate for rate in rates if rate["tipo"] == "Plazo Fijo"]
    selected_terms = fixed_terms

    if not rates and not funds:
        raise HTTPException(
            status_code=503,
            detail="La base de datos se está sincronizando. Reintente en unos segundos."
        )

    riesgo = data.riesgo.strip().lower()
    if riesgo not in {"bajo", "moderado", "alto"}:
        raise HTTPException(status_code=422, detail="Nivel de riesgo inválido.")
    opciones: list[EntityResult] = []

    for item in rates + funds:
        es_fci = item["tipo"].startswith("FCI")
        perfil_riesgo = (
            fund_risk(item["tipo"].replace("FCI ", ""), item.get("horizonte"))
            if es_fci
            else "bajo"
        )
        if not risk_matches(riesgo, perfil_riesgo):
            continue
        tna = item["tna"]

        if es_fci:
            rendimiento_30d = item.get("rendimiento_30d")
            if rendimiento_30d is not None:
                rendimiento_periodo_pct = (
                    (1 + rendimiento_30d / 100) ** (data.plazo / 30) - 1
                ) * 100
                ganancia = data.capital * rendimiento_periodo_pct / 100
            else:
                rendimiento_periodo_pct = tna * data.plazo / 365
                ganancia = data.capital * rendimiento_periodo_pct / 100
            monto_final = data.capital + ganancia
            plazo_liq = item.get("plazo_liq")
            liquidez = (
                f"Rescate informado: {plazo_liq} día(s)"
                if plazo_liq is not None
                else "Según plazo de rescate del fondo"
            )
            instrumento = "Fondo Común de Inversión"
            horizonte = item["horizonte"] or "No informado"
            tipo_fci = item["tipo"].lower()
            if "mercado de dinero" in tipo_fci or "plazo fijo" in tipo_fci:
                categoria = "money_market"
            else:
                categoria = "fondos"
        else:
            ganancia = data.capital * (tna / 100) * (data.plazo / 365)
            monto_final = data.capital + ganancia
            liquidez = f"Al vencimiento ({data.plazo} días)"
            instrumento = "Renta Fija Tradicional"
            horizonte = f"Referencia para {data.plazo} días"
            categoria = "plazo_fijo"
            rendimiento_periodo_pct = tna * data.plazo / 365
        rendimiento_ultimo_dia_pct = (
            item.get("rendimiento_1d") if es_fci else None
        )

        opciones.append(
            EntityResult(
                nombre=item["nombre"],
                banco=item.get("banco"),
                tipo=item["tipo"],
                categoria=categoria,
                instrumento=instrumento,
                horizonte=horizonte,
                perfil_riesgo=perfil_riesgo,
                tna=tna,
                rendimiento_ultimo_dia_pct=rendimiento_ultimo_dia_pct,
                rendimiento_periodo_pct=round(rendimiento_periodo_pct, 4),
                garantizado=item["garantizado"],
                fuente=item["fuente"],
                fecha_datos=item["fecha_datos"],
                rendimiento=round(ganancia, 2),
                monto_final=round(monto_final, 2),
                liquidez=liquidez,
                acceso_app=(
                    "Asociado al banco; confirmá en la app si está habilitado "
                    "para tu cuenta."
                    if es_fci and item.get("banco")
                    else None
                )
            )
        )

    if not opciones:
        raise HTTPException(
            status_code=404,
            detail="No encontramos opciones compatibles con ese nivel de riesgo."
        )

    opciones.sort(key=lambda x: x.rendimiento, reverse=True)
    mejor = opciones[0]

    tna_referencia = (
        f"{mejor.tna:.2f}% TNA de referencia"
        if mejor.tna is not None
        else "TNA no disponible"
    )
    recomendacion = (
        f"Para un plazo de {data.plazo} días y perfil '{data.riesgo}': "
        f"La mejor opción estimada es {mejor.nombre} ({mejor.instrumento}) con "
        f"{tna_referencia} y una ganancia estimada de "
        f"${mejor.rendimiento:,.2f}. Los FCI no garantizan rendimientos; "
        f"sus tasas provienen de resultados históricos publicados."
    )

    return InvestmentResponse(
        capital=data.capital,
        plazo=data.plazo,
        riesgo=data.riesgo,
        opciones=opciones,
        recomendacion=recomendacion,
        plazos_fijos=selected_terms,
    )

# ============================================================================
# ARCHIVOS ESTATICOS DEL FRONTEND
# ============================================================================

frontend_path = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")