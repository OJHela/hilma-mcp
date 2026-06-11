"""
Generoi JWT-token Intricin API Key -kenttään.
Käyttö: python3 generate_token.py
"""
import datetime
import os

import jwt
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv("MCP_SERVER_JWT_SECRET")
issuer = os.getenv("MCP_SERVER_JWT_ISSUER", "")
audience = os.getenv("MCP_SERVER_JWT_AUDIENCE", "")

if not secret:
    print("Virhe: MCP_SERVER_JWT_SECRET puuttuu .env-tiedostosta")
    print("Kopioi .env.example → .env ja aseta avain (min 32 merkkiä)")
    exit(1)

payload = {
    "sub": "intric-user",
    "iat": datetime.datetime.now(datetime.timezone.utc),
    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365),
}
if issuer:
    payload["iss"] = issuer
if audience:
    payload["aud"] = audience

token = jwt.encode(payload, secret, algorithm="HS256")

print("Lisää tämä token Intricin Api Key -kenttään:")
print(token)
