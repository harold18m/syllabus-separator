#!/usr/bin/env python3
"""
Web App para procesar PDFs de sílabos de Tecsup.
Segmenta el PDF por cursos y permite descargar cada uno.
"""

import fitz  # PyMuPDF
import os
import re
import io
import zipfile
import uuid
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB máximo
# Desactivar debug en producción (Render define RENDER=true)
if os.environ.get('RENDER'):
    app.config['DEBUG'] = False

# Carpeta temporal para archivos
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def limpiar_nombre_archivo(nombre: str) -> str:
    """Limpia el nombre de caracteres especiales e inválidos para archivos."""
    nombre_limpio = re.sub(r'[<>:"/\\|?*]', '', nombre)
    nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio)
    nombre_limpio = nombre_limpio.strip()
    if len(nombre_limpio) > 100:
        nombre_limpio = nombre_limpio[:100].strip()
    return nombre_limpio


def extraer_nombre_curso(texto: str, marcador: str = "Sílabo del Curso") -> str:
    """
    Extrae el nombre del curso que aparece en la línea debajo del marcador.
    El formato esperado es:
        Sílabo del Curso
        NOMBRE DEL CURSO
    """
    # Buscar el marcador
    idx = texto.find(marcador)
    if idx == -1:
        return ""
    
    # Obtener el texto después del marcador
    texto_despues = texto[idx + len(marcador):]
    
    # Dividir en líneas y buscar la primera línea con contenido real
    lineas = texto_despues.split('\n')
    
    for linea in lineas:
        linea = linea.strip()
        # Ignorar líneas vacías o que solo contengan espacios/caracteres especiales
        if linea and len(linea) > 1:
            # Verificar que no sea otra sección o encabezado del documento
            # El nombre del curso generalmente no contiene ciertos patrones
            palabras_excluir = ['código', 'créditos', 'horas', 'ciclo', 'semestre', 
                               'requisito', 'docente', 'sumilla', 'competencia']
            linea_lower = linea.lower()
            
            # Si la línea parece ser un campo del formulario, saltarla
            if any(palabra in linea_lower for palabra in palabras_excluir):
                continue
            
            # Si contiene ":" probablemente es un campo, no el nombre
            if ':' in linea and len(linea.split(':')[0]) < 20:
                continue
                
            return linea
    
    return ""


def procesar_pdf(pdf_bytes: bytes) -> dict:
    """
    Procesa un PDF de sílabos y retorna los cursos segmentados.
    
    Returns:
        dict con 'cursos' (lista de info) y 'archivos' (dict nombre -> bytes)
    """
    MARCADOR = "Sílabo del Curso"
    
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_paginas = len(doc)
    
    # Encontrar inicio de cada curso
    cursos_encontrados = []
    for num_pagina in range(total_paginas):
        pagina = doc[num_pagina]
        texto = pagina.get_text()
        
        if MARCADOR in texto:
            nombre_curso = extraer_nombre_curso(texto, MARCADOR)
            nombre_limpio = limpiar_nombre_archivo(nombre_curso)
            cursos_encontrados.append((num_pagina, nombre_limpio))
    
    if not cursos_encontrados:
        doc.close()
        return {'cursos': [], 'archivos': {}, 'mensaje': 'No se encontraron cursos'}
    
    # Procesar cada curso
    contador_desconocido = 0
    cursos_info = []
    archivos_pdf = {}
    nombres_usados = {}
    
    for i, (pagina_inicio, nombre_curso) in enumerate(cursos_encontrados):
        # Determinar página final
        if i + 1 < len(cursos_encontrados):
            pagina_fin = cursos_encontrados[i + 1][0] - 1
        else:
            pagina_fin = total_paginas - 1
        
        # Manejar nombre vacío
        if not nombre_curso:
            contador_desconocido += 1
            nombre_curso = f"Curso_Desconocido_{contador_desconocido}"
        
        # Manejar duplicados
        nombre_base = nombre_curso
        if nombre_base in nombres_usados:
            nombres_usados[nombre_base] += 1
            nombre_curso = f"{nombre_base}_{nombres_usados[nombre_base]}"
        else:
            nombres_usados[nombre_base] = 0
        
        nombre_archivo = f"{nombre_curso}.pdf"
        num_paginas = pagina_fin - pagina_inicio + 1
        
        # Crear PDF del curso
        doc_nuevo = fitz.open()
        doc_nuevo.insert_pdf(doc, from_page=pagina_inicio, to_page=pagina_fin)
        
        # Guardar en memoria
        pdf_buffer = io.BytesIO()
        doc_nuevo.save(pdf_buffer)
        doc_nuevo.close()
        
        archivos_pdf[nombre_archivo] = pdf_buffer.getvalue()
        
        cursos_info.append({
            'nombre': nombre_curso,
            'archivo': nombre_archivo,
            'paginas': num_paginas,
            'rango': f"{pagina_inicio + 1}-{pagina_fin + 1}"
        })
    
    doc.close()
    
    return {
        'cursos': cursos_info,
        'archivos': archivos_pdf,
        'total_paginas': total_paginas,
        'mensaje': f'Se procesaron {len(cursos_info)} cursos exitosamente'
    }


# Variable global temporal para almacenar resultados (en producción usar Redis/DB)
resultados_procesados = {}


@app.route('/')
def index():
    """Página principal."""
    return render_template('index.html')


@app.route('/procesar', methods=['POST'])
def procesar():
    """Endpoint para procesar el PDF subido."""
    if 'pdf' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    archivo = request.files['pdf']
    
    if archivo.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not archivo.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'El archivo debe ser un PDF'}), 400
    
    try:
        pdf_bytes = archivo.read()
        resultado = procesar_pdf(pdf_bytes)
        
        if not resultado['cursos']:
            return jsonify({
                'error': 'No se encontraron cursos con el marcador "Sílabo del Curso"'
            }), 400
        
        # Generar ID único para este resultado
        resultado_id = str(uuid.uuid4())
        resultados_procesados[resultado_id] = resultado['archivos']
        
        return jsonify({
            'success': True,
            'resultado_id': resultado_id,
            'cursos': resultado['cursos'],
            'total_paginas': resultado['total_paginas'],
            'mensaje': resultado['mensaje']
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al procesar el PDF: {str(e)}'}), 500


@app.route('/descargar/<resultado_id>/<nombre_archivo>')
def descargar_individual(resultado_id, nombre_archivo):
    """Descargar un PDF individual."""
    if resultado_id not in resultados_procesados:
        return jsonify({'error': 'Resultado no encontrado'}), 404
    
    archivos = resultados_procesados[resultado_id]
    
    if nombre_archivo not in archivos:
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    return send_file(
        io.BytesIO(archivos[nombre_archivo]),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nombre_archivo
    )


@app.route('/descargar-todo/<resultado_id>')
def descargar_todo(resultado_id):
    """Descargar todos los PDFs como ZIP."""
    if resultado_id not in resultados_procesados:
        return jsonify({'error': 'Resultado no encontrado'}), 404
    
    archivos = resultados_procesados[resultado_id]
    
    # Crear ZIP en memoria
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for nombre, contenido in archivos.items():
            zip_file.writestr(f"Convalidaciones_UPC/{nombre}", contenido)
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='Convalidaciones_UPC.zip'
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Nunca debug en producción (Render define RENDER=true)
    debug = not os.environ.get('RENDER')
    app.run(debug=debug, port=port)
