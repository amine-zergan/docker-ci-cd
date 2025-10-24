#!/usr/bin/env python3
# create_admin_dotenv_minimal.py
"""
Minimal script:
- Loads MONGO_URL from .env
- Prompts only for email and password
- Hashes password with bcrypt
- Inserts or updates { email, password } in collection "users" of the DB provided in MONGO_URL
"""

import os
import sys
from getpass import getpass

from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt

# load .env from current working directory
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    print("❌ MONGO_URL not found in .env. Add it and retry.")
    sys.exit(1)

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    # force connection
    client.admin.command("ping")
except Exception as e:
    print("❌ Cannot connect to MongoDB:", e)
    sys.exit(1)

# determine target database from URI default database, else ask user (but you said it's already in MONGO_URL)
db = client.get_default_database()
if db is None:
    print("❌ No default database found in MONGO_URL. Please include the database in the URI (e.g. .../myappdb?authSource=admin).")
    sys.exit(1)

users = db["users"]

# prompt only for email and password
print("=== Create or update admin (only email + password) ===")
email = input("Email: ").strip()
if not email:
    print("❌ Email is required. Exiting.")
    sys.exit(1)

password = getpass("Password (hidden): ").strip()
if not password:
    print("❌ Password is required. Exiting.")
    sys.exit(1)

# hash the password
hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
hashed_str = hashed.decode("utf-8")

doc = {"email": email, "password": hashed_str,"role":"admin"}

existing = users.find_one({"email": email})
if existing:
    # update only the two fields (email stays same), keep only email+password as requested
    result = users.update_one({"email": email}, {"$set": doc})
    if result.modified_count > 0:
        print("✅ Existing user updated (password replaced).")
    else:
        # could be the same hash; still show user
        print("⚠️ Update executed but no document was modified (hash may be identical).")
    found = users.find_one({"email": email}, {"email": 1, "password": 1})
    print("\nDocument in DB (email + password-hash):")
    print(found)
else:
    inserted = users.insert_one(doc)
    print("✅ Admin created with _id:", inserted.inserted_id)
    found = users.find_one({"_id": inserted.inserted_id}, {"email": 1, "password": 1})
    print("\nDocument in DB (email + password-hash):")
    print(found)

client.close()
