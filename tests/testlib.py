"""Shared harness: serve fork/ locally and drive it with headless Chromium."""
import functools, http.server, socketserver, threading
from pathlib import Path

import os
FORK = Path(os.environ.get("TITRATE_SITE")
            or Path(__file__).resolve().parent.parent / "docs")
PORT = 8099
BASE = f"http://127.0.0.1:{PORT}/"


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(directory=None):
    h = functools.partial(_Quiet, directory=str(directory or FORK))
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


SEED_JS = """
async (records) => {
  const db = await new Promise((res, rej) => {
    const r = indexedDB.open('GLPalDB');
    r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
  });
  await new Promise((res, rej) => {
    const tx = db.transaction('medications', 'readwrite');
    const os = tx.objectStore('medications');
    records.forEach(x => os.put(x));
    tx.oncomplete = res; tx.onerror = () => rej(tx.error);
  });
  db.close();
  return true;
}
"""

DUMP_JS = """
async () => {
  const db = await new Promise((res, rej) => {
    const r = indexedDB.open('GLPalDB');
    r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
  });
  const out = {};
  for (const store of ['medications', 'weights']) {
    out[store] = await new Promise((res, rej) => {
      const rq = db.transaction(store, 'readonly').objectStore(store).getAll();
      rq.onsuccess = () => res(rq.result); rq.onerror = () => rej(rq.error);
    });
  }
  db.close();
  return out;
}
"""

CLEAR_JS = """
async () => {
  const db = await new Promise((res, rej) => {
    const r = indexedDB.open('GLPalDB');
    r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
  });
  await new Promise((res) => {
    const tx = db.transaction(['medications', 'weights'], 'readwrite');
    tx.objectStore('medications').clear();
    tx.objectStore('weights').clear();
    tx.oncomplete = res;
  });
  db.close();
  return true;
}
"""


def dose(date, medication, dose_mg, **extra):
    r = {"date": date, "medication": medication, "dose": dose_mg,
         "halfLifeHours": 168, "isManual": True, "time": "08:00"}
    r.update(extra)
    return r


def open_app(browser, seed=None, path=""):
    """New context, load the app, optionally seed, reload so the UI reflects it."""
    ctx = browser.new_context()
    pg = ctx.new_page()
    pg.goto(BASE + path, wait_until="networkidle")
    pg.wait_for_timeout(1500)
    if seed:
        pg.evaluate(SEED_JS, seed)
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(1800)
    return ctx, pg


def goto_doses(pg):
    pg.click("button:has-text('Doses')")
    pg.wait_for_timeout(1200)


def meds(pg):
    """Medication records, sorted for stable comparison."""
    d = pg.evaluate(DUMP_JS)
    return sorted(d["medications"], key=lambda r: (r["date"], r["medication"])), d["weights"]


class Report:
    def __init__(self):
        self.rows = []

    def check(self, case, desc, ok, detail=""):
        self.rows.append((case, desc, bool(ok), detail))
        print(f"  {'PASS' if ok else 'FAIL'}  {desc}" + (f"  [{detail}]" if detail else ""))
        return ok

    def summary(self):
        bad = [r for r in self.rows if not r[2]]
        print(f"\n{'=' * 62}\n{len(self.rows) - len(bad)}/{len(self.rows)} checks passed")
        for c, d, _, det in bad:
            print(f"  FAILED {c}: {d} {det}")
        return not bad
