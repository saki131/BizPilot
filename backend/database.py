from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")

# Neon接続の最適化：接続プール設定とタイムアウトを改善
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 接続前に疎通確認（古い接続を自動再接続）
    pool_size=5,         # 接続プールサイズ（小さめに設定）
    max_overflow=10,     # プールが満杯時の追加接続数
    pool_recycle=3600,   # 1時間ごとに接続を再作成（Neonのタイムアウト対策）
    connect_args={
        "connect_timeout": 30,        # 接続タイムアウトを30秒に延長
        "keepalives": 1,              # TCPキープアライブを有効化
        "keepalives_idle": 30,        # アイドル30秒後にキープアライブ開始
        "keepalives_interval": 10,    # 10秒ごとにキープアライブパケット送信
        "keepalives_count": 5,        # 5回失敗したら接続を切断
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()