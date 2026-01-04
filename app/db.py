import os
from sqlalchemy import create_engine, Integer,  String, select
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    price_cents: Mapped[int] = mapped_column(Integer)

def init_db_and_seed():
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        existing = db.execute(select(Product.id).limit(1)).first()
        if existing:
            return
        db.add_all(
            [
                Product(id=1, name="Keyboard", price_cents=4999),
                Product(id=2, name="Mouse", price_cents=2999),
                Product(id=3, name="Monitor", price_cents=15999),
            ]
        )

        db.commit()