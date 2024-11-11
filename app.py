from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta'

# Modelo de usuario
class Usuario(UserMixin):
    def __init__(self, id, usuario, contrasena, tipo_usuario=None, materia=None):
        self.id = id
        self.usuario = usuario
        self.contrasena = contrasena
        self.tipo_usuario = tipo_usuario
        self.materia = materia

    def __repr__(self):
        return f"Usuario({self.usuario})"

login_manager = LoginManager(app)

# Carga el usuario
@login_manager.user_loader
def load_user(usuario_id):
    conn = sqlite3.connect('colegio.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    usuario_data = cursor.fetchone()
    conn.close()
    if usuario_data:
        return Usuario(*usuario_data)
    return None

# Ruta principal que redirige al login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        # Verificar credenciales
        conn = sqlite3.connect('colegio.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?", (usuario, contrasena))
        usuario_encontrado = cursor.fetchone()

        # Verificar si es profesor
        if not usuario_encontrado:
            cursor.execute("SELECT * FROM profesores WHERE usuario = ? AND contrasena = ?", (usuario, contrasena))
            usuario_encontrado = cursor.fetchone()

            if usuario_encontrado:
                # Guardar materia del profesor
                usuario_obj = Usuario(usuario_encontrado[0], usuario_encontrado[1], usuario_encontrado[2], usuario_encontrado[3], usuario_encontrado[4])
                login_user(usuario_obj)
                if usuario_encontrado[3] == 'profesor':
                    return redirect(url_for('ver_notas'))
                else:
                    return redirect(url_for('dashboard'))

        if usuario_encontrado:
            login_user(Usuario(*usuario_encontrado))
            if usuario_encontrado[2] == 'coordinador':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('ver_notas'))

    return render_template('login.html')

# Ruta de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Ruta del dashboard (pantalla principal después del login)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Ruta para registrar pagos a profesores
@app.route('/registrar_pago', methods=['GET', 'POST'])
@login_required
def registrar_pago():
    if request.method == 'POST':
        id_profesor = request.form['id_profesor']
        monto = request.form['monto']

        conn = sqlite3.connect('colegio.db')
        cursor = conn.cursor()

        # Insertar pago a profesor en la base de datos
        cursor.execute("INSERT INTO pagos (id_profesor, monto) VALUES (?, ?)", (id_profesor, monto))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('registrar_pago.html')

# Ruta para registrar pagos a profesores
@app.route('/registrar_pago_profesor', methods=['GET', 'POST'])
@login_required
def registrar_pago_profesor():
    if current_user.tipo_usuario != 'coordinador':
        return redirect(url_for('dashboard'))

    conn = sqlite3.connect('colegio.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre, materia, pago FROM profesores")
    profesores = cursor.fetchall()

    if request.method == 'POST':
        for profesor in profesores:
            profesor_id = profesor[0]
            pago = request.form.get(f'pago_{profesor_id}') == 'Si'

            cursor.execute("UPDATE profesores SET pago = ? WHERE id = ?", (pago, profesor_id))
            conn.commit()

    # Recargar profesores con su estado de pago actualizado
    cursor.execute("SELECT id, nombre, materia, pago FROM profesores")
    profesores = cursor.fetchall()

    conn.close()

    return render_template('registrar_pago_profesor.html', profesores=profesores)

# Ruta para ver estudiantes por grado y marcar matrícula pagada
@app.route('/ver_estudiantes', methods=['GET', 'POST'])
@login_required
def ver_estudiantes():
    if current_user.tipo_usuario != 'coordinador':
        return redirect(url_for('dashboard'))

    conn = sqlite3.connect('colegio.db')
    cursor = conn.cursor()

    # Obtener estudiantes por grado
    cursor.execute("SELECT id, identificacion, nombre, edad, grado, matricula_pagada FROM estudiantes WHERE grado = 6")
    estudiantes_6 = cursor.fetchall()

    cursor.execute("SELECT id, identificacion, nombre, edad, grado, matricula_pagada FROM estudiantes WHERE grado = 7")
    estudiantes_7 = cursor.fetchall()

    cursor.execute("SELECT id, identificacion, nombre, edad, grado, matricula_pagada FROM estudiantes WHERE grado = 8")
    estudiantes_8 = cursor.fetchall()

    if request.method == 'POST':
        estudiante_id = request.form.get('estudiante_id')
        if estudiante_id:
            # Actualizar estado de matrícula pagada para el estudiante
            cursor.execute("UPDATE estudiantes SET matricula_pagada = 1 WHERE id = ?", (estudiante_id,))
            conn.commit()

        # Recargar los datos después de actualizar la matrícula
        cursor.execute("SELECT id, identificacion, nombre, edad, grado, matricula_pagada FROM estudiantes WHERE grado = 6")
        estudiantes_6 = cursor.fetchall()

        cursor.execute("SELECT id, identificacion, nombre, edad, grado, matricula_pagada FROM estudiantes WHERE grado = 7")
        estudiantes_7 = cursor.fetchall()

        cursor.execute("SELECT id, identificacion, nombre, edad, grado, matricula_pagada FROM estudiantes WHERE grado = 8")
        estudiantes_8 = cursor.fetchall()

    conn.close()

    return render_template('ver_estudiantes.html', estudiantes_6=estudiantes_6, estudiantes_7=estudiantes_7, estudiantes_8=estudiantes_8)

# Ruta para ver profesores
@app.route('/ver_profesores')
@login_required
def ver_profesores():
    conn = sqlite3.connect('colegio.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, usuario, materia, nombre FROM profesores")
    profesores = cursor.fetchall()
    conn.close()

    return render_template('ver_profesores.html', profesores=profesores)

# Ruta para ver notas como profesor
@app.route('/ver_notas', methods=['GET', 'POST'])
@login_required
def ver_notas():
    try:
        conn = sqlite3.connect('colegio.db')
        cursor = conn.cursor()
        print("Conexión exitosa")

        # Obtener materia del profesor actual
        cursor.execute("SELECT materia FROM profesores WHERE usuario = ?", (current_user.usuario,))
        materia_profesor = cursor.fetchone()

        if materia_profesor is None:
            flash('No se encontró materia para este profesor')
            return redirect(url_for('dashboard'))

        materia_profesor = materia_profesor[0]

        # Obtener todos los estudiantes
        cursor.execute("SELECT id, nombre, edad, grado FROM estudiantes ORDER BY grado")
        estudiantes = cursor.fetchall()

        # Agrupar estudiantes por grado
        estudiantes_por_grado = {}
        for estudiante in estudiantes:
            grado = estudiante[3]
            if grado not in estudiantes_por_grado:
                estudiantes_por_grado[grado] = []
            estudiantes_por_grado[grado].append(estudiante)

        # Obtener notas del profesor actual para su materia
        cursor.execute("SELECT e.id, e.nombre, n.nota FROM estudiantes e INNER JOIN notas n ON e.id = n.id_estudiante INNER JOIN profesores p ON n.id_profesor = p.id WHERE p.usuario = ? AND n.materia = ?", (current_user.usuario, materia_profesor))
        notas = cursor.fetchall()

        # Crear diccionario para notas por estudiante
        notas_por_estudiante = {nota[0]: nota[2] for nota in notas}

        # Obtener última nota por estudiante
        cursor.execute("SELECT id_estudiante, nota FROM notas WHERE id_profesor = ? AND materia = ?", (current_user.id, materia_profesor))
        ultimas_notas_db = cursor.fetchall()
        ultimas_notas = {nota[0]: nota[1] for nota in ultimas_notas_db}

        if request.method == 'POST':
            for estudiante_id, nota in request.form.items():
                if estudiante_id != 'csrf_token':
                    cursor.execute("INSERT OR REPLACE INTO notas (id_estudiante, id_profesor, materia, nota) VALUES (?, ?, ?, ?)",
                                   (estudiante_id, current_user.id, materia_profesor, nota))
                    conn.commit()
                    ultimas_notas[int(estudiante_id)] = nota  # Actualizar última nota
            flash('Notas guardadas correctamente')
            return redirect(url_for('ver_notas'))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

    return render_template('ver_notas.html', estudiantes_por_grado=estudiantes_por_grado, notas_por_estudiante=notas_por_estudiante, ultimas_notas=ultimas_notas, materia=materia_profesor)

# Ruta para verificar notas de estudiantes
@app.route('/verificar_nota', methods=['GET', 'POST'])
@login_required
def verificar_nota():
    if request.method == 'POST':
        id_estudiante = request.form['id_estudiante']

        conn = sqlite3.connect('colegio.db')
        cursor = conn.cursor()

        # Obtener datos del estudiante
        cursor.execute("SELECT nombre, grado FROM estudiantes WHERE id = ?", (id_estudiante,))
        estudiante_data = cursor.fetchone()

        if estudiante_data:
            # Obtener notas del estudiante
            cursor.execute("SELECT p.materia, n.nota FROM notas n INNER JOIN profesores p ON n.id_profesor = p.id WHERE n.id_estudiante = ?", (id_estudiante,))
            notas = cursor.fetchall()

            return render_template('verificar_nota.html', estudiante=estudiante_data, notas=notas)
        else:
            flash('Estudiante no encontrado')
            return redirect(url_for('verificar_nota'))

    return render_template('verificar_nota.html')

if __name__ == '__main__':
    app.run(debug=True)