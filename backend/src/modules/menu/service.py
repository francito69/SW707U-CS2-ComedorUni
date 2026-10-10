from datetime import date
from zoneinfo import ZoneInfo

import psycopg2
from fastapi import HTTPException, status

from ...shared.db import get_db_conn

LIMA_TZ = ZoneInfo("America/Lima")
VALID_TIPOS = {"DESAYUNO", "ALMUERZO", "CENA"}


def fecha_peru() -> date:
    from datetime import datetime
    return datetime.now(LIMA_TZ).date()


def _validate_comidas(comidas: list[dict]) -> None:
    if not comidas:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe enviar al menos una comida.")

    for item in comidas:
        tipo = str(item.get("tipo_comida", "")).upper()
        if tipo not in VALID_TIPOS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Tipo de comida inválido: {item.get('tipo_comida')}")


def _persist_menu(conn, fecha: date, comidas: list[dict]) -> None:
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        for item in comidas:
            tipo = str(item.get("tipo_comida", "")).upper()
            cur.execute(
                """
                INSERT INTO menu_dia (fecha, tipo_comida, energia_kcal, lipidos_g, proteinas_g, carbohidratos_g)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    fecha,
                    tipo,
                    item.get("energia_kcal"),
                    item.get("lipidos_g"),
                    item.get("proteinas_g"),
                    item.get("carbohidratos_g"),
                ),
            )
            menu_id = cur.fetchone()[0]
            for plato in item.get("platos", []):
                cur.execute(
                    "INSERT INTO menu_platos (menu_dia_id, nombre) VALUES (%s, %s)",
                    (menu_id, plato.get("nombre")),
                )
        conn.commit()


def create_menu_dia(fecha: date, comidas: list[dict]) -> list[dict]:
    _validate_comidas(comidas)
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM menu_dia WHERE fecha=%s)", (fecha,))
            exists = cur.fetchone()[0]
            if exists:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un menú para esta fecha.")

        _persist_menu(conn, fecha, comidas)
        return get_menu(fecha)
    except psycopg2.IntegrityError as exc:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al crear el menú del día.") from exc
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_menu_dia(fecha: date, comidas: list[dict]) -> list[dict]:
    _validate_comidas(comidas)
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM menu_dia WHERE fecha=%s)", (fecha,))
            exists = cur.fetchone()[0]
            if not exists:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe un menú para esta fecha.")

        with conn.cursor() as cur:
            cur.execute("BEGIN")
            cur.execute("DELETE FROM menu_platos WHERE menu_dia_id IN (SELECT id FROM menu_dia WHERE fecha=%s)", (fecha,))
            cur.execute("DELETE FROM menu_dia WHERE fecha=%s", (fecha,))
            for item in comidas:
                tipo = str(item.get("tipo_comida", "")).upper()
                cur.execute(
                    """
                    INSERT INTO menu_dia (fecha, tipo_comida, energia_kcal, lipidos_g, proteinas_g, carbohidratos_g)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (fecha, tipo, item.get("energia_kcal"), item.get("lipidos_g"), item.get("proteinas_g"), item.get("carbohidratos_g")),
                )
                cur.execute("SELECT id FROM menu_dia WHERE fecha=%s AND tipo_comida=%s", (fecha, tipo))
                menu_id = cur.fetchone()[0]
                for plato in item.get("platos", []):
                    cur.execute("INSERT INTO menu_platos (menu_dia_id, nombre) VALUES (%s, %s)", (menu_id, plato.get("nombre")))
            conn.commit()
        return get_menu(fecha)
    except psycopg2.IntegrityError as exc:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicto al actualizar el menú del día.") from exc
    except HTTPException:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_menu(fecha: date) -> list[dict]:
    """
    Retorna las comidas del día con sus platos y aporte nutricional.
    Ordenadas DESAYUNO → ALMUERZO → CENA.
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.id, m.tipo_comida,
                       m.energia_kcal, m.lipidos_g, m.proteinas_g, m.carbohidratos_g,
                       p.id, p.nombre
                FROM menu_dia m
                LEFT JOIN menu_platos p ON p.menu_dia_id = m.id
                WHERE m.fecha = %s
                ORDER BY
                    CASE m.tipo_comida
                        WHEN 'DESAYUNO' THEN 1
                        WHEN 'ALMUERZO' THEN 2
                        WHEN 'CENA'     THEN 3
                    END,
                    p.id ASC
                """,
                (fecha,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    # Agrupar platos por comida
    comidas: dict[int, dict] = {}
    for row in rows:
        menu_id, tipo, energia, lipidos, proteinas, carbohidratos, plato_id, plato_nombre = row
        if menu_id not in comidas:
            comidas[menu_id] = {
                "id": menu_id,
                "tipo_comida": tipo,
                "energia_kcal": float(energia) if energia else None,
                "lipidos_g": float(lipidos) if lipidos else None,
                "proteinas_g": float(proteinas) if proteinas else None,
                "carbohidratos_g": float(carbohidratos) if carbohidratos else None,
                "platos": [],
            }
        if plato_id:
            comidas[menu_id]["platos"].append({"id": plato_id, "nombre": plato_nombre})

    return list(comidas.values())
