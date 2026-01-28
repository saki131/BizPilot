from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

password = "password123"
hashed = pwd_context.hash(password)
print(hashed)