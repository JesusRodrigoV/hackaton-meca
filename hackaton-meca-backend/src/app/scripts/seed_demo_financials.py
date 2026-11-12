"""Script to seed initial demo budgets and movements for MECA."""

import hashlib
import logging
from datetime import date
from decimal import Decimal
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.catalogs import Area, Cuenta, Financiador, Gestion, Region, Rubro
from app.models.presupuestos import Presupuesto, PresupuestoModificacion
from app.models.movimientos import Movimiento

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed():
    db = SessionLocal()
    try:
        gestion = db.execute(select(Gestion).where(Gestion.year == 2026)).scalar_one()
        reg_lpz = db.execute(select(Region).where(Region.code == "LPZ")).scalar_one()
        reg_scz = db.execute(select(Region).where(Region.code == "SCZ")).scalar_one()
        reg_cbb = db.execute(select(Region).where(Region.code == "CBB")).scalar_one()
        reg_nac = db.execute(select(Region).where(Region.code == "NAC")).scalar_one()

        area_for = db.execute(select(Area).where(Area.name == "Formación y Liderazgo")).scalar_one()
        area_exp = db.execute(select(Area).where(Area.name == "Expansión e Impacto")).scalar_one()
        area_dir = db.execute(select(Area).where(Area.name == "Dirección Ejecutiva")).scalar_one()
        area_ope = db.execute(select(Area).where(Area.name == "Operaciones y Finanzas")).scalar_one()

        fin_cat = db.execute(select(Financiador).where(Financiador.code == "CATALYST 18")).scalar_one()
        fin_cel = db.execute(select(Financiador).where(Financiador.code == "CEL")).scalar_one()
        fin_kjc = db.execute(select(Financiador).where(Financiador.code == "KJCF")).scalar_one()

        cta_5101 = db.execute(select(Cuenta).where(Cuenta.code == "5.1.01")).scalar_one()
        cta_5102 = db.execute(select(Cuenta).where(Cuenta.code == "5.1.02")).scalar_one()
        cta_5203 = db.execute(select(Cuenta).where(Cuenta.code == "5.2.03")).scalar_one()
        cta_5301 = db.execute(select(Cuenta).where(Cuenta.code == "5.3.01")).scalar_one()
        cta_5402 = db.execute(select(Cuenta).where(Cuenta.code == "5.4.02")).scalar_one()
        cta_5501 = db.execute(select(Cuenta).where(Cuenta.code == "5.5.01")).scalar_one()

        # Seed Presupuestos
        items = [
            (gestion.id, reg_lpz.id, area_for.id, fin_cat.id, cta_5101.rubro_id, cta_5101.id, Decimal("280000.00"), "Sueldos"),
            (gestion.id, reg_scz.id, area_for.id, fin_cel.id, cta_5102.rubro_id, cta_5102.id, Decimal("120000.00"), "Honorarios"),
            (gestion.id, reg_cbb.id, area_exp.id, fin_kjc.id, cta_5203.rubro_id, cta_5203.id, Decimal("85000.00"), "Talleres"),
            (gestion.id, reg_nac.id, area_dir.id, fin_cat.id, cta_5301.rubro_id, cta_5301.id, Decimal("45000.00"), "Pasajes"),
            (gestion.id, reg_nac.id, area_ope.id, fin_cel.id, cta_5402.rubro_id, cta_5402.id, Decimal("32000.00"), "Software"),
        ]

        pres_created = []
        for g_id, r_id, a_id, f_id, ru_id, c_id, monto, linea in items:
            existing = db.execute(
                select(Presupuesto).where(
                    Presupuesto.gestion_id == g_id,
                    Presupuesto.region_id == r_id,
                    Presupuesto.area_id == a_id,
                    Presupuesto.financiador_id == f_id,
                    Presupuesto.cuenta_id == c_id,
                )
            ).scalar_one_or_none()
            if not existing:
                p = Presupuesto(
                    gestion_id=g_id,
                    region_id=r_id,
                    area_id=a_id,
                    financiador_id=f_id,
                    rubro_id=ru_id,
                    cuenta_id=c_id,
                    monto_original=monto,
                    amount_bob=monto,
                    amount_usd=round(monto / Decimal("6.96"), 2),
                    linea=linea,
                )
                db.add(p)
                db.flush()
                pres_created.append(p)
            else:
                pres_created.append(existing)
        db.commit()

        # Seed Presupuesto Modificaciones (Aprobadas)
        # 1. Ampliación de 20,000 en Sueldos
        p_sueldos = pres_created[0]
        mod_1 = db.execute(
            select(PresupuestoModificacion).where(PresupuestoModificacion.destino_presupuesto_id == p_sueldos.id)
        ).scalar_one_or_none()
        if not mod_1:
            db.add(
                PresupuestoModificacion(
                    gestion_id=gestion.id,
                    tipo="ampliacion",
                    destino_presupuesto_id=p_sueldos.id,
                    amount_bob=Decimal("20000.00"),
                    reason="Ajuste inflacionario planilla docente",
                    estado="aprobado",
                    aprobado_por=1,
                    aprobado_at=date(2026, 2, 1),
                )
            )

        # 2. Reducción de 15,000 en Honorarios
        p_honorarios = pres_created[1]
        mod_2 = db.execute(
            select(PresupuestoModificacion).where(PresupuestoModificacion.origen_presupuesto_id == p_honorarios.id)
        ).scalar_one_or_none()
        if not mod_2:
            db.add(
                PresupuestoModificacion(
                    gestion_id=gestion.id,
                    tipo="reduccion",
                    origen_presupuesto_id=p_honorarios.id,
                    amount_bob=Decimal("15000.00"),
                    reason="Reducción de horas consultores",
                    estado="aprobado",
                    aprobado_por=1,
                    aprobado_at=date(2026, 2, 15),
                )
            )

        # 3. Ampliación de 8,000 en Software
        p_software = pres_created[4]
        mod_3 = db.execute(
            select(PresupuestoModificacion).where(PresupuestoModificacion.destino_presupuesto_id == p_software.id)
        ).scalar_one_or_none()
        if not mod_3:
            db.add(
                PresupuestoModificacion(
                    gestion_id=gestion.id,
                    tipo="ampliacion",
                    destino_presupuesto_id=p_software.id,
                    amount_bob=Decimal("8000.00"),
                    reason="Licencias adicionales Zoom y LMS",
                    estado="aprobado",
                    aprobado_por=1,
                    aprobado_at=date(2026, 3, 1),
                )
            )
        db.commit()

        # Seed Movimientos (Ejecución real)
        movs = [
            (gestion.id, reg_lpz.id, area_for.id, fin_cat.id, cta_5101.rubro_id, cta_5101.id, 3, date(2026, 3, 15), "EGR-2026-00101", "Planilla Docente Marzo", Decimal("215450.00"), "Planilla mensual Sueldos"),
            (gestion.id, reg_scz.id, area_for.id, fin_cel.id, cta_5102.rubro_id, cta_5102.id, 3, date(2026, 3, 28), "EGR-2026-00341", "Consultora Educativa Andina SRL", Decimal("112300.00"), "Honorarios Asesores Pedagógicos"),
            (gestion.id, reg_cbb.id, area_exp.id, fin_kjc.id, cta_5203.rubro_id, cta_5203.id, 3, date(2026, 3, 25), "EGR-2026-00338", "Hotel Cochabamba Centro", Decimal("68400.00"), "Talleres Presenciales e Inducción"),
            (gestion.id, reg_nac.id, area_ope.id, fin_cel.id, cta_5402.rubro_id, cta_5402.id, 3, date(2026, 3, 10), "EGR-2026-00210", "Canvas / Instructure Inc.", Decimal("38900.00"), "Licencias Plataforma LMS"),
            # Gasto sin presupuesto (para mostrar alerta EJECUCION_SIN_PRESUPUESTO)
            (gestion.id, reg_lpz.id, area_dir.id, fin_kjc.id, cta_5501.rubro_id, cta_5501.id, 3, date(2026, 3, 5), "EGR-2026-00085", "Notaría de Fe Pública Nro 12", Decimal("4850.00"), "Gastos Notariales y Legal"),
        ]

        for g_id, r_id, a_id, f_id, ru_id, c_id, mes, f_fecha, comp, benef, monto_bob, conc in movs:
            row_hash = hashlib.sha256(f"{comp}_{monto_bob}_{f_fecha}".encode()).hexdigest()
            existing_mov = db.execute(select(Movimiento).where(Movimiento.row_hash == row_hash)).scalar_one_or_none()
            if not existing_mov:
                m = Movimiento(
                    gestion_id=g_id,
                    region_id=r_id,
                    area_id=a_id,
                    financiador_id=f_id,
                    rubro_id=ru_id,
                    cuenta_id=c_id,
                    month=mes,
                    voucher_date=f_fecha,
                    documento_ref=comp,
                    beneficiario=benef,
                    reference=conc,
                    debit_bob=monto_bob,
                    credit_bob=Decimal("0.00"),
                    exchange_rate=Decimal("6.96"),
                    debit_usd=round(monto_bob / Decimal("6.96"), 2),
                    credit_usd=Decimal("0.00"),
                    row_hash=row_hash,
                )
                db.add(m)
        db.commit()

        logger.info("Presupuestos y movimientos de demostración sembrados exitosamente.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
