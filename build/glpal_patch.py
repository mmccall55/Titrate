#!/usr/bin/env python3
"""
Deterministic patcher for the GLPal deployed application bundle analyzed on 2026-08-13.

Expected input SHA-256:
  a561c9f0a86560313b7165758e131b3140807482ba140922035c810f0d7f5631

Expected output SHA-256:
  dbea7baaff958b56a4567c1a984c9b7a46ef696b792412bd1279e7433f75236e

Usage:
  python glpal_patch.py glpal-index.js glpal-index-editable.js

This patch intentionally refuses to run against a different upstream bundle.
If GLPal has changed, re-audit the new bundle rather than blindly applying
minified-code replacements.
"""

from pathlib import Path
import hashlib
import sys

EXPECTED_INPUT_SHA256 = "a561c9f0a86560313b7165758e131b3140807482ba140922035c810f0d7f5631"
EXPECTED_OUTPUT_SHA256 = "dbea7baaff958b56a4567c1a984c9b7a46ef696b792412bd1279e7433f75236e"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly one source match, found {count}. "
            "The upstream bundle probably changed."
        )
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python glpal_patch.py INPUT_JS OUTPUT_JS")

    src_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    raw = src_path.read_bytes()
    actual_in = sha256_bytes(raw)
    if actual_in != EXPECTED_INPUT_SHA256:
        raise RuntimeError(
            "Input bundle SHA-256 does not match the analyzed GLPal build.\n"
            f"Expected: {EXPECTED_INPUT_SHA256}\n"
            f"Actual:   {actual_in}"
        )

    text = raw.decode("utf-8")

    # 1. Fix broken dose deletion and add a transactional update primitive.
    text = replace_once(
        text,
        'xW=async r=>{await st.weights.delete(r)},Bc=async()=>Es()',
        'xW=async r=>{await st.medications.delete([r.date,r.medication])},'
        '__glpalUpdateDose=async(r,t)=>{await st.transaction("rw",st.medications,async()=>{'
        '(r.date!==t.date||r.medication!==t.medication)&&await st.medications.delete([r.date,r.medication]),'
        'await st.medications.put({...t,isManual:!0})})},Bc=async()=>Es()',
        "Fix deleteDose persistence + add update primitive",
    )

    # 2. Expose updateDose through the Zustand application store.
    text = replace_once(
        text,
        'addDose:async e=>{await Gf(e);const a=await Bc();r({dosesEntries:a})},'
        'deleteDose:async e=>{await xW(e);const a=await Bc();r({dosesEntries:a})}',
        'addDose:async e=>{await Gf(e);const a=await Bc();r({dosesEntries:a})},'
        'updateDose:async(e,a)=>{await __glpalUpdateDose(e,a);const n=await Bc();r({dosesEntries:n})},'
        'deleteDose:async e=>{await xW(e);const a=await Bc();r({dosesEntries:a})}',
        "Expose updateDose in store",
    )

    # 3. Insert the Edit Dose modal implementation.
    editor = '__glpalOpenDoseEditor=(r,t,e)=>{const a=document.createElement("div"),n=document.createElement("div"),i=document.createElement("div"),o=document.createElement("h2"),s=document.createElement("div"),l=(u,c,d="text")=>{const h=document.createElement("label"),v=document.createElement("span"),g=document.createElement(d==="select"?"select":"input");return v.textContent=u,v.style.cssText="display:block;font-size:12px;margin-bottom:4px;color:#c4b5d9",d==="select"?(g.innerHTML=\'<option value="">None</option><option>None</option><option>Mild</option><option>Moderate</option><option>Severe</option>\',g.value=c||""):(g.type=d,g.value=c??""),g.style.cssText="width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:1px solid #5b4d70;background:#181522;color:white;font-size:16px",h.style.cssText="display:block;margin-bottom:10px",h.append(v,g),s.appendChild(h),g};a.style.cssText="position:fixed;inset:0;z-index:100000;display:flex;align-items:center;justify-content:center;padding:16px",n.style.cssText="position:absolute;inset:0;background:rgba(0,0,0,.72);backdrop-filter:blur(6px)",i.style.cssText="position:relative;width:min(520px,100%);max-height:90vh;overflow:auto;background:#211c2d;color:white;border:1px solid #6d5a85;border-radius:16px;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.55)",o.textContent="Edit Dose",o.style.cssText="font-size:20px;font-weight:700;margin:0 0 16px",s.style.cssText="display:block";const u=l("Date",r.date,"date"),c=l("Time",r.time||"","time"),d=l("Medication",r.medication),h=l("Dose (mg)",r.dose,"number"),v=l("Pain level 0-10",r.painLevel??"","number"),g=l("Injection site",r.injectionSite||""),y=l("Injection-site reaction",r.isr||"","select"),x=document.createElement("label"),b=document.createElement("span"),w=document.createElement("textarea");b.textContent="Notes",b.style.cssText="display:block;font-size:12px;margin-bottom:4px;color:#c4b5d9",w.value=r.notes||"",w.rows=3,w.style.cssText="width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:1px solid #5b4d70;background:#181522;color:white;font-size:16px",x.style.cssText="display:block;margin-bottom:14px",x.append(b,w),s.appendChild(x);const D=document.createElement("div"),C=document.createElement("button"),T=document.createElement("button"),M=document.createElement("button");D.style.cssText="display:flex;gap:8px;flex-wrap:wrap",[C,T,M].forEach(N=>N.style.cssText="flex:1;min-width:90px;padding:11px;border-radius:9px;border:0;font-weight:600;font-size:14px;cursor:pointer"),C.textContent="Cancel",C.style.background="#3b3348",C.style.color="white",T.textContent="Delete",T.style.background="#7f1d1d",T.style.color="white",M.textContent="Save",M.style.background="#9C7BD3",M.style.color="white",D.append(C,T,M),i.append(o,s,D),a.append(n,i),document.body.appendChild(a);const N=()=>{a.remove(),document.body.classList.remove("modal-open")};document.body.classList.add("modal-open"),n.onclick=C.onclick=N,T.onclick=async()=>{window.confirm(`Delete ${r.medication} dose on ${r.date}?`)&&(T.disabled=!0,await e(r),N())},M.onclick=async()=>{const a=parseFloat(h.value),n=v.value===""?void 0:parseFloat(v.value);if(!u.value||!d.value.trim()||!Number.isFinite(a)||a<=0){window.alert("Date, medication, and a valid dose are required.");return}if(n!==void 0&&(!Number.isFinite(n)||n<0||n>10)){window.alert("Pain level must be between 0 and 10.");return}M.disabled=!0;const i={...r,date:u.value,medication:d.value.trim(),dose:a,time:c.value||void 0,painLevel:n,injectionSite:g.value.trim()||void 0,isr:y.value&&y.value!=="None"?y.value:void 0,notes:w.value.trim()||void 0,isManual:!0};try{await t(r,i),N()}catch(o){M.disabled=!1,window.alert("Could not save the edited dose: "+(o?.message||o))}}}'
    text = replace_once(
        text,
        'm0e=["Nausea","Vomiting","Diarrhea","Constipation","Abdominal Pain","Headache","Fatigue",'
        '"Dizziness","Loss of Appetite","Heartburn"],y0e=',
        'm0e=["Nausea","Vomiting","Diarrhea","Constipation","Abdominal Pain","Headache","Fatigue",'
        '"Dizziness","Loss of Appetite","Heartburn"],' + editor + ';const y0e=',
        "Insert Edit Dose modal",
    )

    # 4. Bind updateDose/deleteDose in the dose-history component.
    text = replace_once(
        text,
        'addWeight:P,deleteWeight:O,refreshWeights:R}=w1()',
        'addWeight:P,deleteWeight:O,refreshWeights:R,updateDose:GlpU,deleteDose:GlpD}=w1()',
        "Bind dose update/delete actions",
    )

    # 5. Fix side-effect/note editing so it targets date + medication, not date alone.
    text = replace_once(
        text,
        'const le=G.map(et=>et.date===V.date?{...et,sideEffects:Pr.length>0?Pr:void 0,notes:So||void 0}:et);',
        'const le=G.map(et=>et.date===V.date&&et.medication===V.medication?'
        '{...et,sideEffects:Pr.length>0?Pr:void 0,notes:So||void 0}:et);',
        "Fix side-effects record targeting",
    )

    # 6. Add the Edit button beside Side Effects / Notes.
    text = replace_once(
        text,
        'S.jsx("div",{className:"flex justify-end mt-2",children:S.jsx("button",{'
        'onClick:()=>zn(le),className:"px-3 py-1 text-xs rounded-lg transition-all duration-300 '
        'transform hover:scale-[1.02] bg-gradient-to-r from-[#B19CD9] to-[#9C7BD3] text-white '
        'shadow-[0_0_10px_rgba(177,156,217,0.4)]",children:"+ Side Effects / Notes"})})',
        'S.jsxs("div",{className:"flex justify-end gap-2 mt-2",children:['
        'S.jsx("button",{onClick:()=>zn(le),className:"px-3 py-1 text-xs rounded-lg transition-all '
        'duration-300 transform hover:scale-[1.02] bg-gradient-to-r from-[#B19CD9] to-[#9C7BD3] '
        'text-white shadow-[0_0_10px_rgba(177,156,217,0.4)]",children:"Side Effects / Notes"}),'
        'S.jsx("button",{onClick:()=>__glpalOpenDoseEditor(le,GlpU,GlpD),'
        'className:"px-3 py-1 text-xs rounded-lg transition-all duration-300 transform '
        'hover:scale-[1.02] bg-[#4ADEA8]/20 text-[#4ADEA8] border border-[#4ADEA8]/30",'
        'children:"Edit"})]})',
        "Add Edit button to dose history",
    )

    out = text.encode("utf-8")
    actual_out = sha256_bytes(out)
    if actual_out != EXPECTED_OUTPUT_SHA256:
        raise RuntimeError(
            "Patched output did not match the verified bundle.\n"
            f"Expected: {EXPECTED_OUTPUT_SHA256}\n"
            f"Actual:   {actual_out}"
        )

    out_path.write_bytes(out)
    print(f"Wrote {out_path}")
    print(f"SHA-256: {actual_out}")

if __name__ == "__main__":
    main()
