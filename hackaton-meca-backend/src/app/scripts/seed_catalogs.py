"""Script to seed basic operational catalogs for MECA."""

import logging
from datetime import date
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.catalogs import (
    Area,
    Cuenta,
    Financiador,
    FinanciadorGrupo,
    Gestion,
    Region,
    Rubro,
    TipoCambio,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed():
    db = SessionLocal()
    try:
        # 1. Regiones
        regiones_data = [
            ("LPZ", "La Paz"),
            ("SCZ", "Santa Cruz"),
            ("CBB", "Cochabamba"),
            ("NAC", "Nacional"),
        ]
        for code, name in regiones_data:
            existing = db.execute(select(Region).where(Region.code == code)).scalar_one_or_none()
            if not existing:
                db.add(Region(code=code, name=name))
        db.commit()

        # 2. Áreas
        areas_data = [
            ("Formación y Liderazgo", "Área académica y formación pedagógica"),
            ("Expansión e Impacto", "Crecimiento territorial e impacto social"),
            ("Dirección Ejecutiva", "Gobernanza y relaciones institucionales"),
            ("Operaciones y Finanzas", "Administración, logística y finanzas"),
        ]
        for name, desc in areas_data:
            existing = db.execute(select(Area).where(Area.name == name)).scalar_one_or_none()
            if not existing:
                db.add(Area(name=name, description=desc))
        db.commit()

        # 3. Financiador Grupos
        grupo_2026 = db.execute(
            select(FinanciadorGrupo).where(FinanciadorGrupo.code == "2026")
        ).scalar_one_or_none()
        if not grupo_2026:
            grupo_2026 = FinanciadorGrupo(code="2026", name="Convenios Gestión 2026")
            db.add(grupo_2026)
            db.commit()
            db.refresh(grupo_2026)

        # 4. Financiadores
        financiadores_data = [
            ("CATALYST 18", "CATALYST 18", "Fondo internacional de aceleración educativa", "BOB"),
            ("CEL", "CEL (Comunidad)", "Comunidad de Ex-alumnos y Liderazgo", "BOB"),
            ("KJCF", "KJCF (Fundación)", "Fundación para la Infancia y Juventud", "BOB"),
            ("RP", "Recursos Propios", "Ingresos propios y donaciones individuales", "BOB"),
        ]
        for code, name, desc, mon in financiadores_data:
            existing = db.execute(
                select(Financiador).where(Financiador.name == name)
            ).scalar_one_or_none()
            if not existing:
                db.add(
                    Financiador(
                        grupo_id=grupo_2026.id,
                        code=code,
                        name=name,
                        description=desc,
                        moneda=mon,
                    )
                )
        db.commit()

        # 5. Gestiones
        gestion_2026 = db.execute(select(Gestion).where(Gestion.year == 2026)).scalar_one_or_none()
        if not gestion_2026:
            gestion_2026 = Gestion(year=2026, is_closed=False, description="Gestión Fiscal 2026")
            db.add(gestion_2026)
            db.commit()

        # 6. Tipos de Cambio
        hoy = date(2026, 1, 1)
        tc_oficial = db.execute(
            select(TipoCambio).where(TipoCambio.fecha == hoy, TipoCambio.tipo == "oficial")
        ).scalar_one_or_none()
        if not tc_oficial:
            db.add(TipoCambio(fecha=hoy, tipo="oficial", rate=6.96))

        tc_mercado = db.execute(
            select(TipoCambio).where(TipoCambio.fecha == hoy, TipoCambio.tipo == "mercado")
        ).scalar_one_or_none()
        if not tc_mercado:
            db.add(TipoCambio(fecha=hoy, tipo="mercado", rate=7.20))
        db.commit()

        # 7. Rubros y Cuentas
        rubros_data = [
            ("5.1", "Recursos Humanos y Honorarios", [
                ("5.1.01", "Sueldos y Cargas Sociales Profesores"),
                ("5.1.02", "Honorarios Asesores Pedagógicos"),
            ]),
            ("5.2", "Capacitación y Eventos", [
                ("5.2.03", "Talleres Presenciales e Inducción"),
            ]),
            ("5.3", "Transporte y Viáticos", [
                ("5.3.01", "Pasajes Aéreos y Terrestres"),
            ]),
            ("5.4", "Tecnología e Infraestructura", [
                ("5.4.02", "Licencias de Software y Plataforma LMS"),
            ]),
            ("5.5", "Servicios Básicos y Legales", [
                ("5.5.01", "Gastos Notariales y Legal Registro"),
            ]),
        ]

        for rubro_code, rubro_name, cuentas_list in rubros_data:
            rubro = db.execute(
                select(Rubro).where(Rubro.code == rubro_code)
            ).scalar_one_or_none()
            if not rubro:
                rubro = Rubro(code=rubro_code, name=rubro_name)
                db.add(rubro)
                db.commit()
                db.refresh(rubro)

            for c_code, c_name in cuentas_list:
                cuenta = db.execute(
                    select(Cuenta).where(Cuenta.rubro_id == rubro.id, Cuenta.code == c_code)
                ).scalar_one_or_none()
                if not cuenta:
                    db.add(Cuenta(rubro_id=rubro.id, code=c_code, name=c_name))
        db.commit()

        logger.info("Catálogos sembrados exitosamente.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
