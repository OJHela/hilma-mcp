"""
hilma_client.py – Client for HILMA public procurement portal (hankintailmoitukset.fi).

HILMA is Finland's official mandatory procurement notice channel, maintained by Hansel Oy.
All endpoints are public and require no authentication.

Endpoints (from embedded hilmaConfig on the website):
  Search notices:  https://www.hankintailmoitukset.fi/search/eformnotices
  Organisations:   https://www.hankintailmoitukset.fi/search/organisations
  CPV codes:       https://www.hankintailmoitukset.fi/search/cpv
  Statistics:      https://www.hankintailmoitukset.fi/statistics/NoticeStatistics
"""

import httpx

BASE_WEB = "https://www.hankintailmoitukset.fi"
SEARCH_URL = f"{BASE_WEB}/search/eformnotices"
ORGS_URL = f"{BASE_WEB}/search/organisations"
CPV_URL = f"{BASE_WEB}/search/cpv"
STATS_URL = f"{BASE_WEB}/statistics/NoticeStatistics"
NOTICE_BASE_URL = f"{BASE_WEB}/fi/notice"

MAIN_TYPE_MAP = {
    "ContractNotices": "Hankintailmoitus",
    "ContractAwardNotices": "Jälki-ilmoitus",
    "PriorInformationNotices": "Ennakkoilmoitus",
    "NationalNotices": "Kansallinen ilmoitus",
    "DesignContestNotices": "Suunnittelukilpailu",
    "ExAnteNotices": "Suorahankinta (Ex-ante)",
    "SocialAndOtherSpecificServices": "Sosiaali- ja erityispalvelut",
    "CorrigendumNotices": "Korrigendum",
}

PROCUREMENT_TYPE_MAP = {
    "services": "Palvelut",
    "supplies": "Tavarahankinnat",
    "works": "Rakennusurakka",
    "socialAndOtherSpecificServices": "Sosiaali- ja erityispalvelut",
    "concessions": "Käyttöoikeussopimus",
    "defence": "Puolustushankinta",
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MCP-Bot/1.0; HILMA)",
    "Accept": "application/json",
}


def _get(url: str, params: dict) -> dict:
    with httpx.Client(headers=_HEADERS, follow_redirects=True, timeout=30) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def search_notices(keyword: str = "", page: int = 1, page_size: int = 20) -> dict:
    """Search HILMA procurement notices. No authentication required."""
    params: dict = {"pageSize": page_size, "page": page}
    if keyword.strip():
        params["search"] = keyword.strip()
    return _get(SEARCH_URL, params)


def fetch_notice(notice_id: str) -> dict | None:
    """Fetch a single notice by exact ID (e.g. 'EF-450'). Returns None if not found."""
    nid = notice_id.strip()
    raw = _get(SEARCH_URL, {"$filter": f"id eq '{nid}'", "pageSize": 1})
    items = raw.get("value", [])
    return items[0] if items else None


def search_organisations(keyword: str = "", page_size: int = 200) -> dict:
    """Search HILMA registered contracting authorities. No authentication required."""
    params: dict = {"pageSize": page_size}
    if keyword.strip():
        params["search"] = keyword.strip()
    return _get(ORGS_URL, params)


def search_cpv(keyword: str = "", page_size: int = 100) -> dict:
    """Search CPV codes by keyword. No authentication required."""
    params: dict = {"pageSize": page_size}
    if keyword.strip():
        params["search"] = keyword.strip()
    return _get(CPV_URL, params)


def get_statistics() -> dict:
    """Get live procurement statistics. No authentication required."""
    return _get(STATS_URL, {})


def format_notice(n: dict) -> dict:
    """Normalize a notice search result into a clean dict."""
    main_type = n.get("mainType", "")
    proc_type = n.get("procurementTypeCode", "")
    notice_id = n.get("id", "")

    deadline = n.get("deadline") or n.get("tendersOrRequestsToParticipateDueDateTime") or ""
    if deadline:
        deadline = deadline[:10]

    return {
        "id": notice_id,
        "notice_number": n.get("noticeNumber", ""),
        "title": (
            n.get("titleFi") or n.get("titleSv") or n.get("titleEn")
            or n.get("projectTitle", "")
        ),
        "organization": (
            n.get("organisationNameFi") or n.get("organisationNameSv")
            or n.get("organisationName", "")
        ),
        "org_id": n.get("organisationNationalRegistrationNumber", ""),
        "org_nuts": n.get("organisationNutsCode", ""),
        "description": (
            n.get("descriptionFi") or n.get("descriptionSv")
            or n.get("projectShortDescription") or ""
        ),
        "date_published": (n.get("datePublished") or "")[:10],
        "deadline": deadline,
        "notice_type": MAIN_TYPE_MAP.get(main_type, main_type),
        "procurement_type": PROCUREMENT_TYPE_MAP.get(proc_type, proc_type),
        "cpv_codes": n.get("cpvCodes", ""),
        "nuts_codes": n.get("nutsCodes", ""),
        "is_eu": n.get("isEuProcurement", not n.get("isNationalProcurement", False)),
        "is_eforms": n.get("isEForms", False),
        "contract_value": n.get("noticeResultTotalAmount") or n.get("estimatedValue"),
        "currency": n.get("noticeResultTotalAmountCurrency") or n.get("currency", "EUR"),
        "lots": n.get("lots", []),
        "url": f"{NOTICE_BASE_URL}/{notice_id}",
        "ted_id": n.get("tedPublicationId", ""),
    }
