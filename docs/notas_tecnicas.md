# Notas Técnicas — Decisiones de Diseño

## Elección de base de datos: PostgreSQL

Se eligió PostgreSQL 15 frente a otras alternativas (MySQL, MongoDB, Elasticsearch) por las siguientes razones:

- Soporte nativo de tipos de datos avanzados (DATE, NUMERIC, TEXT).
- Integración directa y madura con SQLAlchemy y psycopg2.
- Imagen Docker oficial mantenida y estable.
- Soporte completo de SQL estándar, adecuado para las consultas analíticas del dashboard.
- Metabase tiene soporte nativo y optimizado para PostgreSQL.

## Elección de herramienta BI: Metabase

Se eligió Metabase frente a Grafana, Superset o Kibana por:

- Imagen Docker oficial con configuración mínima.
- Interfaz web intuitiva que permite construir dashboards sin escribir SQL obligatoriamente.
- Conexión a PostgreSQL en pocos pasos con UI guiada.
- Soporte de gráficos de líneas, barras y mapas, necesarios para las 3 preguntas de negocio.
- Curva de aprendizaje baja, lo que reduce el riesgo de fallos en la fase de visualización.

## Ejecución del ETL en el host (no en contenedor)

El script etl_musica.py se ejecuta directamente en el sistema anfitrión (Windows 11) 
en lugar de en un contenedor adicional. Esta decisión se tomó porque:

- Simplifica la depuración de errores Python.
- Evita problemas de permisos y montaje de volúmenes en Windows.
- El script se conecta a PostgreSQL a través del puerto 5432 expuesto al host.
- Es perfectamente válido en un entorno académico y de desarrollo.

## Dataset simulado

El dataset se genera programáticamente con Python (numpy, faker) en lugar de 
descargarse de una fuente externa. Esto garantiza:

- Reproducibilidad total del proyecto.
- Control sobre la distribución de géneros, décadas y geografías.
- Posibilidad de introducir errores intencionados de forma controlada.
- Independencia de URLs o APIs externas que podrían no estar disponibles.

## Driver de conexion Python: pg8000

Durante el desarrollo se identifico un bug conocido en psycopg2 y psycopg3
en entornos Windows con locale en espanol: el servidor PostgreSQL envia
mensajes de error de autenticacion en latin-1 durante la fase de startup,
antes de que se pueda negociar la codificacion UTF-8 con el cliente.
Esto provoca un UnicodeDecodeError en psycopg al intentar decodificar
dichos mensajes.

La solucion adoptada fue usar pg8000, un driver PostgreSQL escrito
enteramente en Python puro, sin dependencias de libpq ni del sistema
operativo. pg8000 no tiene este problema porque implementa el protocolo
de comunicacion de PostgreSQL de forma independiente.

Adicionalmente, el PostgreSQL nativo de Windows ocupaba el puerto 5432,
por lo que el contenedor Docker se expone en el puerto 5455 del host.
Internamente el contenedor sigue usando el puerto 5432 estandar.