#!/usr/bin/env python3
"""Script para insertar 8 servicios de demo en MySQL.

Idempotente: si ya existen servicios con el mismo título + proveedor, no duplica.
Diseñado para correrse una vez sobre la base MySQL real de Alwaysdata.
"""
import os
import sys
from datetime import datetime

# Cargar .env manualmente (same path as app)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

import pymysql

def get_db_config():
    return {
        'host': os.getenv('DB_HOST', 'mysql-moovacloud.alwaysdata.net'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'moovacloud'),
        'password': os.getenv('DB_PASSWORD', '$Mo0vaCl1nic//'),
        'db': os.getenv('DB_NAME', 'moovacloud_rapijob'),
        'charset': 'utf8mb4',
    }

def get_providers(cur):
    """Obtener usuarios con rol proveedor."""
    cur.execute("SELECT id, nombre, email, telefono, ciudad FROM usuarios WHERE rol = 'proveedor'")
    return cur.fetchall()

def get_categories(cur):
    """Obtener todas las categorías."""
    cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre")
    return cur.fetchall()

def services_exist(cur, titulo, proveedor_id):
    """Verificar si ya existe un servicio con ese título + proveedor."""
    cur.execute(
        "SELECT id FROM servicios WHERE titulo = %s AND proveedor_id = %s",
        [titulo, proveedor_id]
    )
    row = cur.fetchone()
    return row is not None

def insert_service(cur, titulo, descripcion, precio, ubicacion, categoria_id, proveedor_id):
    """Insertar un servicio."""
    cur.execute(
        "INSERT INTO servicios (proveedor_id, categoria_id, titulo, descripcion, precio, ubicacion) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        [proveedor_id, categoria_id, titulo, descripcion, precio, ubicacion]
    )

def main():
    config = get_db_config()
    conn = pymysql.connect(**config)
    cur = conn.cursor()

    providers = get_providers(cur)
    if not providers:
        print("❌ No hay usuarios con rol='proveedor'. Revisa init_passwords.py o la BD.")
        conn.close()
        return

    categories = get_categories(cur)
    if not categories:
        print("❌ No hay categorías en la BD.")
        conn.close()
        return

    # Mapeo de servicios: título, descripción, precio, ubicación, categoria_id, proveedor_id
    # 8 servicios distribuidos entre 5 categorías
    service_data = [
        # Electricista
        {"titulo": "Instalación eléctrica completa", "desc": "Proyecto eléctrico nuevo, tableros y cablado.", "precio": 180, "ubic": "Huancayo", "cat_key": "electricidad"},
        # Gasfitero
        {"titulo": "Reparación de fugas y grifos", "desc": "Atención urgente para fugas de agua y cambio de accesorios.", "precio": 85, "ubic": "El Tambo", "cat_key": "fontaneria"},
        # Técnico de computadoras
        {"titulo": "Formato y recuperación de sistema", "desc": "Formateo, instalación de SO y recuperación de datos.", "precio": 120, "ubic": "Huancayo", "cat_key": "computación"},
        # Pintura
        {"titulo": "Pintura interior y exterior", "desc": "Preparación de superficies y pintura en paredes y techos.", "precio": 150, "ubic": "Chilca", "cat_key": "pintura"},
        # Carpintería
        {"titulo": "Muebles a medida y reparación", "desc": "Construcción y reparación de muebles de madera y MDF.", "precio": 200, "ubic": "Huancayo", "cat_key": "carpintería"},
        # Electricista (otro)
        {"titulo": "Mantenimiento preventivo eléctrico", "desc": "Revisión de instalaciones, interruptores y circuitos.", "precio": 100, "ubic": "El Tambo", "cat_key": "electricidad"},
        # Fontanería avanzada
        {"titulo": "Instalación de caldera y calefacción", "desc": "Sustitución y mantenimiento de sistemas de calefacción.", "precio": 250, "ubic": "Chilca", "cat_key": "fontaneria"},
        # Técnico general
        {"titulo": "Diagnóstico y reparación de electrodomésticos", "desc": "Reparación de lavadoras, secadoras y neveras.", "precio": 95, "ubic": "Huancayo", "cat_key": "computación"},
    ]

    # Nombre categoría por clave (usamos los nombres reales del seed)
    cat_map = {c[1].lower(): c[0] for c in categories}  # id a partir del nombre

    services_assigned = {p[0]: 0 for p in providers}  # contador por proveedor para rotar

    for s in service_data:
        cat_name = s["cat_key"]
        if cat_name not in cat_map:
            # fallback: toma la primera categoría
            cat_id = categories[0][0]
        else:
            cat_id = cat_map[cat_name]

        # Rotar entre proveedores
        prov_ids = [p[0] for p in providers]
        prov_idx = services_assigned[prov_ids[0]] % len(prov_ids)
        prov_id = prov_ids[prov_idx]
        services_assigned[prov_ids[0]] += 1

        titulo = s["titulo"]
        if not services_exist(cur, titulo, prov_id):
            insert_service(cur, titulo, s["desc"], s["precio"], s["ubic"], cat_id, prov_id)
            print(f"[OK] Insertado: {titulo} por proveedor ID {prov_id} (categoria {cat_id})")
        else:
            print(f"[WAIT] Ya existe: {titulo} por proveedor ID {prov_id}, skip.")

    conn.commit()
    # Contar total
    cur.execute("SELECT COUNT(*) FROM servicios")
    total = cur.fetchone()[0]
    print(f"\nTotal de servicios en la BD: {total}")

    cur.close()
    conn.close()
    print("Script finalizado.")

if __name__ == "__main__":
    main()