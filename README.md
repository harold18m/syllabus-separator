# Separador de Sílabos de Tecsup

Aplicación web para procesar PDFs de sílabos de Tecsup, segmentándolos en archivos individuales por curso.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip

## Instalación y Ejecución

### Con UV (recomendado)

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/syllabus-separator.git
cd syllabus-separator

# Instalar dependencias y ejecutar
uv sync
uv run python app.py
```

### Con pip

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/syllabus-separator.git
cd syllabus-separator

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python app.py
```

Luego abre tu navegador en: **http://127.0.0.1:5000**

## Uso

1. Abre la aplicación en tu navegador
2. Arrastra tu PDF de sílabos o haz clic para seleccionarlo
3. Presiona "Procesar PDF"
4. Descarga cada curso individualmente o todos en un ZIP

## Características

- **Interfaz moderna**: Diseño limpio con drag & drop
- **Procesamiento automático**: Detecta cada curso por el marcador "Sílabo del Curso"
- **Extracción inteligente**: Obtiene el nombre del curso de la línea siguiente al marcador
- **Descarga individual**: Descarga cada curso por separado
- **Descarga masiva**: Descarga todos los cursos en `Convalidaciones_UPC.zip`

## Lógica de Segmentación

1. Recorre el PDF página por página usando PyMuPDF
2. Busca el marcador **"Sílabo del Curso"** para identificar el inicio de cada curso
3. Extrae el nombre del curso del texto que aparece en la línea inmediatamente debajo
4. El contenido de un curso termina en la página anterior al siguiente marcador

## Estructura del Proyecto

```
syllabus-separator/
├── app.py                 # Aplicación web Flask
├── syllabus_separator.py  # Script CLI (alternativo)
├── templates/
│   └── index.html         # Interfaz web
├── requirements.txt       # Dependencias (pip/Render)
├── pyproject.toml         # Configuración del proyecto (uv)
├── render.yaml            # Configuración de despliegue en Render
└── README.md
```

## Script CLI (Alternativo)

También puedes usar el script de línea de comandos:

```bash
uv run python syllabus_separator.py tu_archivo.pdf
```

## Manejo de Errores

- Si el nombre del curso está vacío → usa `Curso_Desconocido_N`
- Si hay nombres duplicados → agrega sufijo numérico
- Caracteres especiales inválidos → se eliminan automáticamente

## Tecnologías

- **Backend**: Flask 3.x
- **PDF Processing**: PyMuPDF (fitz)
- **Frontend**: HTML5, CSS3, JavaScript vanilla

## Despliegue en Render

Render es ideal para esta app porque mantiene el servidor activo (no serverless), lo que permite que las descargas funcionen correctamente.

### Opción 1: Desde la web (recomendado)

1. Sube el proyecto a **GitHub** o **GitLab**.
2. Entra en [render.com](https://render.com) y crea una cuenta (puedes usar GitHub).
3. En el Dashboard: **New** → **Web Service**.
4. Conecta tu repositorio.
5. Render detectará Python automáticamente. Configura:
   - **Name**: `syllabus-separator` (o el que prefieras)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Selecciona el plan **Free** (la app se duerme tras 15 min de inactividad).
7. Haz clic en **Create Web Service**.

### Opción 2: Con Blueprint (render.yaml)

El proyecto incluye `render.yaml` con la configuración lista. Solo conecta el repo y Render lo configurará automáticamente.

### Variables de entorno (opcional)

Si necesitas configurar algo, puedes añadir variables en el panel de Render:
- `PORT`: Render lo define automáticamente, gunicorn lo usa por defecto.

### Notas sobre el plan gratuito

- La app se **duerme** tras ~15 minutos de inactividad.
- El primer request tras dormir tarda unos segundos (cold start).
- Para evitar esto, puedes usar el plan **Starter** (~7 USD/mes) o un servicio de ping externo.

## Licencia

MIT License
