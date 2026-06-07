from models.base import BaseModel
from database.connection import get_connection


class FuelType(BaseModel):
    TABLE = "fuel_types"

    @classmethod
    def create(cls, name, unit="Litre", hsn_code="", gst_rate=18):
        conn = get_connection()
        conn.execute(
            "INSERT INTO fuel_types (name, unit, hsn_code, gst_rate) VALUES (?,?,?,?)",
            (name, unit, hsn_code, gst_rate),
        )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id


class Tank(BaseModel):
    TABLE = "tanks"

    @classmethod
    def create(cls, name, fuel_type_id, capacity, current_level=0):
        conn = get_connection()
        conn.execute(
            "INSERT INTO tanks (name, fuel_type_id, capacity, current_level) VALUES (?,?,?,?)",
            (name, fuel_type_id, capacity, current_level),
        )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id

    @classmethod
    def get_with_fuel_type(cls):
        conn = get_connection()
        rows = conn.execute("""
            SELECT t.*, f.name as fuel_name, f.unit as fuel_unit
            FROM tanks t
            JOIN fuel_types f ON f.id = t.fuel_type_id
            ORDER BY t.name
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]


class Pump(BaseModel):
    TABLE = "pumps"

    @classmethod
    def create(cls, pump_no, tank_id, description=""):
        conn = get_connection()
        conn.execute(
            "INSERT INTO pumps (pump_no, tank_id, description) VALUES (?,?,?)",
            (pump_no, tank_id, description),
        )
        conn.commit()
        id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return id

    @classmethod
    def get_with_tank(cls):
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.*, t.name as tank_name, f.name as fuel_name
            FROM pumps p
            JOIN tanks t ON t.id = p.tank_id
            JOIN fuel_types f ON f.id = t.fuel_type_id
            ORDER BY p.pump_no
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
