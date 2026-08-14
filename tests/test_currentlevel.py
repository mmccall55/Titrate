#!/usr/bin/env python3
"""
Current-level marker on the dose chart (patch 13).

The marker is canvas-drawn, so this asserts on pixels, keying on its dark
label plate, which sits in a band nothing else draws into.

Single-medication is the case that matters: Vge returns

    [...(meds.length > 1 ? combined : []), ...perMed]

so the combined series is dropped entirely when only one medication is tracked.
A first attempt appended the marker to that dropped array and rendered nothing,
which this test would have caught.
"""
import sys
from datetime import date, timedelta
from io import BytesIO
from playwright.sync_api import sync_playwright
from PIL import Image

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from testlib import serve, BASE, Report  # noqa: E402

TODAY = date(2026, 8, 13)
PROFILE = {"id": 1, "unitSystem": "metric", "age": 35, "gender": "male",
           "height": 180, "activityLevel": 1.2, "goalWeight": 80}

SEED = """async (d) => {
  const db = await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
  await new Promise(r=>{const tx=db.transaction(['weights','medications','userProfile'],'readwrite');
    tx.objectStore('weights').clear(); tx.objectStore('medications').clear();
    d.w.forEach(x=>tx.objectStore('weights').put(x));
    d.m.forEach(x=>tx.objectStore('medications').put(x));
    tx.objectStore('userProfile').put(d.p); tx.oncomplete=r});
  db.close(); return true; }"""


def weights():
    return [{"date": str(TODAY - timedelta(days=i * 5)), "weight": round(95 - i * 0.4, 1)}
            for i in range(20)]


def doses(names):
    out = []
    for n, name in enumerate(names):
        out += [{"date": str(TODAY - timedelta(days=i * 7)), "medication": name,
                 "dose": 7.5 if n == 0 else 4.0, "halfLifeHours": 168,
                 "isManual": True, "time": "08:00"} for i in range(12)]
    return out


def plate_pixels(png_bytes):
    """
    Count dark label-plate pixels in the top band of the chart.

    The marker's label is rgba(0,0,0,0.9) and sits above the curve at today.
    Nothing else draws dark pixels up there - the axis labels and gridlines are
    pale grey - so this is a reliable presence check without depending on where
    today lands horizontally.
    """
    im = Image.open(BytesIO(png_bytes)).convert("RGB")
    w, h = im.size
    top = im.crop((0, 0, w, int(h * 0.25)))
    return sum(1 for px in top.getdata() if sum(px) < 250)


def main():
    srv = serve()
    rep = Report()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for label, meds in (("one medication", ["Tirzepatide"]),
                                ("two medications", ["Tirzepatide", "Retatrutide"])):
                print(f"\n{label}")
                ctx = b.new_context(viewport={"width": 900, "height": 1000}, device_scale_factor=2)
                pg = ctx.new_page()
                pg.goto(BASE, wait_until="networkidle")
                pg.wait_for_timeout(1500)
                pg.evaluate(SEED, {"w": weights(), "m": doses(meds), "p": PROFILE})
                pg.reload(wait_until="networkidle")
                pg.wait_for_timeout(3200)

                chart = pg.locator("div[_echarts_instance_]").nth(1)
                chart.scroll_into_view_if_needed()
                pg.wait_for_timeout(600)
                plate = plate_pixels(chart.screenshot())

                rep.check("LEVEL", f"{label}: current-level marker label is drawn",
                          plate > 800, f"{plate} plate px")
                rep.check("LEVEL", f"{label}: label is not clipped by the plot top",
                          plate > 1500, f"{plate} plate px")

                # the marker must disappear along with the data
                pg.evaluate("""async () => {
                  const db=await new Promise(r=>{const q=indexedDB.open('GLPalDB');q.onsuccess=()=>r(q.result)});
                  await new Promise(r=>{const tx=db.transaction('medications','readwrite');
                    tx.objectStore('medications').clear(); tx.oncomplete=r});
                  db.close(); }""")
                pg.reload(wait_until="networkidle")
                pg.wait_for_timeout(2500)
                rep.check("LEVEL", f"{label}: empty state when doses removed",
                          "No dose data yet" in pg.inner_text("body"))
                ctx.close()
            b.close()
    finally:
        srv.shutdown()
    return 0 if rep.summary() else 1


if __name__ == "__main__":
    sys.exit(main())
