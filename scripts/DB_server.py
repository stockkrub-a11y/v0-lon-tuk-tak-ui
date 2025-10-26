from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ------------------------------------------------------
# ⚙️ Database connection settings
# ------------------------------------------------------
DB_USER = "postgres"       # postgres username
DB_PASSWORD = "maipai" # postgres password
DB_HOST = "localhost"      # server IP
DB_PORT = "5432"          # postgres port
DB_NAME = "postgres"     # our project database

# ------------------------------------------------------
# 🔗 Create SQLAlchemy Engine
# ------------------------------------------------------
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        now = conn.execute(text("SELECT NOW();")).fetchone()
        print(f"✅ Connected to Postgres, now: {now[0]}")
except Exception as e:
    print("❌ Database connection failed:", e)
    engine = None

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
