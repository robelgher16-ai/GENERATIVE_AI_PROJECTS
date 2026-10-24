"""
Full API test.  Usage:
    python test_api.py                                  # tests http://localhost:8000
    python test_api.py https://your-api.onrender.com    # tests the deployed API
    python test_api.py http://localhost:8000 path/to/short_meeting.mp3

Env (optional): APP_API_KEY=<same value as on the server>
"""
import os
import sys
import time
import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
FILE = sys.argv[2] if len(sys.argv) > 2 else None
YOUTUBE = os.environ.get("TEST_YOUTUBE_URL", "")  # e.g. a SHORT video (2-3 minutes)
HEADERS = {"X-API-Key": os.environ["APP_API_KEY"]} if os.environ.get("APP_API_KEY") else {}

ok_count = fail_count = 0


def check(name, cond, extra=""):
    global ok_count, fail_count
    if cond:
        ok_count += 1
        print(f"  PASS  {name}")
    else:
        fail_count += 1
        print(f"  FAIL  {name}  {extra}")


def call(method, path, **kw):
    r = requests.request(method, BASE + path, headers=HEADERS, timeout=kw.pop("timeout", 120), **kw)
    return r


print(f"\nTesting {BASE}\n")

print("1) Health")
r = call("GET", "/health")
check("GET /health -> 200", r.status_code == 200, r.text)
h = r.json() if r.ok else {}
check("Gemini key is set on server", h.get("gemini_key_set") is True)

print("2) Security / validation")
if os.environ.get("APP_API_KEY"):
    bad = requests.get(BASE + "/reports/en", timeout=30)
    check("Request without API key is rejected (401)", bad.status_code == 401, str(bad.status_code))
check("Bad URL rejected (400)", call("POST", "/analyze/url", json={"url": "not-a-url"}).status_code == 400)
check("Unknown job -> 404", call("GET", "/jobs/doesnotexist").status_code == 404)
check("Empty question -> 400", call("POST", "/chat", json={"question": "  "}).status_code == 400)

print("3) Full pipeline")
job_id = None
if FILE:
    with open(FILE, "rb") as f:
        r = call("POST", "/analyze/upload", files={"file": (os.path.basename(FILE), f)}, timeout=600)
elif YOUTUBE:
    r = call("POST", "/analyze/url", json={"url": YOUTUBE})
else:
    r = None
    print("  SKIP  no file/URL given (pass a short audio file as 2nd argument, or set TEST_YOUTUBE_URL)")

if r is not None:
    check("Job accepted (200)", r.status_code == 200, r.text)
    if r.ok:
        job_id = r.json()["job_id"]
        print(f"  job_id = {job_id}")
        started = time.time()
        status = ""
        while time.time() - started < 3600:
            j = call("GET", f"/jobs/{job_id}").json()
            if j["status"] != status or True:
                status = j["status"]
                print(f"    ... {j['status']} | {j['step']}")
            if j["status"] in ("done", "failed"):
                break
            time.sleep(10)
        check("Job finished with status 'done'", j["status"] == "done", str(j.get("error")))

print("4) Results (needs a finished analysis)")
for path, label in [("/reports/en", "English report"), ("/reports/amh", "Amharic report"), ("/transcript", "Transcript")]:
    r = call("GET", path)
    if r.status_code == 404:
        print(f"  SKIP  {label} (not generated yet)")
    else:
        check(f"GET {path} -> 200", r.status_code == 200, r.text[:200])

print("5) Chat (English + Amharic)")
if call("GET", "/reports/en").status_code == 200:
    for q in ["Give me a short summary of the meeting.", "በስብሰባው ላይ ዋና ዋና ውሳኔዎች ምንድን ናቸው?"]:
        r = call("POST", "/chat", json={"question": q})
        check(f"Chat: {q[:35]}...", r.status_code == 200 and len(r.json().get("answer", "")) > 10, r.text[:200])
        if r.ok:
            print("     ->", r.json()["answer"][:150].replace("\n", " "))
else:
    print("  SKIP  no report yet")

print(f"\nResult: {ok_count} passed, {fail_count} failed")
sys.exit(1 if fail_count else 0)