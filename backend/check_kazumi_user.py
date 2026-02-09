#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""kazumiユーザーの情報を確認"""
from database import SessionLocal
from models import User

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == "kazumi").first()
    if user:
        print(f"✅ kazumiユーザーが見つかりました")
        print(f"Username: {user.username}")
        print(f"Hashed password: {user.hashed_password}")
        print(f"Deleted flag: {user.deleted_flag}")
    else:
        print("❌ kazumiユーザーが見つかりません")
        print("\n登録されているユーザー:")
        users = db.query(User).all()
        for u in users:
            print(f"  - {u.username} (deleted: {u.deleted_flag})")
finally:
    db.close()
