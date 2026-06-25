"""
Live verification — calls real HILMA API. Must exit 0 before deploying.
Run: python3 test_tools.py
"""
import asyncio, sys, traceback, time

from tools_hilma import (
    hae_hankintailmoitukset,
    get_hankintailmoitus,
    listaa_hankintayksikot,
    hae_cpv_koodit,
    hilma_tilastot,
)

results = []


def test(name: str, coro, *args, expected_min_chars=50, **kwargs):
    print(f"\n{'='*55}")
    print(f"TEST: {name}")
    t0 = time.time()
    try:
        result = asyncio.run(coro(*args, **kwargs))
        elapsed = time.time() - t0
        output = str(result) if not isinstance(result, str) else result
        size_kb = len(output.encode()) / 1024
        print(f"  Time: {elapsed:.1f}s | Size: {size_kb:.1f}KB")
        print(f"  Preview: {output[:300]}")
        if elapsed > 20:
            raise TimeoutError(f"Tool took {elapsed:.1f}s (limit: 20s)")
        if size_kb > 20:
            print(f"  WARNING: Response is {size_kb:.1f}KB — check row cap")
        if len(output) < expected_min_chars:
            raise ValueError(f"Response too short: {len(output)} chars")
        results.append((name, True, None))
        print("  PASS")
    except Exception as e:
        elapsed = time.time() - t0
        traceback.print_exc()
        results.append((name, False, str(e)))
        print(f"  FAIL ({elapsed:.1f}s): {e}")


test("hae_hankintailmoitukset no filter",  hae_hankintailmoitukset)
test("hae_hankintailmoitukset keyword",    hae_hankintailmoitukset, "siivous")
test("get_hankintailmoitus known id",      get_hankintailmoitus, "EF-450")
test("listaa_hankintayksikot no filter",   listaa_hankintayksikot)
test("listaa_hankintayksikot keyword",     listaa_hankintayksikot, "Helsin")
test("hae_cpv_koodit keyword",             hae_cpv_koodit, "siivous")
test("hilma_tilastot",                     hilma_tilastot)

print(f"\n{'='*55}")
print("VERIFICATION SUMMARY")
for name, ok, err in results:
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {err}" if err else ""))

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n{passed}/{len(results)} passed")

if passed < len(results):
    print("\nNOT DONE — fix failing tools and re-run")
    sys.exit(1)
else:
    print("\nALL PASSED — server ready for Intric")
    sys.exit(0)
