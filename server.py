"""
server.py – HILMA MCP -palvelin (FastMCP, SSE-transport).

HILMA on Suomen virallinen julkisten hankintojen ilmoituskanava (Hansel Oy).
Käyttää HILMA:n julkisia JSON-rajapintoja ilman autentikointia.

Käyttö:
    python3 server.py                  → käynnistää palvelimen portissa 8000
    uvicorn server:app --port 8000     → tuotanto-ajotapa

Ympäristömuuttujat (.env):
    MCP_PORT        – portti (oletus 8000)
    MCP_HOST        – osoite (oletus 0.0.0.0)
    MCP_ALLOWED_IPS – sallitut IP:t pilkulla eroteltuina, tai * kaikille (oletus *)
"""

import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

load_dotenv()

from tools_hilma import (
    get_hankintailmoitus,
    hae_cpv_koodit,
    hae_hankintailmoitukset,
    hilma_tilastot,
    listaa_hankintayksikot,
)

####### CUSTOM MIDDLEWARE #######

class IPAllowlistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_ips: list[str]):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips)
        self.allow_all = "*" in self.allowed_ips

    async def dispatch(self, request, call_next):
        if self.allow_all:
            return await call_next(request)
        client_ip = request.client.host if request.client else None
        if client_ip not in self.allowed_ips:
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "your_ip": client_ip},
            )
        return await call_next(request)


ALLOWED_IPS = os.getenv("MCP_ALLOWED_IPS", "*").split(",")
middleware = [Middleware(IPAllowlistMiddleware, allowed_ips=ALLOWED_IPS)]

####### SERVER METADATA #######

INSTRUCTION_STRING = """HILMA – Suomen virallinen julkisten hankintojen ilmoituskanava (hankintailmoitukset.fi).

HILMA:ssa julkaistaan kaikki Suomen kansalliset ja EU-kynnysarvon ylittävät hankinnat.
Palvelua ylläpitää Hansel Oy. Rajapinta on julkinen, maksuton eikä vaadi autentikointia.

TYÖKALUT:
  hae_hankintailmoitukset(hakusana)     → Hae ilmoituksia vapaahaulla
  get_hankintailmoitus(id)              → Hae yksittäisen ilmoituksen täydet tiedot
  listaa_hankintayksikot(hakusana)      → Listaa hankintayksiköt (organisaatiot)
  hae_cpv_koodit(hakusana)              → Hae CPV-koodeja kategorian nimellä
  hilma_tilastot()                      → Reaaliaikaiset tilastot (uudet, avoimet)

SUOSITELTU TYÖNKULKU:
  1. hae_hankintailmoitukset("hakusana")  → löydä kiinnostavat ilmoitukset ja niiden ID:t
  2. get_hankintailmoitus("EF-450")       → lue yksityiskohtainen kuvaus, ehdot, osa-alueet

ILMOITUSTYYPIT:
  Hankintailmoitus   – avoin kilpailutus (tärkein tyyppi)
  Ennakkoilmoitus    – tuleva kilpailutus, ei vielä deadline
  Jälki-ilmoitus     – kilpailutuksen tulos (voittaja + hinta)
  Kansallinen        – alle EU-kynnysarvon, vain Suomessa
  Suorahankinta      – suorahankintailmoitus (Ex-ante)

CPV-KOODIT:
  Hankintailmoituksissa käytetään CPV-koodeja kategorisointiin.
  Etsi koodit: hae_cpv_koodit("siivous") → CPV-numero → käytä hakusanana

HUOMIOITA:
  • Ilmoitus-ID: "EF-" = eForms (2023–), "OLD-" tai numero = vanha formaatti
  • EU-kynnysarvo (tavarat/palvelut): 140 000 € (viranomaiset) / 215 000 € (muut)
  • EU-kynnysarvo (rakennusurakka): 5 382 000 €
  • Kaikki hinnat euroissa (EUR)

Datalähde: hankintailmoitukset.fi | Ylläpitäjä: Hansel Oy | Lisenssi: avoin data"""

VERSION = "1.0.0"

####### SERVER CONFIGURATION #######

mcp = FastMCP(
    name="HILMA – Julkiset hankinnat",
    instructions=INSTRUCTION_STRING,
    version=VERSION,
)

####### TOOLS #######

mcp.tool(meta={"requires_permission": False})(hae_hankintailmoitukset)
mcp.tool(meta={"requires_permission": False})(get_hankintailmoitus)
mcp.tool(meta={"requires_permission": False})(listaa_hankintayksikot)
mcp.tool(meta={"requires_permission": False})(hae_cpv_koodit)
mcp.tool(meta={"requires_permission": False})(hilma_tilastot)

####### CUSTOM ROUTES #######

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

####### RUNNING THE SERVER #######
# Run with: uvicorn server:app --host 0.0.0.0 --port 8000
app = mcp.http_app(middleware=middleware)

if __name__ == "__main__":
    import sys

    if "--stdio" in sys.argv:
        mcp.run(transport="stdio")
    else:
        import uvicorn
        port = int(os.getenv("MCP_PORT", "8000"))
        host = os.getenv("MCP_HOST", "0.0.0.0")
        print(f"Käynnistetään HILMA MCP -palvelin osoitteessa {host}:{port}/mcp")
        uvicorn.run(app, host=host, port=port)
