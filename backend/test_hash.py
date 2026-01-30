from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# From database
hash_from_db = "$2b$12$I8D0MamMYGYV4kA0DtYJ/.v/CGGDn9.4tDVIYU4pjxnAlzjJ8vUXG"
password = "password123"

print(f"Testing password verification:")
print(f"Password: {password}")
print(f"Hash: {hash_from_db}")
print(f"Hash length: {len(hash_from_db)}")

try:
    result = pwd_context.verify(password, hash_from_db)
    print(f"✓ Verification result: {result}")
except Exception as e:
    print(f"❌ Error: {e}")

# Generate a new hash for comparison
new_hash = pwd_context.hash(password)
print(f"\nNew hash: {new_hash}")
print(f"New hash length: {len(new_hash)}")
