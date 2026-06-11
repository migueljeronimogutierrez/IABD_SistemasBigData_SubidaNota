# =============================================================================
# etl_musica.py
# =============================================================================
# Script ETL - Analisis de Tendencias Musicales Historicas
# Modulo 5074 - Sistemas de Big Data
# Alumno: Miguel Jeronimo Gutierrez
# =============================================================================

import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import create_engine, text
import os
import warnings
warnings.filterwarnings("ignore")

fake = Faker("es_ES")
np.random.seed(42)

# =============================================================================
# CONFIGURACION DE CONEXION A POSTGRESQL (pg8000)
# =============================================================================
DB_HOST     = "localhost"
DB_PORT     = "5455"
DB_NAME     = "musicdb"
DB_USER     = "sbguser"
DB_PASSWORD = "sbgpass123"

# pg8000: driver PostgreSQL puro Python, sin dependencias del sistema
# Necesario en Windows con locale en espanol por bug de codificacion en psycopg
CONNECTION_STRING = (
    f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def crear_engine():
    return create_engine(CONNECTION_STRING)

# =============================================================================
# PARAMETROS DEL DATASET
# =============================================================================
N_REGISTROS = 50000

GENEROS_CORRECTOS = ["Rock", "Soul", "R&B", "Blues", "Salsa"]

GENEROS_SUCIOS = {
    "Rock":  ["Rock", "rock", "ROCK", "Rok", "Rock "],
    "Soul":  ["Soul", "soul", "SOUL", "Sowl", "Soul "],
    "R&B":   ["R&B", "r&b", "R & B", "RnB", "R&b"],
    "Blues": ["Blues", "blues", "BLUES", "Bluess", "Blue"],
    "Salsa": ["Salsa", "salsa", "SALSA", "Zalsa", "Sals"],
}

SUBGENEROS = {
    "Rock":  ["Hard Rock", "Soft Rock", "Progressive Rock", "Psychedelic Rock", "Folk Rock"],
    "Soul":  ["Classic Soul", "Deep Soul", "Southern Soul", "Funk Soul", "Neo Soul"],
    "R&B":   ["Rhythm and Blues", "Contemporary RnB", "New Jack Swing", "Doo-Wop", "Gospel RnB"],
    "Blues": ["Delta Blues", "Chicago Blues", "Electric Blues", "Piedmont Blues", "Jump Blues"],
    "Salsa": ["Salsa Romantica", "Salsa Dura", "Salsa Choke", "Timba", "Salsa Brava"],
}

GEOGRAFIA = {
    "Rock":  [("USA", "Northeast"), ("UK", "London"), ("USA", "West Coast"),
              ("Germany", "Bavaria"), ("Australia", "New South Wales")],
    "Soul":  [("USA", "Southeast"), ("USA", "Midwest"), ("UK", "London"),
              ("Canada", "Ontario"), ("USA", "Northeast")],
    "R&B":   [("USA", "Southeast"), ("USA", "Midwest"), ("USA", "Northeast"),
              ("UK", "London"), ("Canada", "Quebec")],
    "Blues": [("USA", "Southeast"), ("USA", "Midwest"), ("USA", "Mississippi Delta"),
              ("UK", "London"), ("USA", "Chicago")],
    "Salsa": [("Colombia", "Costa Caribe"), ("Puerto Rico", "San Juan"),
              ("Cuba", "La Habana"), ("USA", "New York"), ("Venezuela", "Caracas"),
              ("Panama", "Ciudad de Panama"), ("Spain", "Cataluna")],
}

GRUPOS_EDAD = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
FORMATOS    = ["LP", "Single", "EP", "Cassette", "8-Track"]

DECADAS_ANIOS = {
    "60s": list(range(1960, 1970)),
    "70s": list(range(1970, 1980)),
    "80s": list(range(1980, 1990)),
}

print("=" * 65)
print("  ETL -- Analisis de Tendencias Musicales Historicas")
print("  Modulo 5074 - Sistemas de Big Data")
print("=" * 65)

# =============================================================================
# BLOQUE 1: GENERACION DEL DATASET SIMULADO
# =============================================================================
print("\n[1/7] Generando dataset simulado...")

registros = []

for i in range(N_REGISTROS):
    genero_base = np.random.choice(
        GENEROS_CORRECTOS,
        p=[0.28, 0.22, 0.20, 0.18, 0.12]
    )

    if np.random.random() < 0.20:
        genero_display = np.random.choice(GENEROS_SUCIOS[genero_base])
    else:
        genero_display = genero_base

    subgenero = np.random.choice(SUBGENEROS[genero_base])
    geo       = GEOGRAFIA[genero_base][np.random.randint(len(GEOGRAFIA[genero_base]))]
    pais      = geo[0]
    region    = geo[1]

    decada = np.random.choice(["60s", "70s", "80s"], p=[0.25, 0.50, 0.25])
    anio   = np.random.choice(DECADAS_ANIOS[decada])

    if np.random.random() < 0.15:
        fecha_str = f"{np.random.randint(1,13):02d}/{anio}"
    else:
        fecha_str = str(anio)

    grupo_edad = np.random.choice(GRUPOS_EDAD)
    formato    = np.random.choice(FORMATOS, p=[0.55, 0.20, 0.10, 0.10, 0.05])

    ventas                = int(np.random.lognormal(mean=8.5, sigma=1.2))
    streams               = int(np.random.lognormal(mean=10.0, sigma=1.5))
    compradores_unicos    = int(ventas * np.random.uniform(0.6, 0.95))
    compradores_repetidos = int(compradores_unicos * np.random.uniform(0.1, 0.6))
    tasa_retencion        = round(compradores_repetidos / max(compradores_unicos, 1), 4)
    ingresos              = round(ventas * np.random.uniform(5.0, 25.0), 2)

    if np.random.random() < 0.08:
        streams = None
    if np.random.random() < 0.05:
        grupo_edad = None
    if np.random.random() < 0.03:
        region = None

    n_veces = 2 if np.random.random() < 0.02 else 1

    for _ in range(n_veces):
        registros.append({
            "album":               fake.catch_phrase()[:60],
            "artist":              fake.name()[:50],
            "genre":               genero_display,
            "subgenre":            subgenero,
            "year_raw":            fecha_str,
            "decade":              decada,
            "country":             pais,
            "region":              region,
            "age_group":           grupo_edad,
            "sales_units":         ventas,
            "streams":             streams,
            "unique_buyers":       compradores_unicos,
            "repeat_buyers":       compradores_repetidos,
            "retention_rate":      tasa_retencion,
            "revenue":             ingresos,
            "format":              formato,
        })

df_raw = pd.DataFrame(registros)
df_raw.reset_index(drop=True, inplace=True)
df_raw["id"] = df_raw.index + 1

print(f"    Registros generados (con duplicados): {len(df_raw):,}")
print(f"    Columnas: {list(df_raw.columns)}")

os.makedirs("data/raw",       exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
df_raw.to_csv("data/raw/musica_raw.csv", index=False, encoding="utf-8")
print(f"    Guardado en data/raw/musica_raw.csv")

# =============================================================================
# BLOQUE 2: DIAGNOSTICO ANTES DE LIMPIAR
# =============================================================================
print("\n[2/7] Diagnostico del dataset RAW (antes de limpiar)...")

print(f"\n    Filas totales:    {len(df_raw):,}")
print(f"    Duplicados:       {df_raw.duplicated(subset=['album','artist','genre','year_raw']).sum():,}")
print(f"\n    Nulos por columna:")
nulos_antes = df_raw.isnull().sum()
for col, val in nulos_antes[nulos_antes > 0].items():
    print(f"      {col:<20} {val:,} nulos ({val/len(df_raw)*100:.1f}%)")

print(f"\n    Variantes de genero encontradas:")
for g in sorted(df_raw["genre"].unique()):
    print(f"      '{g}'")

# =============================================================================
# BLOQUE 3: LIMPIEZA Y ESTANDARIZACION
# =============================================================================
print("\n[3/7] Aplicando limpieza y estandarizacion...")

df = df_raw.copy()

antes = len(df)
df.drop_duplicates(subset=["album", "artist", "genre", "year_raw"], inplace=True)
df.reset_index(drop=True, inplace=True)
df["id"] = df.index + 1
print(f"    Duplicados eliminados: {antes - len(df):,}  (filas: {antes:,} -> {len(df):,})")

mapa_generos = {}
for genero_correcto, variantes in GENEROS_SUCIOS.items():
    for v in variantes:
        mapa_generos[v.strip().lower()] = genero_correcto

def estandarizar_genero(valor):
    if pd.isna(valor):
        return None
    clave = str(valor).strip().lower()
    return mapa_generos.get(clave, valor)

df["genre"] = df["genre"].apply(estandarizar_genero)
print(f"    Generos estandarizados. Valores unicos ahora: {sorted(df['genre'].unique())}")

def extraer_anio(valor):
    if pd.isna(valor):
        return None
    valor = str(valor).strip()
    if "/" in valor and len(valor) == 7:
        return int(valor.split("/")[1])
    if "-" in valor and len(valor) == 10:
        return int(valor.split("-")[0])
    try:
        return int(valor[:4])
    except ValueError:
        return None

df["year"] = df["year_raw"].apply(extraer_anio)
df.drop(columns=["year_raw"], inplace=True)

anios_invalidos = df[~df["year"].between(1960, 1989)]
if len(anios_invalidos) > 0:
    print(f"    AVISO: {len(anios_invalidos)} registros fuera de rango -- eliminados")
    df = df[df["year"].between(1960, 1989)]
print(f"    Anios estandarizados. Rango: {df['year'].min()} -- {df['year'].max()}")

mediana_streams = df.groupby("genre")["streams"].transform("median")
df["streams"] = df["streams"].fillna(mediana_streams).astype(int)

moda_edad = df["age_group"].mode()[0]
df["age_group"] = df["age_group"].fillna(moda_edad)

df["region"] = df["region"].fillna("Unknown")

print(f"    Nulos gestionados:")
nulos_despues = df.isnull().sum()
for col in nulos_antes[nulos_antes > 0].index:
    print(f"      {col:<20} {nulos_antes[col]:,} -> {nulos_despues.get(col, 0):,} nulos")

df["retention_rate"] = (
    df["repeat_buyers"] / df["unique_buyers"].replace(0, np.nan)
).round(4).fillna(0)

df["created_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

df.to_csv("data/processed/musica_processed.csv", index=False, encoding="utf-8")
print(f"\n    Guardado en data/processed/musica_processed.csv")
print(f"    Filas finales del dataset limpio: {len(df):,}")

# =============================================================================
# BLOQUE 4: ANALISIS BASICO POST-LIMPIEZA
# =============================================================================
print("\n[4/7] Analisis basico del dataset limpio...")

print("\n    Distribucion por genero:")
dist_genero = df["genre"].value_counts()
for genero, count in dist_genero.items():
    pct = count / len(df) * 100
    print(f"      {genero:<10} {count:>6,} registros  ({pct:.1f}%)")

print("\n    Distribucion por decada:")
dist_decada = df["decade"].value_counts().sort_index()
for decada, count in dist_decada.items():
    pct = count / len(df) * 100
    print(f"      {decada}  {count:>6,} registros  ({pct:.1f}%)")

print("\n    Metricas de ventas:")
print(f"      Media ventas:      {df['sales_units'].mean():,.0f} unidades")
print(f"      Mediana ventas:    {df['sales_units'].median():,.0f} unidades")
print(f"      Total ingresos:    ${df['revenue'].sum():,.2f}")

print("\n    Retencion media por subgenero (Blues y R&B):")
blues_rnb = df[df["genre"].isin(["Blues", "R&B"])]
ret_subgenero = (
    blues_rnb.groupby("subgenre")["retention_rate"]
    .mean()
    .sort_values(ascending=False)
    .round(4)
)
for sg, val in ret_subgenero.items():
    print(f"      {sg:<25} {val:.4f}")

# =============================================================================
# BLOQUE 5: CONEXION Y CREACION DE TABLA EN POSTGRESQL
# =============================================================================
print("\n[5/7] Conectando a PostgreSQL y creando esquema...")

try:
    engine = crear_engine()

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS ventas_musicales"))
        conn.execute(text("""
            CREATE TABLE ventas_musicales (
                id                SERIAL PRIMARY KEY,
                album             VARCHAR(100),
                artist            VARCHAR(100),
                genre             VARCHAR(20)  NOT NULL,
                subgenre          VARCHAR(50),
                year              SMALLINT     NOT NULL,
                decade            VARCHAR(5),
                country           VARCHAR(50),
                region            VARCHAR(100),
                age_group         VARCHAR(10),
                sales_units       INTEGER,
                streams           BIGINT,
                unique_buyers     INTEGER,
                repeat_buyers     INTEGER,
                retention_rate    NUMERIC(6,4),
                revenue           NUMERIC(12,2),
                format            VARCHAR(20),
                created_at        TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.commit()
    print("    Tabla ventas_musicales creada correctamente.")

except Exception as e:
    print(f"\n    ERROR al conectar con PostgreSQL: {e}")
    print("    Verifica que el contenedor esta levantado: docker compose up -d")
    raise

# =============================================================================
# BLOQUE 6: INSERCION MASIVA
# =============================================================================
print("\n[6/7] Insertando datos en PostgreSQL...")

columnas_bd = [
    "album", "artist", "genre", "subgenre", "year", "decade",
    "country", "region", "age_group", "sales_units", "streams",
    "unique_buyers", "repeat_buyers", "retention_rate", "revenue", "format"
]

df_insertar = df[columnas_bd].copy()

try:
    df_insertar.to_sql(
        name      = "ventas_musicales",
        con       = engine,
        if_exists = "append",
        index     = False,
        chunksize = 1000,
        method    = "multi",
    )
    print(f"    Insertados {len(df_insertar):,} registros correctamente.")

except Exception as e:
    print(f"\n    ERROR durante la insercion: {e}")
    raise

# =============================================================================
# BLOQUE 7: VERIFICACION FINAL EN BASE DE DATOS
# =============================================================================
print("\n[7/7] Verificando datos en PostgreSQL...")

with engine.connect() as conn:

    total = conn.execute(text("SELECT COUNT(*) FROM ventas_musicales")).scalar()
    print(f"\n    Total registros en BD:  {total:,}")

    print("\n    Registros por genero:")
    resultado = conn.execute(text("""
        SELECT genre, COUNT(*) as total
        FROM ventas_musicales
        GROUP BY genre
        ORDER BY total DESC
    """))
    for fila in resultado:
        print(f"      {fila[0]:<10} {fila[1]:,}")

    print("\n    Rango de anios:")
    resultado = conn.execute(text("SELECT MIN(year), MAX(year) FROM ventas_musicales"))
    fila = resultado.fetchone()
    print(f"      {fila[0]} -- {fila[1]}")

    print("\n    Top 3 subgeneros con mayor retencion (Blues y R&B):")
    resultado = conn.execute(text("""
        SELECT subgenre, ROUND(AVG(retention_rate)::numeric, 4) as retencion_media
        FROM ventas_musicales
        WHERE genre IN ('Blues', 'R&B')
        GROUP BY subgenre
        ORDER BY retencion_media DESC
        LIMIT 3
    """))
    for fila in resultado:
        print(f"      {fila[0]:<25} {fila[1]}")

    print("\n    Ventas de Salsa por pais:")
    resultado = conn.execute(text("""
        SELECT country, SUM(sales_units) as ventas_totales
        FROM ventas_musicales
        WHERE genre = 'Salsa'
        GROUP BY country
        ORDER BY ventas_totales DESC
    """))
    for fila in resultado:
        print(f"      {fila[0]:<30} {fila[1]:,}")

print("\n" + "=" * 65)
print("  ETL completado con exito.")
print("=" * 65)