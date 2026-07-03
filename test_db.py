from src.shared.infrastructure.database import SessionLocal
from src.modules.telephony.models.phone_call import Employee

db = SessionLocal()
emp = db.query(Employee).filter(Employee.username == "eshernandez").first()
if emp:
    print(f"Found employee: {emp.id} - {emp.username}")
else:
    print("Employee NOT FOUND")
    
all_emps = db.query(Employee).limit(3).all()
print(f"Total found from query: {len(all_emps)}")
db.close()
