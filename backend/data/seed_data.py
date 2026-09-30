import hashlib
from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models.user import User, UserRole, WarningLevel
from backend.app.models.location import Building, Room
from backend.app.models.alert import Alert, AlertStatus, AlertPriority, EmergencyType, AlertStatusHistory

def get_password_hash(password: str) -> str:
    """Generate SHA-256 hash for student/admin demo passwords."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def seed_database():
    """Drop and recreate tables with realistic campus demo data."""
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already contains data. Skipping initial seeding.")
            return

        print("Seeding Buildings and Rooms...")
        # 1. Seed Buildings
        buildings_data = [
            {"code": "ENG-A", "name": "Engineering Block A", "description": "CSE & IT Departments, Computer Labs", "total_floors": 4},
            {"code": "ENG-B", "name": "Engineering Block B", "description": "ECE & Mechanical Departments, Robotics Lab", "total_floors": 4},
            {"code": "SCI-MAIN", "name": "Science & Humanities Block", "description": "Physics, Chemistry, Math Labs & Lecture Halls", "total_floors": 3},
            {"code": "LIB", "name": "Central Campus Library", "description": "Reading Halls, Digital Library, Study Pods", "total_floors": 2},
            {"code": "ADM", "name": "Administrative Building", "description": "Director Office, Dean, Registrar, Security Control Room", "total_floors": 3},
            {"code": "HST-BOYS", "name": "Boys Hostel Block", "description": "Student Residential Block 1", "total_floors": 5},
            {"code": "HST-GIRLS", "name": "Girls Hostel Block", "description": "Student Residential Block 2", "total_floors": 5},
        ]
        
        building_instances = {}
        for b_data in buildings_data:
            b = Building(**b_data)
            db.add(b)
            db.flush()
            building_instances[b.code] = b

        # 2. Seed Rooms
        rooms_data = [
            # Engineering Block A
            {"building_code": "ENG-A", "room_number": "101", "floor": 1, "wing": "East", "room_type": "Classroom"},
            {"building_code": "ENG-A", "room_number": "102", "floor": 1, "wing": "East", "room_type": "Classroom"},
            {"building_code": "ENG-A", "room_number": "LAB-1", "floor": 1, "wing": "West", "room_type": "Computer Lab"},
            {"building_code": "ENG-A", "room_number": "201", "floor": 2, "wing": "East", "room_type": "Seminar Hall"},
            {"building_code": "ENG-A", "room_number": "205", "floor": 2, "wing": "West", "room_type": "Faculty Room"},
            {"building_code": "ENG-A", "room_number": "301", "floor": 3, "wing": "East", "room_type": "IoT Lab"},
            {"building_code": "ENG-A", "room_number": "304", "floor": 3, "wing": "West", "room_type": "Project Lab"},

            # Engineering Block B
            {"building_code": "ENG-B", "room_number": "101", "floor": 1, "wing": "Main", "room_type": "Mechanics Lab"},
            {"building_code": "ENG-B", "room_number": "201", "floor": 2, "wing": "Main", "room_type": "Robotics Lab"},
            {"building_code": "ENG-B", "room_number": "301", "floor": 3, "wing": "Main", "room_type": "Classroom"},

            # Science Block
            {"building_code": "SCI-MAIN", "room_number": "G01", "floor": 0, "wing": "Ground", "room_type": "Physics Lab"},
            {"building_code": "SCI-MAIN", "room_number": "G02", "floor": 0, "wing": "Ground", "room_type": "Chemistry Lab"},
            {"building_code": "SCI-MAIN", "room_number": "101", "floor": 1, "wing": "North", "room_type": "Lecture Hall 1"},
            {"building_code": "SCI-MAIN", "room_number": "201", "floor": 2, "wing": "North", "room_type": "Math Department"},

            # Central Library
            {"building_code": "LIB", "room_number": "G-READING", "floor": 0, "wing": "Ground", "room_type": "General Reading Hall"},
            {"building_code": "LIB", "room_number": "101-DIGITAL", "floor": 1, "wing": "First", "room_type": "Digital Library"},

            # Admin Block
            {"building_code": "ADM", "room_number": "SEC-DESK", "floor": 0, "wing": "Main Gate", "room_type": "Security Control Room"},
            {"building_code": "ADM", "room_number": "MED-AID", "floor": 0, "wing": "Ground", "room_type": "Campus First Aid Center"},
            {"building_code": "ADM", "room_number": "DEAN-OFFICE", "floor": 1, "wing": "East", "room_type": "Dean Student Welfare"},

            # Hostels
            {"building_code": "HST-BOYS", "room_number": "B-COMMON", "floor": 0, "wing": "Ground", "room_type": "Common Hall"},
            {"building_code": "HST-BOYS", "room_number": "B-204", "floor": 2, "wing": "Block 1", "room_type": "Student Room"},
            {"building_code": "HST-GIRLS", "room_number": "G-COMMON", "floor": 0, "wing": "Ground", "room_type": "Common Hall"},
            {"building_code": "HST-GIRLS", "room_number": "G-305", "floor": 3, "wing": "Block 2", "room_type": "Student Room"},
        ]

        for r_data in rooms_data:
            building = building_instances[r_data["building_code"]]
            room = Room(
                building_id=building.id,
                room_number=r_data["room_number"],
                floor=r_data["floor"],
                wing=r_data["wing"],
                room_type=r_data["room_type"]
            )
            db.add(room)

        print("Seeding Users (Students, Security Desk Admins, HODs)...")
        # Default password is "emergency123" for demo
        default_pwd_hash = get_password_hash("emergency123")

        users_data = [
            # Students
            {"roll_number": "21CS001", "full_name": "Aarav Sharma", "email": "aarav.sharma@campus.edu", "phone": "+91-9876543210", "role": UserRole.STUDENT, "department": "Computer Science"},
            {"roll_number": "21CS042", "full_name": "Priya Patel", "email": "priya.patel@campus.edu", "phone": "+91-9876543211", "role": UserRole.STUDENT, "department": "Computer Science"},
            {"roll_number": "22EC015", "full_name": "Rohan Verma", "email": "rohan.verma@campus.edu", "phone": "+91-9876543212", "role": UserRole.STUDENT, "department": "Electronics"},
            {"roll_number": "22ME009", "full_name": "Vikram Singh", "email": "vikram.singh@campus.edu", "phone": "+91-9876543213", "role": UserRole.STUDENT, "department": "Mechanical"},
            {"roll_number": "23CV004", "full_name": "Ananya Sen", "email": "ananya.sen@campus.edu", "phone": "+91-9876543214", "role": UserRole.STUDENT, "department": "Civil"},

            # Security / Admins
            {"roll_number": "ADMIN01", "full_name": "Central Security Desk 1", "email": "security.desk1@campus.edu", "phone": "+91-9876500001", "role": UserRole.ADMIN, "department": "Campus Security"},
            {"roll_number": "ADMIN02", "full_name": "Chief Security Officer", "email": "cso@campus.edu", "phone": "+91-9876500002", "role": UserRole.ADMIN, "department": "Campus Security"},

            # Department HODs
            {"roll_number": "HOD_CSE", "full_name": "Dr. S. K. Raman (HOD CSE)", "email": "hod.cse@campus.edu", "phone": "+91-9876500010", "role": UserRole.HOD, "department": "Computer Science"},
            {"roll_number": "HOD_ECE", "full_name": "Dr. Meenakshi Iyer (HOD ECE)", "email": "hod.ece@campus.edu", "phone": "+91-9876500011", "role": UserRole.HOD, "department": "Electronics"},
        ]

        for u_data in users_data:
            user = User(
                roll_number=u_data["roll_number"],
                full_name=u_data["full_name"],
                email=u_data["email"],
                phone=u_data["phone"],
                hashed_password=default_pwd_hash,
                role=u_data["role"],
                department=u_data["department"],
                offense_count=0,
                warning_status=WarningLevel.NONE,
                is_active=True
            )
            db.add(user)

        db.commit()
        print("Database initialized and seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
