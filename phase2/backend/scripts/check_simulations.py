from app.core.database import SessionLocal
from app.models.simulation import SimulationRun, SimulatedTrigger

db = SessionLocal()
sims = db.query(SimulationRun).order_by(SimulationRun.id.desc()).all()
if not sims:
    print("No simulations found.")
else:
    latest = sims[0]
    print(f"LATEST SIMULATION: ID {latest.id} ({latest.status})")
    
    triggers = db.query(SimulatedTrigger).filter(SimulatedTrigger.simulation_id == latest.id).order_by(SimulatedTrigger.year).all()
    print("-" * 40)
    for t in triggers:
        print(f"{t.year}: {t.trigger_type} | Val: {t.validated}")
        if t.external_validation:
            print(f"  Ext: {t.external_validation}")
    print("-" * 40)
db.close()
