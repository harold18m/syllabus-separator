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
├── requirements.txt       # Dependencias (pip)
├── pyproject.toml         # Configuración del proyecto (uv)
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

## Licencia

MIT License
