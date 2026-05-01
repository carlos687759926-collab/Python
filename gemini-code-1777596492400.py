import requests
from bs4 import BeautifulSoup
import csv
import time
import re

def extraer_precios_cronoshare():
    url_principal = "https://www.cronoshare.com/cuanto-cuesta"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    print("1. Accediendo a la página principal para recopilar enlaces...")
    try:
        respuesta = requests.get(url_principal, headers=headers)
        soup = BeautifulSoup(respuesta.text, 'html.parser')
    except Exception as e:
        print(f"Error al acceder a la web: {e}")
        return

    enlaces = soup.find_all('a', href=True)
    servicios = []
    
    for link in enlaces:
        href = link['href']
        # Filtramos para asegurarnos de que son páginas de precio y no otros menús
        if "/cuanto-cuesta/" in href and href != "/cuanto-cuesta" and not href.endswith(".jpg"):
            url_completa = href if href.startswith('http') else f"https://www.cronoshare.com{href}"
            
            # Limpiamos el nombre usando la URL para un resultado profesional
            # Ejemplo: de "/cuanto-cuesta/broker-hipotecario" obtenemos "Broker hipotecario"
            nombre_limpio = href.split('/')[-1].replace('-', ' ').capitalize()
            
            # Evitar enlaces duplicados
            if not any(s['url'] == url_completa for s in servicios):
                servicios.append({'nombre': nombre_limpio, 'url': url_completa})

    print(f"¡Éxito! Se han encontrado {len(servicios)} servicios distintos.\n")
    print("2. Iniciando la extracción de precios de cada enlace...")

    # SOLUCIÓN DE TEXTO: 'utf-8-sig' obliga a Excel/Drive a leer correctamente los caracteres
    with open('precios_cronoshare_completo.csv', 'w', newline='', encoding='utf-8-sig') as archivo_csv:
        escritor = csv.DictWriter(archivo_csv, fieldnames=['Servicio', 'Rango de Precio', 'URL'])
        escritor.writeheader()

        for i, servicio in enumerate(servicios):
            print(f"[{i+1}/{len(servicios)}] Leyendo: {servicio['nombre']}...")
            
            try:
                res = requests.get(servicio['url'], headers=headers)
                soup_detalle = BeautifulSoup(res.text, 'html.parser')
                
                # Extraemos todo el texto limpio de la página
                texto_pagina = soup_detalle.get_text(separator=' ', strip=True)
                
                # ESTRATEGIA INFALIBLE: Buscar el texto exacto típico de Cronoshare
                # Encuentra rangos tipo "15 € - 25 € / hora. Precio medio a nivel nacional"
                patron_cronoshare = r'([\d\.,]+\s*€(?:\s*-\s*[\d\.,]+\s*€)?.*?Precio medio a nivel nacional)'
                coincidencia = re.search(patron_cronoshare, texto_pagina, re.IGNORECASE)
                
                if coincidencia:
                    precio_final = coincidencia.group(1).strip()
                else:
                    # Alternativa si omiten la frase "Precio medio" pero sí ponen un rango de euros
                    patron_alternativo = r'([\d\.,]+\s*€\s*-\s*[\d\.,]+\s*€(?:[^\.]+)?)'
                    coincidencia_alt = re.search(patron_alternativo, texto_pagina)
                    if coincidencia_alt:
                        precio_final = coincidencia_alt.group(1).strip()
                    else:
                        precio_final = "Precio no listado en el encabezado"
                        
            except Exception as e:
                precio_final = f"Error de lectura"

            # Guardamos la fila inmediatamente
            escritor.writerow({
                'Servicio': servicio['nombre'],
                'Rango de Precio': precio_final,
                'URL': servicio['url']
            })
            
            # Pausa obligatoria de 1 segundo para no saturar el servidor y que no nos bloqueen la IP
            time.sleep(1)

    print("\n¡Proceso finalizado al 100%! Puedes subir el archivo 'precios_cronoshare_completo.csv' a tu Google Drive.")

if __name__ == "__main__":
    extraer_precios_cronoshare()