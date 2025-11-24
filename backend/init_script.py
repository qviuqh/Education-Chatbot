"""
Database Initialization Script
Chạy file này để tạo database và test data
"""
from sqlalchemy.orm import Session
from .db import engine, Base, SessionLocal
from .services.user_service import get_password_hash
from . import models


def init_database():
    """
    Tạo tất cả các bảng trong database
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def create_test_data():
    """
    Tạo dữ liệu test (optional)
    """
    db = SessionLocal()
    
    try:
        print("\nCreating test data...")
        
        # Kiểm tra xem đã có data chưa
        existing_user = db.query(models.User).first()
        if existing_user:
            print("⚠️  Test data already exists. Skipping...")
            return
        
        # Tạo test user
        test_user = models.User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User"
        )
        db.add(test_user)
        db.flush()
        
        print(f"✅ Created test user: {test_user.email}")
        
        # Tạo test subject
        test_subject = models.Subject(
            user_id=test_user.id,
            name="Toán học",
            description="Môn toán cơ bản"
        )
        db.add(test_subject)
        db.flush()
        
        print(f"✅ Created test subject: {test_subject.name}")
        
        db.commit()
        
        print("\n✅ Test data created successfully!")
        print("\nTest credentials:")
        print(f"  Email: {test_user.email}")
        print(f"  Password: password123")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()


def reset_database():
    """
    Xóa và tạo lại database (CẢNH BÁO: Mất hết dữ liệu!)
    """
    print("⚠️  WARNING: This will delete all data!")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    print("\nDropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")
    
    init_database()


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("Database Initialization Script")
    print("=" * 50)
    
    # Parse arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "reset":
            reset_database()
        elif command == "test":
            init_database()
            create_test_data()
        else:
            print(f"Unknown command: {command}")
            print("Available commands:")
            print("  python init_db.py        - Initialize database")
            print("  python init_db.py test   - Initialize with test data")
            print("  python init_db.py reset  - Reset database (delete all)")
    else:
        # Default: chỉ init
        init_database()
    
    print("\n" + "=" * 50)
    print("Done!")
    print("=" * 50)
