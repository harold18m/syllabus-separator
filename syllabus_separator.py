#!/usr/bin/env python3
"""
Script para procesar PDFs de sílabos de Tecsup.
Segmenta el PDF por cursos y guarda cada uno en un archivo independiente.
"""

import fitz  # PyMuPDF
import os
import re
import sys
from pathlib import Path


def limpiar_nombre_archivo(nombre: str) -> str:
    """
    Limpia el nombre de caracteres especiales e inválidos para archivos.
    """
    # Eliminar caracteres no válidos para nombres de archivo
    nombre_limpio = re.sub(r'[<>:"/\\|?*]', '', nombre)
    # Reemplazar múltiples espacios por uno solo
    nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio)
    # Eliminar espacios al inicio y final
    nombre_limpio = nombre_limpio.strip()
    # Limitar longitud del nombre (máximo 100 caracteres)
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


def procesar_pdf_silabos(ruta_pdf: str, carpeta_salida: str = "Convalidaciones_UPC") -> None:
    """
    Procesa un PDF de sílabos y lo segmenta por cursos.
    
    Args:
        ruta_pdf: Ruta al archivo PDF de entrada
        carpeta_salida: Nombre de la carpeta donde guardar los PDFs segmentados
    """
    MARCADOR = "Sílabo del Curso"
    
    # Verificar que el archivo existe
    if not os.path.exists(ruta_pdf):
        print(f"Error: El archivo '{ruta_pdf}' no existe.")
        sys.exit(1)
    
    # Crear carpeta de salida si no existe
    Path(carpeta_salida).mkdir(parents=True, exist_ok=True)
    print(f"Carpeta de salida: {carpeta_salida}/")
    print("-" * 50)
    
    # Abrir el PDF
    try:
        doc = fitz.open(ruta_pdf)
    except Exception as e:
        print(f"Error al abrir el PDF: {e}")
        sys.exit(1)
    
    total_paginas = len(doc)
    print(f"Total de páginas en el PDF: {total_paginas}")
    print("-" * 50)
    
    # Lista para almacenar información de cada curso
    # Cada elemento: (página_inicio, nombre_curso)
    cursos = []
    
    # Recorrer el PDF página por página
    for num_pagina in range(total_paginas):
        pagina = doc[num_pagina]
        texto = pagina.get_text()
        
        # Buscar el marcador en la página
        if MARCADOR in texto:
            nombre_curso = extraer_nombre_curso(texto, MARCADOR)
            nombre_limpio = limpiar_nombre_archivo(nombre_curso)
            cursos.append((num_pagina, nombre_limpio))
    
    if not cursos:
        print("No se encontraron cursos con el marcador 'Sílabo del Curso'.")
        doc.close()
        return
    
    print(f"Cursos detectados: {len(cursos)}")
    print("-" * 50)
    
    # Contador para cursos sin nombre
    contador_desconocido = 0
    cursos_procesados = []
    
    # Procesar cada curso
    for i, (pagina_inicio, nombre_curso) in enumerate(cursos):
        # Determinar página final del curso
        if i + 1 < len(cursos):
            # El curso termina en la página anterior al siguiente curso
            pagina_fin = cursos[i + 1][0] - 1
        else:
            # Último curso: termina en la última página del documento
            pagina_fin = total_paginas - 1
        
        # Manejar nombre vacío
        if not nombre_curso:
            contador_desconocido += 1
            nombre_curso = f"Curso_Desconocido_{contador_desconocido}"
        
        # Crear nombre de archivo
        nombre_archivo = f"{nombre_curso}.pdf"
        ruta_salida = os.path.join(carpeta_salida, nombre_archivo)
        
        # Manejar duplicados agregando un sufijo
        contador_duplicado = 1
        while os.path.exists(ruta_salida):
            nombre_archivo = f"{nombre_curso}_{contador_duplicado}.pdf"
            ruta_salida = os.path.join(carpeta_salida, nombre_archivo)
            contador_duplicado += 1
        
        # Crear nuevo PDF con las páginas del curso
        try:
            doc_nuevo = fitz.open()
            doc_nuevo.insert_pdf(doc, from_page=pagina_inicio, to_page=pagina_fin)
            doc_nuevo.save(ruta_salida)
            doc_nuevo.close()
            
            num_paginas_curso = pagina_fin - pagina_inicio + 1
            cursos_procesados.append({
                'nombre': nombre_curso,
                'archivo': nombre_archivo,
                'paginas': num_paginas_curso,
                'rango': f"{pagina_inicio + 1}-{pagina_fin + 1}"
            })
            
            print(f"✓ {nombre_curso}")
            print(f"  Páginas: {pagina_inicio + 1} a {pagina_fin + 1} ({num_paginas_curso} páginas)")
            print(f"  Archivo: {nombre_archivo}")
            print()
            
        except Exception as e:
            print(f"✗ Error al guardar '{nombre_curso}': {e}")
    
    # Cerrar documento original
    doc.close()
    
    # Imprimir resumen final
    print("=" * 50)
    print("RESUMEN")
    print("=" * 50)
    print(f"Total de cursos procesados: {len(cursos_procesados)}")
    print(f"Cursos con nombre desconocido: {contador_desconocido}")
    print(f"Carpeta de salida: {carpeta_salida}/")
    print()
    print("Lista de cursos:")
    for i, curso in enumerate(cursos_procesados, 1):
        print(f"  {i}. {curso['nombre']} ({curso['paginas']} páginas)")


def main():
    """Función principal del script."""
    if len(sys.argv) < 2:
        print("Uso: python syllabus_separator.py <ruta_pdf>")
        print("Ejemplo: python syllabus_separator.py silabos_tecsup.pdf")
        sys.exit(1)
    
    ruta_pdf = sys.argv[1]
    
    # Opcionalmente se puede pasar la carpeta de salida como segundo argumento
    carpeta_salida = sys.argv[2] if len(sys.argv) > 2 else "Convalidaciones_UPC"
    
    print("=" * 50)
    print("PROCESADOR DE SÍLABOS DE TECSUP")
    print("=" * 50)
    print(f"Archivo de entrada: {ruta_pdf}")
    print()
    
    procesar_pdf_silabos(ruta_pdf, carpeta_salida)
    
    print()
    print("Proceso completado.")


if __name__ == "__main__":
    main()
