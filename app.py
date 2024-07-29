# Importar Flask y funciones para renderizar plantillas y manejar solicitudes
from flask import Flask, render_template, request
import psycopg2  # Importar psycopg2 para conectarse a la base de datos PostgreSQL
import folium  # Importar Folium para crear mapas interactivos
import matplotlib.pyplot as plt  # Importar matplotlib para crear gráficos
# Importar herramientas 3D de Matplotlib
from mpl_toolkits.mplot3d import Axes3D
# Importar FuncAnimation y PillowWriter para crear y guardar animaciones
from matplotlib.animation import FuncAnimation, PillowWriter
import os  # Importar os para manejar rutas de archivos

app = Flask(__name__)  # Crear una instancia de la aplicación Flask


def get_db_connection():
    """Establece una conexión a la base de datos PostgreSQL."""
    conn = psycopg2.connect(
        dbname="geodata",
        user="dcordoba",
        password="Ozzy153624+",
        host="localhost"
    )
    return conn


def generate_matplotlib_graph(sismos):
    """Genera un gráfico 3D de sismos y guarda una imagen y una animación."""
    fig = plt.figure(
        figsize=(21, 14))  # Crear una figura de Matplotlib con tamaño 21x14
    ax = fig.add_subplot(111, projection='3d')  # Añadir un subplot 3D

    # Obtener los datos de la provincia de Córdoba
    conn = get_db_connection()  # Obtener conexión a la base de datos
    cur = conn.cursor()  # Crear un cursor para ejecutar consultas
    cur.execute("""
        SELECT ST_X(point) AS lon, ST_Y(point) AS lat
        FROM (
            SELECT (ST_DumpPoints(ST_ExteriorRing(geom))).geom AS point
            FROM provincia
        ) AS points;
    """)  # Ejecutar consulta para obtener puntos del perímetro de la provincia
    provincia_data = cur.fetchall()  # Obtener todos los resultados de la consulta
    cur.close()  # Cerrar el cursor
    conn.close()  # Cerrar la conexión

    if not provincia_data:
        # Manejar el caso en que no se obtuvieron datos
        raise ValueError("No se obtuvieron datos de la provincia.")

    # Separar latitud y longitud en listas
    latitud, longitud = zip(*provincia_data)

    # Graficar el perímetro de la provincia de Córdoba con líneas
    ax.plot(latitud, longitud, zs=0, zdir='z',
            label='Perímetro de Córdoba', color='b')

    # Graficar los puntos de los sismos
    latitud_s = [sismo[2]
                 for sismo in sismos]  # Obtener latitudes de los sismos
    longitud_s = [sismo[3]
                  for sismo in sismos]  # Obtener longitudes de los sismos
    # Obtener profundidades de los sismos (negativas para representar hacia abajo)
    profundidad_s = [-1 * sismo[4] for sismo in sismos]

    scatter = ax.scatter3D(longitud_s, latitud_s, profundidad_s,
                           label='Sismos', color='r', alpha=0.5)  # Crear un scatter plot 3D de los sismos

    # Configurar la vista inicial
    # Establecer ángulo inicial de elevación y azimut
    ax.view_init(elev=15, azim=225)
    # Guardar la figura como imagen
    # Definir la ruta del archivo de imagen
    image_path = os.path.join('static', 'sismos_plot.png')
    plt.savefig(image_path)  # Guardar la figura como PNG
    plt.close(fig)  # Cerrar la figura

    # Función de animación

    def animate(i):
        ax.view_init(elev=15, azim=i)  # Rotar el gráfico en el eje azimutal
        return ax,

    # Crear la animación
    ani = FuncAnimation(fig, animate, frames=360, interval=20, blit=False)

    # Guardar la animación en un archivo GIF utilizando Pillow
    # Definir la ruta del archivo GIF
    gif_path = os.path.join('static', 'sismos_plot.gif')
    # Guardar la animación como GIF
    ani.save(gif_path, writer=PillowWriter(fps=20))


@app.route('/')
def index():
    """Ruta principal que muestra el último sismo en un mapa."""
    conn = get_db_connection()  # Obtener conexión a la base de datos
    cur = conn.cursor()  # Crear un cursor para ejecutar consultas
    cur.execute("""
        SELECT fecha, hora, latitud, longitud, profundidad, magnitud 
        FROM sismos 
        ORDER BY id DESC 
        LIMIT 1;
    """)  # Consultar el último sismo registrado
    sismos = cur.fetchall()  # Obtener todos los resultados de la consulta
    cur.close()  # Cerrar el cursor
    conn.close()  # Cerrar la conexión

    if sismos:
        sismo = sismos[0]  # Obtener el último sismo
        lat, lon = sismo[2], sismo[3]  # Obtener latitud y longitud del sismo

        # Crear el mapa de Folium
        # Crear un mapa centrado en Córdoba
        mapa = folium.Map(location=[-32.2935000, -64.1810500], zoom_start=6)
        folium.Marker(
            location=[lat, lon],
            popup=f"Fecha: {sismo[0]}, Hora: {sismo[1]}, Magnitud: {sismo[5]}, Profundidad: {sismo[4]} km",
        ).add_to(mapa)  # Añadir un marcador para el sismo

        # Guardar el mapa en un archivo HTML
        mapa.save('static/mapa.html')  # Guardar el mapa como HTML

    # Renderizar plantilla index.html con los datos del sismo
    return render_template('index.html', sismos=sismos)


@app.route('/consultas')
def consultas():
    """Ruta que muestra el formulario de consultas."""
    return render_template('consultas.html')  # Renderizar plantilla consultas.html


@app.route('/resultados', methods=['POST'])
def resultados():
    """Ruta que maneja el formulario de consultas y muestra los resultados."""
    query = "SELECT fecha, hora, latitud, longitud, profundidad, magnitud, geom FROM sismos WHERE 1=1"  # Consulta base
    # Consulta base para contar el número de resultados
    count_query = "SELECT COUNT(*) FROM sismos WHERE 1=1"
    params = []  # Lista para almacenar los parámetros de la consulta

    # Condiciones para la consulta
    if 'fecha_inicio' in request.form and request.form['fecha_inicio']:
        query += " AND fecha >= %s"
        count_query += " AND fecha >= %s"
        params.append(request.form['fecha_inicio'])
    if 'fecha_fin' in request.form and request.form['fecha_fin']:
        query += " AND fecha <= %s"
        count_query += " AND fecha <= %s"
        params.append(request.form['fecha_fin'])
    if 'hora_inicio' in request.form and request.form['hora_inicio']:
        query += " AND hora >= %s"
        count_query += " AND hora >= %s"
        params.append(request.form['hora_inicio'])
    if 'hora_fin' in request.form and request.form['hora_fin']:
        query += " AND hora <= %s"
        count_query += " AND hora <= %s"
        params.append(request.form['hora_fin'])
    if 'magnitud_min' in request.form and request.form['magnitud_min']:
        query += " AND magnitud >= %s"
        count_query += " AND magnitud >= %s"
        params.append(request.form['magnitud_min'])
    if 'magnitud_max' in request.form and request.form['magnitud_max']:
        query += " AND magnitud <= %s"
        count_query += " AND magnitud <= %s"
        params.append(request.form['magnitud_max'])
    if 'profundidad_min' in request.form and request.form['profundidad_min']:
        query += " AND profundidad >= %s"
        count_query += " AND profundidad >= %s"
        params.append(request.form['profundidad_min'])
    if 'profundidad_max' in request.form and request.form['profundidad_max']:
        query += " AND profundidad <= %s"
        count_query += " AND profundidad <= %s"
        params.append(request.form['profundidad_max'])

    # Condición para latitud y longitud con radio de 10 km
    if 'latitud' in request.form and request.form['latitud'] and 'longitud' in request.form and request.form['longitud']:
        lat = float(request.form['latitud'])
        lon = float(request.form['longitud'])
        query += " AND ST_DWithin(geom::geography, ST_MakePoint(%s, %s)::geography, 10000)"
        count_query += " AND ST_DWithin(geom::geography, ST_MakePoint(%s, %s)::geography, 10000)"
        params.append(lon)
        params.append(lat)

    conn = get_db_connection()  # Obtener conexión a la base de datos
    cur = conn.cursor()  # Crear un cursor para ejecutar consultas

    # Ejecutar la consulta para contar el número de registros
    cur.execute(count_query, tuple(params))
    total_eventos = cur.fetchone()[0]  # Obtener el número de eventos

    # Ejecutar la consulta para obtener los resultados
    cur.execute(query, tuple(params))
    sismos = cur.fetchall()  # Obtener todos los resultados de la consulta
    cur.close()  # Cerrar el cursor
    conn.close()  # Cerrar la conexión

    # Crear el mapa de Folium con los resultados
    if sismos:
        # Obtener la ubicación central para el mapa
        latitudes = [sismo[2] for sismo in sismos]
        longitudes = [sismo[3] for sismo in sismos]
        lat_central = sum(latitudes) / len(latitudes)
        lon_central = sum(longitudes) / len(longitudes)

        # Crear el mapa de Folium
        # mapa = folium.Map(location=[lat_central, lon_central], zoom_start=6.5)
        mapa = folium.Map(location=[-32.2935000, -64.1810500], zoom_start=6)

        for sismo in sismos:
            folium.Marker(
                location=[sismo[2], sismo[3]],
                popup=f"Fecha: {sismo[0]}, Hora: {sismo[1]}, Magnitud: {sismo[5]}, Profundidad: {sismo[4]} km"
            ).add_to(mapa)  # Añadir marcadores para cada sismo

        # Guardar el mapa en un archivo HTML
        mapa.save('static/mapa_resultados.html')  # Guardar el mapa como HTML

        # Generar gráfico 3D con Matplotlib
        # Llamar a la función para generar el gráfico 3D
        generate_matplotlib_graph(sismos)

    # Renderizar plantilla resultados.html con los resultados de la consulta
    return render_template('resultados.html', sismos=sismos, total_eventos=total_eventos)


if __name__ == '__main__':
    # Ejecutar la aplicación Flask en modo debug
    app.run(debug=True, host='0.0.0.0')
