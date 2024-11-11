import sqlite3
import random

# Montos de matrícula por grado
MATRICULA_GRADO_6 = 600000
MATRICULA_GRADO_7 = 700000
MATRICULA_GRADO_8 = 800000

def generar_nombre_aleatorio():
    nombres = ["Juan", "Ana", "Carlos", "Maria", "Pedro", "Laura", "Luis", "Sofia", "Felipe", "Marta"]
    apellidos = ["Gomez", "Lopez", "Martinez", "Perez", "Rodriguez", "Sanchez", "Garcia", "Fernandez", "Torres", "Diaz"]
    nombre = random.choice(nombres) + " " + random.choice(apellidos)
    return nombre

def generar_id_unica():
    return str(random.randint(100000, 999999))

def setup_database():
    conn = sqlite3.connect('colegio.db')
    cursor = conn.cursor()

    # Crear tabla de usuarios si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL,
        contrasena TEXT NOT NULL,
        tipo_usuario TEXT
    )''')

    # Crear tabla de coordinadores si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS coordinadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL,
        contrasena TEXT NOT NULL
    )''')

    # Crear tabla de estudiantes si no existe, con columna para el estado de matrícula
    cursor.execute('''CREATE TABLE IF NOT EXISTS estudiantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identificacion TEXT NOT NULL,
        nombre TEXT NOT NULL,
        edad INTEGER NOT NULL,
        grado INTEGER NOT NULL,
        matricula_pagada BOOLEAN DEFAULT 0  -- 0 significa que no ha pagado, 1 que sí
    )''')

    # Crear tabla de profesores si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS profesores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL,
        contrasena TEXT NOT NULL,
        materia TEXT NOT NULL,
        nombre TEXT NOT NULL,
        grados TEXT,
        pago BOOLEAN DEFAULT 0  -- 0 significa que no ha sido pagado, 1 que sí
    )''')

    # Crear tabla de pagos si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_profesor INTEGER,
        monto REAL NOT NULL,
        FOREIGN KEY (id_profesor) REFERENCES profesores(id)
    )''')

    # Crear tabla de notas si no existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_estudiante INTEGER,
        id_profesor INTEGER,
        materia TEXT NOT NULL,
        nota REAL NOT NULL,
        FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id),
        FOREIGN KEY (id_profesor) REFERENCES profesores(id)
    )''')

    # Insertar un coordinador para pruebas
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, contrasena, tipo_usuario) VALUES ('coordinador', '1234', 'coordinador')")

    # Insertar profesores para pruebas
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, contrasena, tipo_usuario) VALUES ('camila', '1234', 'profesor')")
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, contrasena, tipo_usuario) VALUES ('juan', '1234', 'profesor')")
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, contrasena, tipo_usuario) VALUES ('brian', '1234', 'profesor')")
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, contrasena, tipo_usuario) VALUES ('david', '1234', 'profesor')")

    cursor.execute("INSERT OR IGNORE INTO profesores (usuario, contrasena, materia, nombre, grados) VALUES ('camila', '1234', 'Ingles', 'Camila', '6,7,8')")
    cursor.execute("INSERT OR IGNORE INTO profesores (usuario, contrasena, materia, nombre, grados) VALUES ('juan', '1234', 'Español', 'Juan', '6,7,8')")
    cursor.execute("INSERT OR IGNORE INTO profesores (usuario, contrasena, materia, nombre, grados) VALUES ('brian', '1234', 'Fisica', 'Brian', '6,7,8')")
    cursor.execute("INSERT OR IGNORE INTO profesores (usuario, contrasena, materia, nombre, grados) VALUES ('david', '1234', 'Ciencias', 'David', '6,7,8')")

    # Insertar estudiantes con el estado de matrícula sin pagar y notas iniciales
    for grado in [6, 7, 8]:
        for i in range(1, 26):
            if grado == 6:
                edad = 8 + i % 2
            elif grado == 7:
                edad = 9 + i % 2
            elif grado == 8:
                edad = 11 + i % 2

            identificacion = generar_id_unica()
            nombre = generar_nombre_aleatorio()

            while nombre in [row[0] for row in cursor.execute("SELECT nombre FROM estudiantes")]:
                nombre = generar_nombre_aleatorio()

            cursor.execute("INSERT OR IGNORE INTO estudiantes (identificacion, nombre, edad, grado, matricula_pagada) VALUES (?, ?, ?, ?, 0)",
                           (identificacion, nombre, edad, grado))

            # Insertar notas iniciales para cada estudiante y profesor
            for profesor in cursor.execute("SELECT id, materia, nombre FROM profesores"):
                cursor.execute("INSERT OR IGNORE INTO notas (id_estudiante, id_profesor, materia, nota) VALUES (?, ?, ?, ?)",
                               (identificacion, profesor[0], profesor[1], 0.0))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()