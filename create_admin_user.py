from backend.database import SessionLocal, Usuario
from backend.auth import get_password_hash

def create_admin_user():
    db = SessionLocal()
    try:
        # Verificar se o usuário admin já existe
        admin_user = db.query(Usuario).filter(Usuario.username == "admin").first()
        if not admin_user:
            hashed_password = get_password_hash("admin123")
            admin_user = Usuario(username="admin", email="admin@example.com", hashed_password=hashed_password)
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("Usuário admin criado com sucesso!")
        else:
            print("Usuário admin já existe.")
    except Exception as e:
        print(f"Erro ao criar usuário admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()


