"""Streamlit UI: Job Match and Skill Gap Analyzer (career intelligence dashboard)."""
import html
import math
import textwrap
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from extractor import CVExtractionError, extract_text
from matcher import SKILL_WEIGHT, TEXT_WEIGHT, analyze
from skills_db import CATEGORY_TIPS, SAMPLE_CV, SAMPLE_JD, SKILL_TO_CATEGORY

st.set_page_config(page_title="Job Match and Skill Gap Analyzer", page_icon=":material/target:", layout="wide")

# ---------------------------------------------------------------- design tokens
BG, NAVY, SURFACE2 = "#060B18", "#0B1530", "#13213F"
BORDER, BORDER2 = "rgba(120,170,210,.16)", "rgba(120,170,210,.30)"
GRID = "rgba(120,170,210,.14)"
TEXT, MUTED = "#EAF1FB", "#9AA9C2"
TEAL, CYAN, AMBER, BLUE = "#2DD4BF", "#22D3EE", "#F5B84B", "#6CB6FF"
RED, SLATE = AMBER, "#93A4C0"          # RED kept as an alias: "missing" uses warm amber for clear contrast with teal
CHIP = {"match": ("rgba(45,212,191,.14)", "#7CF0E0"), "miss": ("rgba(245,184,75,.14)", "#F9D48A"),
        "extra": ("rgba(108,182,255,.15)", "#A9D2FF")}
KIND = {"Matched": "match", "Missing": "miss", "Extra": "extra"}

# Inline icons (no extra dependencies)
_P = {
    "upload": "<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><path d='M17 8l-5-5-5 5'/><path d='M12 3v12'/>",
    "file": "<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><path d='M14 2v6h6'/><path d='M8 13h8M8 17h5'/>",
    "briefcase": "<rect x='2' y='7' width='20' height='14' rx='2'/><path d='M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16'/>",
    "check": "<path d='M22 11.1V12a10 10 0 1 1-5.9-9.1'/><path d='M22 4L12 14l-3-3'/>",
    "alert": "<path d='M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z'/><path d='M12 9v4M12 17h.01'/>",
    "layers": "<path d='M12 2L2 7l10 5 10-5z'/><path d='M2 17l10 5 10-5M2 12l10 5 10-5'/>",
    "target": "<circle cx='12' cy='12' r='10'/><circle cx='12' cy='12' r='6'/><circle cx='12' cy='12' r='2'/>",
    "compare": "<path d='M16 3h5v5'/><path d='M21 3l-7 7'/><path d='M8 21H3v-5'/><path d='M3 21l7-7'/>",
    "report": "<path d='M3 3v18h18'/><path d='M7 15l4-4 3 3 5-6'/>",
    "lock": "<rect x='3' y='11' width='18' height='11' rx='2'/><path d='M7 11V7a5 5 0 0 1 10 0v4'/>",
    "link": "<path d='M15 3h6v6'/><path d='M10 14L21 3'/><path d='M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6'/>",
    "info": "<circle cx='12' cy='12' r='10'/><path d='M12 16v-4M12 8h.01'/>",
    "download": "<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><path d='M7 10l5 5 5-5'/><path d='M12 15V3'/>",
    "table": "<rect x='3' y='3' width='18' height='18' rx='2'/><path d='M3 9h18M3 15h18M9 3v18'/>",
    "text": "<path d='M4 6h16M4 12h16M4 18h10'/>",
    "book": "<path d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'/><path d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z'/>",
    "sparkle": "<path d='M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z'/><path d='M19 3v4M21 5h-4'/>",
    "bulb": "<path d='M9 18h6M10 22h4'/><path d='M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z'/>",
    "route": "<circle cx='6' cy='19' r='3'/><path d='M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15'/><circle cx='18' cy='5' r='3'/>",
    "trend": "<path d='M22 7l-8.5 8.5-5-5L2 17'/><path d='M16 7h6v6'/>",
    "clock": "<circle cx='12' cy='12' r='10'/><path d='M12 6v6l4 2'/>",
    "cpu": "<rect x='4' y='4' width='16' height='16' rx='2'/><rect x='9' y='9' width='6' height='6'/><path d='M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3'/>",
    "award": "<circle cx='12' cy='8' r='6'/><path d='M15.5 13.9L17 23l-5-3-5 3 1.5-9.1'/>",
}


def icon(name, size=20):
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
            f"stroke-linecap='round' stroke-linejoin='round' aria-hidden='true' focusable='false'>{_P[name]}</svg>")


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');

/* ============ base ============ */
html{font-size:17.6px}
.stApp{background:
 radial-gradient(1000px 520px at 8% -10%,rgba(45,212,191,.16),transparent 60%),
 radial-gradient(900px 480px at 100% 0%,rgba(34,211,238,.10),transparent 58%),
 radial-gradient(800px 600px at 50% 115%,rgba(30,64,140,.18),transparent 60%),var(--bg);
 background-attachment:fixed;color:var(--text)}
.stApp,.stApp li,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stCaptionContainer"]{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp .hero .h1,.stApp .kv,.stApp .sec-h .st,.stApp .ring-v,.stApp .ct,.stApp .ph-t,
.stApp .rn2,.stApp .brand-n,.stApp .ins-t{font-family:'Poppins','Inter',sans-serif!important;letter-spacing:-.01em}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1200px;padding:3rem 1.5rem 4rem}
.stApp p,.stApp li{font-size:1rem;line-height:1.6}
.grad{background:linear-gradient(90deg,#7CF0E0,#22D3EE 70%);-webkit-background-clip:text;background-clip:text;
 -webkit-text-fill-color:transparent;color:#5EEAD4}
:focus-visible{outline:2px solid var(--cyan)!important;outline-offset:2px;border-radius:8px}
::selection{background:rgba(34,211,238,.32)}

/* ============ glass surfaces ============ */
[class*="st-key-card"],.dcard,.stat,.lp,.rnode,.ins,.proc,.donebar,.fstep{
 background:linear-gradient(150deg,rgba(24,40,74,.62),rgba(11,21,44,.58));
 border:1px solid var(--border);-webkit-backdrop-filter:blur(16px) saturate(140%);backdrop-filter:blur(16px) saturate(140%);
 box-shadow:0 12px 36px rgba(2,6,16,.38),inset 0 1px 0 rgba(255,255,255,.05)}
[class*="st-key-card"],.dcard{border-radius:20px}
[class*="st-key-card"]{padding:22px 24px;transition:border-color .2s,box-shadow .2s,transform .2s}
[class*="st-key-card"]:hover,.dcard:hover{border-color:var(--border2);box-shadow:0 16px 44px rgba(2,6,16,.45),0 0 0 1px rgba(45,212,191,.06),inset 0 1px 0 rgba(255,255,255,.06)}
.card-h{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.card-h .ic{flex:none;width:40px;height:40px;border-radius:12px;display:grid;place-items:center;color:var(--teal);
 background:linear-gradient(145deg,rgba(45,212,191,.20),rgba(34,211,238,.08));border:1px solid rgba(45,212,191,.30)}
.card-h .ct{font-weight:600;font-size:1.05rem;color:var(--text);line-height:1.25}
.card-h .cs{font-size:.84rem;color:var(--muted)}
.card-h .cr{margin-left:auto;font-size:.78rem;color:var(--muted);border:1px solid var(--border);border-radius:999px;padding:3px 10px;white-space:nowrap}
.hint{font-size:.84rem;color:var(--muted);margin-top:8px;line-height:1.5}
[data-testid="stMain"] [data-testid="stHorizontalBlock"]:has([class*="st-key-card"]){align-items:stretch}
[data-testid="stMain"] [data-testid="stColumn"]:has([class*="st-key-card"]){display:flex;flex-direction:column}
[data-testid="stMain"] [data-testid="stColumn"]:has([class*="st-key-card"])>[data-testid="stVerticalBlock"]{flex:1 1 auto}
[data-testid="stMain"] [data-testid="stColumn"]>[data-testid="stVerticalBlock"]>[data-testid="stLayoutWrapper"]:has([class*="st-key-card"]),
[data-testid="stMain"] [data-testid="stColumn"]>[data-testid="stVerticalBlock"]>[data-testid="stElementContainer"]:has([class*="st-key-card"]){flex:1 1 auto}
[data-testid="stMain"] [data-testid="stColumn"] [class*="st-key-card"]{flex:1 1 auto;align-self:stretch}

/* ============ sidebar ============ */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0A1430 0%,#070E22 100%);border-right:1px solid var(--border)}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:.5rem}
.sb-brand{display:flex;align-items:center;gap:12px;padding:6px 2px 18px;border-bottom:1px solid var(--border);margin-bottom:16px}
.sb-brand .logo{width:42px;height:42px;border-radius:13px}
.sb-t{font-family:'Poppins',sans-serif;font-weight:600;font-size:1.05rem;line-height:1.2;color:var(--text)}
.sb-s{font-size:.76rem;color:var(--muted);letter-spacing:.02em}
.sb-h{font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600;margin:14px 0 8px}
.ws{display:flex;flex-direction:column;gap:6px}
.ws-i{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:12px;background:rgba(255,255,255,.025);border:1px solid var(--border);font-size:.86rem;color:var(--muted)}
.ws-i b{font-weight:600;color:var(--text)}
.ws-i .dot{flex:none;width:9px;height:9px;border-radius:50%;background:#3A4A6B}
.ws-i.on{border-color:rgba(45,212,191,.35);background:rgba(45,212,191,.06)}
.ws-i.on .dot{background:var(--teal);box-shadow:0 0 10px var(--teal)}
.ws-i .v{margin-left:auto;font-size:.76rem;color:var(--muted);max-width:50%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ws-i.on .v{color:#7CF0E0}
[data-testid="stSidebar"] [data-testid="stExpander"]{background:rgba(255,255,255,.02)}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]{justify-content:flex-start}
[data-testid="stSidebar"] p{font-size:.9rem}

/* ============ top bar + hero ============ */
.topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 16px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:11px;font-weight:600;color:var(--text)}
.logo{width:36px;height:36px;border-radius:11px;display:grid;place-items:center;color:#04231F;
 background:linear-gradient(135deg,#7CF0E0,var(--teal) 55%,var(--cyan));box-shadow:0 8px 22px rgba(34,211,238,.30)}
.brand-n{font-size:1.02rem}.brand-n span{color:var(--muted);font-weight:500}
.pills{display:flex;gap:8px;flex-wrap:wrap}
.pill{display:inline-flex;align-items:center;gap:8px;font-size:.78rem;color:var(--muted);background:rgba(14,26,51,.7);
 border:1px solid var(--border);border-radius:999px;padding:6px 13px;-webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}
.pill svg{color:var(--teal)}
.live{width:8px;height:8px;border-radius:50%;background:var(--teal);box-shadow:0 0 0 0 rgba(45,212,191,.6);animation:pulse 2.2s infinite}
@keyframes pulse{70%{box-shadow:0 0 0 8px rgba(45,212,191,0)}100%{box-shadow:0 0 0 0 rgba(45,212,191,0)}}
.hero{background:linear-gradient(135deg,rgba(26,46,86,.75),rgba(9,18,40,.7) 60%);border:1px solid var(--border2);border-radius:24px;
 padding:34px 36px 28px;margin-bottom:24px;position:relative;overflow:hidden;box-shadow:0 18px 50px rgba(2,6,16,.5),inset 0 1px 0 rgba(255,255,255,.07)}
.hero::before{content:"";position:absolute;inset:0;pointer-events:none;opacity:.5;
 background-image:linear-gradient(rgba(120,170,210,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(120,170,210,.07) 1px,transparent 1px);
 background-size:38px 38px;-webkit-mask-image:radial-gradient(ellipse at 85% 0%,#000,transparent 70%);mask-image:radial-gradient(ellipse at 85% 0%,#000,transparent 70%)}
.hero::after{content:"";position:absolute;right:-110px;top:-120px;width:380px;height:380px;border-radius:50%;pointer-events:none;
 background:radial-gradient(circle,rgba(34,211,238,.26),rgba(45,212,191,.10) 45%,transparent 70%);animation:drift 9s ease-in-out infinite alternate}
@keyframes drift{to{transform:translate(-30px,24px) scale(1.08)}}
.hero>*{position:relative;z-index:1}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:#7CF0E0;font-weight:600;
 margin-bottom:12px;background:rgba(45,212,191,.10);border:1px solid rgba(45,212,191,.28);border-radius:999px;padding:5px 12px}
.hero .h1{color:var(--text);font-size:2.6rem;font-weight:700;line-height:1.12;margin:0 0 12px}
.hero .sub{color:var(--muted);font-size:1.06rem;line-height:1.6;max-width:720px;margin-bottom:18px}
.tags{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px}
.tag{font-size:.78rem;color:#B6C4DC;border:1px solid var(--border);background:rgba(255,255,255,.03);border-radius:8px;padding:4px 10px}
.flow{display:flex;align-items:center;gap:10px}
.fstep{flex:1 1 0;display:flex;align-items:center;gap:12px;border-radius:16px;padding:12px 14px;min-width:0;transition:border-color .2s,transform .2s}
.fstep:hover{transform:translateY(-2px);border-color:var(--border2)}
.fi{flex:none;width:40px;height:40px;border-radius:12px;display:grid;place-items:center;background:rgba(255,255,255,.04);color:var(--muted);border:1px solid var(--border)}
.ft{font-size:.92rem;font-weight:600;color:var(--text)}
.fs{font-size:.8rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fline{flex:0 0 22px;height:2px;background:linear-gradient(90deg,var(--border2),rgba(45,212,191,.4));border-radius:2px}
.fstep.active{border-color:rgba(34,211,238,.6);box-shadow:0 0 0 3px rgba(34,211,238,.10),0 12px 36px rgba(2,6,16,.38)}
.fstep.active .fi{color:var(--cyan);border-color:rgba(34,211,238,.55);background:rgba(34,211,238,.10)}
.fstep.done{border-color:rgba(45,212,191,.4)}
.fstep.done .fi{background:linear-gradient(135deg,#5EEAD4,var(--teal));color:#04231F;border-color:transparent}
.fstep.done .fs{color:#7CF0E0}
.fstep>div:last-child{min-width:0}

/* ============ form fields ============ */
.stApp [data-testid="stWidgetLabel"] p{font-size:.9rem!important;font-weight:500;color:#C9D5EA}
[data-baseweb="input"],[data-baseweb="textarea"]{background:rgba(6,12,28,.7)!important;border:1px solid var(--border2)!important;
 border-radius:12px!important;transition:border-color .15s,box-shadow .15s}
[data-baseweb="base-input"]{background:transparent!important}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within{border-color:var(--cyan)!important;box-shadow:0 0 0 3px rgba(34,211,238,.20)}
.stApp input,.stApp textarea{font-size:.98rem!important;color:var(--text)!important}
.stApp textarea::placeholder,.stApp input::placeholder{color:#7686A3!important;opacity:1}
[data-baseweb="select"]>div{background:rgba(6,12,28,.7)!important;border-color:var(--border2)!important;border-radius:12px!important}
[data-baseweb="tag"]{background:rgba(45,212,191,.16)!important;color:#7CF0E0!important;border-radius:8px!important}

/* ============ file uploader ============ */
[data-testid="stFileUploaderDropzone"]{background:rgba(45,212,191,.04);border:1.5px dashed rgba(45,212,191,.5);
 border-radius:18px;padding:26px 18px;transition:background .2s,border-color .2s,box-shadow .2s}
[data-testid="stFileUploaderDropzone"]:hover{background:rgba(45,212,191,.09);border-color:var(--cyan);box-shadow:0 0 0 4px rgba(34,211,238,.07)}
[data-testid="stFileUploaderDropzone"]:not(:has([data-testid="stFileChips"],[data-testid="stUploadedFile"])){
 display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;text-align:center;min-height:210px}
[data-testid="stFileUploaderDropzone"]:not(:has([data-testid="stFileChips"],[data-testid="stUploadedFile"]))::before{
 content:"";order:0;width:56px;height:56px;border-radius:17px;background-color:rgba(45,212,191,.14);
 background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='26' height='26' viewBox='0 0 24 24' fill='none' stroke='%232DD4BF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><path d='M17 8l-5-5-5 5'/><path d='M12 3v12'/></svg>");
 background-repeat:no-repeat;background-position:center;border:1px solid rgba(45,212,191,.32);animation:float 3.2s ease-in-out infinite}
@keyframes float{50%{transform:translateY(-4px)}}
[data-testid="stFileUploaderDropzone"]:not(:has([data-testid="stFileChips"],[data-testid="stUploadedFile"]))::after{
 content:"Drag and drop your CV here";order:1;font-weight:600;color:var(--text);font-size:1rem}
[data-testid="stFileUploaderDropzone"]>span{order:2}
[data-testid="stFileUploaderDropzoneInstructions"]{order:3;color:var(--muted)}
[data-testid="stFileUploaderDropzoneInstructions"] *{font-size:.82rem!important;color:var(--muted)!important}
[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]{background:linear-gradient(135deg,#5EEAD4,var(--teal));color:#04231F;
 border:none;border-radius:10px;font-weight:600;padding:.45rem 1.1rem}
[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"] p{color:#04231F!important}
[data-testid="stFileUploaderDropzone"] button[data-testid="stBaseButton-secondary"]:hover{filter:brightness(1.08);color:#04231F}
[data-testid="stFileUploaderDropzone"]:has([data-testid="stFileChips"],[data-testid="stUploadedFile"]){display:flex;align-items:center;min-height:210px;
 background:rgba(45,212,191,.05);border-style:solid;border-color:rgba(45,212,191,.38)}
[data-testid="stFileUploaderDropzone"]>div,[data-testid="stFileUploaderDropzone"]>div>div,[data-testid="stFileChips"],[data-testid="stFileChips"]>div,[data-testid="stFileChips"]>div>div{width:100%;max-width:none;flex:1 1 auto}
[data-testid="stFileUploaderDropzone"] [aria-label="Add files"]{display:none}
[data-testid="stFileChip"],[data-testid="stUploadedFile"]{width:100%;background:rgba(19,33,63,.85);border:1px solid rgba(45,212,191,.45);
 border-radius:14px;padding:14px 16px;align-items:center;gap:14px;box-shadow:0 6px 18px rgba(2,6,16,.35)}
[data-testid="stFileChip"]>div:first-child,[data-testid="stUploadedFile"]>div:first-child{flex:none;width:46px;height:46px;border-radius:12px;
 display:grid;place-items:center;background:rgba(45,212,191,.15)!important;border:1px solid rgba(45,212,191,.3)}
[data-testid="stFileChip"]>div:first-child svg,[data-testid="stUploadedFile"] svg{color:var(--teal);fill:var(--teal);width:24px;height:24px}
[data-testid="stFileChipName"]{color:var(--text);font-weight:600;font-size:1rem}
[data-testid="stFileChip"] [data-testid="stFileChipName"]+div,[data-testid="stFileChip"]>div:nth-child(2)>div:last-child{color:var(--muted);font-size:.84rem}
[data-testid="stFileChipDeleteBtn"],[data-testid="stUploadedFileDeleteBtn"]{margin-left:auto}
[data-testid="stFileChipDeleteBtn"] button{color:var(--muted);border-radius:10px;padding:6px;transition:color .15s,background .15s}
[data-testid="stFileChipDeleteBtn"] button svg{width:22px;height:22px}
[data-testid="stFileChipDeleteBtn"] button:hover,[data-testid="stUploadedFileDeleteBtn"]:hover{color:#FCA5A5;background:rgba(239,68,68,.14)}

/* ============ buttons ============ */
.stApp [data-testid="stBaseButton-secondary"],.stApp [data-testid="stBaseButton-secondary"]:focus{background:rgba(19,33,63,.7);
 border:1px solid var(--border2);border-radius:12px;color:var(--text);transition:all .18s}
.stApp [data-testid="stBaseButton-secondary"]:hover{border-color:var(--teal);color:#7CF0E0;background:rgba(45,212,191,.09);transform:translateY(-1px)}
.stApp [data-testid="stBaseButton-secondary"] p,.stApp [data-testid="stBaseButton-primary"] p{font-weight:600;font-size:.98rem!important}
.stApp [data-testid="stBaseButton-primary"]{position:relative;overflow:hidden;isolation:isolate;
 background:linear-gradient(110deg,#14B8A6,#2DD4BF 40%,#22D3EE 100%)!important;border:1px solid rgba(255,255,255,.22)!important;
 border-radius:16px;min-height:3.6rem;box-shadow:0 12px 34px rgba(34,211,238,.28),inset 0 1px 0 rgba(255,255,255,.4);
 transition:transform .18s,box-shadow .18s,filter .18s}
.stApp [data-testid="stBaseButton-primary"]::before{content:"";position:absolute;inset:0;z-index:-1;width:45%;left:-60%;
 background:linear-gradient(105deg,transparent,rgba(255,255,255,.45),transparent);transform:skewX(-18deg);animation:shine 4.5s ease-in-out infinite}
@keyframes shine{0%,55%{left:-60%}100%{left:130%}}
.stApp [data-testid="stBaseButton-primary"]:hover{transform:translateY(-2px);filter:brightness(1.06);box-shadow:0 18px 44px rgba(34,211,238,.42),inset 0 1px 0 rgba(255,255,255,.45)}
.stApp [data-testid="stBaseButton-primary"]:active{transform:translateY(0) scale(.99)}
.stApp [data-testid="stBaseButton-primary"] p,.stApp [data-testid="stBaseButton-primary"] span{color:#031C1A!important;font-size:1.08rem!important;font-weight:700}
.stApp [data-testid="stDownloadButton"] button{background:rgba(45,212,191,.10);border:1px solid rgba(45,212,191,.5);color:#7CF0E0;border-radius:12px;min-height:2.9rem}
.stApp [data-testid="stDownloadButton"] button:hover{background:var(--teal);color:#04231F;border-color:var(--teal);transform:translateY(-1px)}
.stApp [data-testid="stDownloadButton"] button:hover p{color:#04231F!important}
.stApp [data-testid="stDownloadButton"] button p{color:inherit}

/* ============ alerts, notes, expanders ============ */
[data-testid="stAlert"]{border-radius:14px;border:1px solid var(--border2);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}
.note{display:flex;gap:11px;align-items:flex-start;background:rgba(245,184,75,.07);border:1px solid rgba(245,184,75,.30);
 color:#EAD39B;border-radius:14px;padding:12px 15px;font-size:.88rem;line-height:1.5;margin:6px 0 20px}
.note svg{flex:none;margin-top:2px;color:var(--amber)}
[data-testid="stSidebar"] .note{margin:6px 0 12px;font-size:.82rem}
[data-testid="stExpander"]{border:1px solid var(--border);border-radius:14px;background:rgba(14,26,51,.55)}

/* ============ AI processing state ============ */
.proc{border-radius:20px;padding:22px 26px;display:grid;grid-template-columns:96px 1fr;gap:24px;align-items:center;margin-top:14px;
 border-color:rgba(34,211,238,.4);position:relative;overflow:hidden}
.proc::after{content:"";position:absolute;left:0;bottom:0;height:3px;width:40%;background:linear-gradient(90deg,transparent,var(--cyan),transparent);animation:slide 1.4s ease-in-out infinite}
@keyframes slide{0%{left:-40%}100%{left:100%}}
.orb{position:relative;width:88px;height:88px;margin:auto}
.orb i{position:absolute;inset:0;border-radius:50%;border:2px solid transparent}
.orb i:nth-child(1){border-top-color:var(--teal);border-right-color:var(--teal);animation:spin 1.3s linear infinite}
.orb i:nth-child(2){inset:11px;border-bottom-color:var(--cyan);border-left-color:var(--cyan);animation:spin 1.9s linear infinite reverse}
.orb i:nth-child(3){inset:22px;border-top-color:#7CF0E0;animation:spin 2.6s linear infinite}
.orb b{position:absolute;inset:32px;border-radius:50%;background:radial-gradient(circle,#7CF0E0,var(--teal) 55%,transparent 72%);animation:breathe 1.8s ease-in-out infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes breathe{50%{transform:scale(.7);opacity:.7}}
.proc-t{font-family:'Poppins',sans-serif;font-weight:600;font-size:1.12rem;margin-bottom:2px}
.proc-s{font-size:.86rem;color:var(--muted);margin-bottom:12px}
.stg{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px}
.st1{display:flex;align-items:center;gap:10px;padding:8px 11px;border-radius:11px;border:1px solid var(--border);background:rgba(255,255,255,.02);font-size:.84rem;color:var(--muted);min-width:0}
.st1 .sd{flex:none;width:18px;height:18px;border-radius:50%;border:2px solid #3A4A6B}
.st1 div{min-width:0}.st1 span{display:block;font-size:.74rem;color:#7CF0E0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.st1.ok{color:var(--text);border-color:rgba(45,212,191,.32)}
.st1.ok .sd{background:var(--teal);border-color:var(--teal);box-shadow:inset 0 0 0 3px #062925}
.st1.run{color:var(--text);border-color:rgba(34,211,238,.55);background:rgba(34,211,238,.06)}
.st1.run .sd{border-color:var(--cyan);border-top-color:transparent;animation:spin .8s linear infinite}
.donebar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;border-radius:16px;padding:12px 18px;margin:18px 0 6px;border-color:rgba(45,212,191,.35)}
.donebar .ic{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:linear-gradient(135deg,#5EEAD4,var(--teal));color:#04231F}
.donebar b{font-weight:600}.donebar .m{font-size:.84rem;color:var(--muted)}
.donebar .chips2{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}
.donebar .chips2 span{font-size:.76rem;color:#B6C4DC;border:1px solid var(--border);border-radius:8px;padding:3px 9px;background:rgba(255,255,255,.03)}

/* ============ dashboard ============ */
.sec-h{display:flex;align-items:flex-end;justify-content:space-between;gap:10px;margin:14px 0 16px;flex-wrap:wrap}
.sec-h .st{font-size:1.8rem;font-weight:600;color:var(--text);line-height:1.2}
.sec-h .ss{font-size:.92rem;color:var(--muted);margin-top:2px}
.sec-h .role{font-size:.82rem;color:#7CF0E0;background:rgba(45,212,191,.10);border:1px solid rgba(45,212,191,.3);
 border-radius:999px;padding:5px 13px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-flex;gap:6px;align-items:center}
.sub-h{display:flex;align-items:center;gap:12px;margin:22px 0 14px}
.sub-h .ic{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;color:var(--teal);background:rgba(45,212,191,.12);border:1px solid rgba(45,212,191,.28)}
.sub-h .t{font-family:'Poppins',sans-serif;font-weight:600;font-size:1.25rem;line-height:1.2}
.sub-h .s{font-size:.86rem;color:var(--muted)}
.dash{display:grid;grid-template-columns:minmax(250px,.9fr) 2fr;gap:16px;margin-bottom:16px}
.dcard{padding:22px;transition:border-color .2s,transform .2s}
.score{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:14px;position:relative;overflow:hidden}
.score::before{content:"";position:absolute;width:260px;height:260px;border-radius:50%;top:50%;left:50%;transform:translate(-50%,-62%);
 background:radial-gradient(circle,var(--glow),transparent 66%);opacity:.22;pointer-events:none}
.ring-w{position:relative;width:184px;height:184px}
.ring{width:100%;height:100%;display:block;filter:drop-shadow(0 0 12px var(--glow))}
.ring-bg{stroke:rgba(120,170,210,.14)}
.ring-fg{animation:ringin 1.3s cubic-bezier(.2,.8,.2,1)}
@keyframes ringin{from{stroke-dasharray:0 327}}
.ring-c{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring-v{font-size:2.6rem;font-weight:700;color:var(--text);line-height:1}
.ring-v small{font-size:1.2rem;font-weight:600;color:var(--muted)}
.ring-l{font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-top:7px}
.verdict{font-size:.95rem;font-weight:600;padding:6px 16px;border-radius:999px;border:1px solid;position:relative}
.dright{display:flex;flex-direction:column;gap:16px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.stat{border-radius:20px;padding:18px 20px;position:relative;overflow:hidden;transition:transform .2s,border-color .2s}
.stat:hover,.lp:hover,.ins:hover,.rnode:hover{transform:translateY(-3px);border-color:var(--border2)}
.stat::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--c)}
.stat::after{content:"";position:absolute;right:-30px;top:-30px;width:110px;height:110px;border-radius:50%;background:radial-gradient(circle,var(--bgc),transparent 70%)}
.stat-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;position:relative;z-index:1}
.kl{font-size:.76rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-weight:600}
.stat-i{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;color:var(--c);background:var(--bgc)}
.kv{font-size:2.4rem;font-weight:700;color:var(--text);line-height:1;position:relative;z-index:1}
.ks{font-size:.82rem;color:var(--muted);margin-top:6px;position:relative;z-index:1}
.break{flex:1}
.brow{margin-top:14px}.brow:first-of-type{margin-top:0}
.bh{display:flex;justify-content:space-between;align-items:baseline;font-size:.9rem;margin-bottom:7px;gap:10px}
.bh b{color:var(--text);font-weight:600}.bh span{color:var(--muted);font-size:.8rem}
.bh .bv{color:var(--text);font-weight:700;font-size:1rem;font-family:'Poppins',sans-serif}
.bar{height:10px;background:rgba(120,170,210,.13);border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#14B8A6,#2DD4BF 50%,#22D3EE);animation:grow 1s ease-out;box-shadow:0 0 12px rgba(45,212,191,.45)}
@keyframes grow{from{width:0!important}}
.chip{display:inline-block;padding:5px 13px;margin:3px 5px 3px 0;border-radius:9px;font-size:.88rem;font-weight:500;border:1px solid rgba(255,255,255,.06);transition:transform .15s}
.chip:hover{transform:translateY(-1px)}
.none{color:var(--muted);font-style:italic;font-size:.9rem}
.grp-h{display:flex;flex-direction:column;align-items:flex-start;gap:2px;margin-bottom:12px}
.grp-h b{font-family:'Poppins',sans-serif;font-weight:600;font-size:1rem}.grp-h span{font-size:.8rem;color:var(--muted)}
.cnt{display:inline-block;min-width:28px;text-align:center;border-radius:999px;padding:2px 10px;font-size:.82rem;font-weight:700;margin-left:8px}
.legend{display:flex;gap:16px;font-size:.82rem;color:var(--muted);margin:-6px 0 4px;flex-wrap:wrap}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
.chart-sum{font-size:.8rem;color:var(--muted);margin-top:4px}

/* ============ tabs ============ */
[role="tablist"]{gap:4px;background:rgba(10,20,44,.7);border:1px solid var(--border);border-radius:16px;padding:6px;margin-bottom:10px;
 box-shadow:none!important;-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);overflow-x:auto}
[data-baseweb="tab-border"],[data-baseweb="tab-highlight"]{display:none}
[role="tablist"]>div:not([role="tab"]):empty{display:none}
[role="tab"]{height:auto;padding:11px 18px;border-radius:11px;color:var(--muted);transition:background .15s,color .15s;margin:0;border:0;background:transparent;white-space:nowrap}
[role="tab"]:hover{background:rgba(255,255,255,.05);color:var(--text)}
[role="tab"][aria-selected="true"]{background:linear-gradient(135deg,rgba(45,212,191,.20),rgba(34,211,238,.10));color:#9BF5E8;box-shadow:inset 0 -3px 0 var(--teal)}
[role="tab"]>div:last-child:not([data-testid="stMarkdownContainer"]){display:none}
.stApp [role="tab"] p{font-size:.96rem!important;font-weight:600;color:inherit}
[role="tabpanel"]{padding-top:14px}

/* ============ skill table ============ */
.tbl-w{container:tblw/inline-size}
.tbl-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:14px}
.tbl{width:100%;border-collapse:separate;border-spacing:0;font-size:.93rem}
.tbl th{position:sticky;top:0;background:#101C38;color:var(--muted);text-align:left;font-size:.74rem;text-transform:uppercase;
 letter-spacing:.08em;font-weight:600;padding:13px 20px;border-bottom:1px solid var(--border);white-space:nowrap}
.tbl td{padding:14px 20px;border-bottom:1px solid rgba(120,170,210,.10);color:var(--text)}
.tbl tr:last-child td{border-bottom:0}
.tbl .sk{font-weight:600}.tbl .cat{color:var(--muted)}
.tbl .num,.tbl th.num{text-align:right;font-variant-numeric:tabular-nums}
.tbl tbody tr{transition:background .12s}
.tbl tr.row-match td:first-child{box-shadow:inset 3px 0 0 #2DD4BF}
.tbl tr.row-miss td:first-child{box-shadow:inset 3px 0 0 #F5B84B}
.tbl tr.row-extra td:first-child{box-shadow:inset 3px 0 0 #6CB6FF}
.tbl tr.row-match{background:rgba(45,212,191,.04)}.tbl tr.row-miss{background:rgba(245,184,75,.045)}.tbl tr.row-extra{background:rgba(108,182,255,.045)}
.tbl tbody tr:hover{background:rgba(255,255,255,.055)}
.badge{display:inline-flex;align-items:center;gap:7px;padding:4px 12px;border-radius:999px;font-size:.8rem;font-weight:600}
.badge::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}
.b-match{background:rgba(45,212,191,.15);color:#7CF0E0}.b-miss{background:rgba(245,184,75,.15);color:#F9D48A}.b-extra{background:rgba(108,182,255,.16);color:#A9D2FF}
.empty{padding:28px;text-align:center;color:var(--muted);border:1px dashed var(--border2);border-radius:14px}
.count{font-size:.84rem;color:var(--muted);margin:10px 2px 0}

/* ============ recommendations + roadmap ============ */
.ins-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-bottom:8px}
.ins{border-radius:18px;padding:18px 20px;display:flex;flex-direction:column;gap:8px;position:relative;overflow:hidden;transition:transform .2s,border-color .2s;min-width:0}
.ins::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--c)}
.ins-top{display:flex;align-items:center;gap:12px}
.ins-i{flex:none;width:36px;height:36px;border-radius:11px;display:grid;place-items:center;color:var(--c);background:var(--bgc);border:1px solid var(--c)}
.ins-t{font-weight:600;font-size:1rem;line-height:1.3}
.ins-b{font-size:.92rem;color:#B9C6DC;line-height:1.55}
.ins .chip{font-size:.8rem;padding:3px 10px}
.road{display:flex;align-items:stretch;gap:12px;margin:4px 0 22px}
.rnode{flex:1;border-radius:16px;border-top:3px solid var(--c);padding:14px 16px;transition:transform .2s,border-color .2s}
.rn1{font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--c);font-weight:700}
.rn2{font-weight:600;font-size:1.04rem;margin:3px 0 2px}
.rn3{font-size:.82rem;color:var(--muted)}
.rn4{font-size:.8rem;color:#C9D5EA;margin-top:8px;padding-top:8px;border-top:1px dashed var(--border2)}
.rn4 b{color:var(--c);font-weight:700}
.phase{position:relative;padding-left:40px;margin-bottom:22px}
.phase::before{content:"";position:absolute;left:14px;top:34px;bottom:-24px;width:2px;background:linear-gradient(var(--c),var(--border2))}
.phase.last::before{display:none}
.pdot{position:absolute;left:0;top:2px;width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font-size:.82rem;
 font-weight:700;color:#06121F;background:var(--c);box-shadow:0 0 0 5px rgba(255,255,255,.04),0 0 18px var(--c)}
.ph-t{font-weight:600;font-size:1.1rem;line-height:1.3;margin-top:2px}
.ph-s{font-size:.86rem;color:var(--muted);margin:2px 0 14px}
.lp-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.lp{border-radius:18px;padding:16px 18px;display:flex;flex-direction:column;gap:12px;transition:border-color .2s,transform .2s}
.lp-top{display:flex;align-items:center;gap:12px}.lp-top>div{min-width:0}
.lp,.rnode,.stat,.dcard,.ins{min-width:0}
.lp-n{flex:none;width:30px;height:30px;border-radius:9px;display:grid;place-items:center;background:rgba(255,255,255,.05);border:1px solid var(--border2);font-weight:700;font-size:.85rem}
.lp-name{font-weight:600;font-size:1.02rem;line-height:1.25}.lp-cat{font-size:.78rem;color:var(--muted)}
.pri{margin-left:auto;flex:none;padding:3px 11px;border-radius:999px;font-size:.74rem;font-weight:700;color:var(--c);background:var(--bgc);border:1px solid var(--c)}
.res{display:flex;align-items:center;gap:9px;padding:8px 12px;border-radius:10px;background:rgba(255,255,255,.03);border:1px solid var(--border);
 color:#C9D5EA!important;text-decoration:none!important;font-size:.88rem;transition:all .15s}
.res:hover{border-color:var(--teal);color:#7CF0E0!important;background:rgba(45,212,191,.08);transform:translateX(2px)}
.res svg{flex:none;color:var(--teal)}.res span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lp-links{display:flex;flex-direction:column;gap:7px}
.lp-tip{font-size:.82rem;color:var(--muted);border-top:1px dashed var(--border2);padding-top:10px}

/* ============ export / analysis details ============ */
.kvlist{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.kvi{padding:10px 14px;border-radius:12px;border:1px solid var(--border);background:rgba(255,255,255,.025)}
.kvi span{display:block;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.kvi b{font-family:'Poppins',sans-serif;font-weight:600;font-size:1.05rem}

/* ============ responsive ============ */
@container tblw (max-width:700px){
 .tbl-wrap{border:0}.tbl thead{display:none}
 .tbl,.tbl tbody,.tbl tr,.tbl td{display:block;width:100%}
 .tbl tr{margin-bottom:10px;border:1px solid var(--border);border-radius:12px;padding:8px 14px}
 .tbl td{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border:0!important;text-align:right!important;box-shadow:none!important}
 .tbl td::before{content:attr(data-label);color:var(--muted);font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;font-weight:600}
}
@media (max-width:980px){
 .dash{grid-template-columns:minmax(0,1fr)}
 .score{flex-direction:row;justify-content:space-around;flex-wrap:wrap}
 .lp-grid,.ins-grid{grid-template-columns:minmax(0,1fr)}
}
@media (max-width:760px){
 .block-container{padding:3rem .9rem 3rem}
 .hero{padding:24px 18px 20px}.hero .h1{font-size:1.75rem}
 .flow{flex-direction:column;align-items:stretch}.fline{display:none}
 .stats{grid-template-columns:1fr 1fr 1fr;gap:10px}.stat{padding:14px 12px}.kv{font-size:1.7rem}.stat-i{display:none}
 .road{flex-direction:column}
 [class*="st-key-card"]{padding:18px 16px}
 [role="tab"]{padding:10px 12px}
 .sec-h .st{font-size:1.45rem}
 .proc{grid-template-columns:1fr;text-align:center;gap:14px}
 .stg{text-align:left}
 .donebar .chips2{margin-left:0}
}
@media (max-width:480px){.stats{gap:8px}.stat{padding:12px 11px}.stat::before{width:3px}.kv{font-size:1.55rem}.kl{font-size:.64rem;letter-spacing:.05em}.ks{font-size:.72rem}.pill{font-size:.74rem}.bh{flex-wrap:wrap}}

/* ============ accessibility: reduced motion ============ */
@media (prefers-reduced-motion:reduce){
 *,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}
 .ring-fg,.bar i{animation:none!important}
}
"""
_vars = (f"--bg:{BG};--navy:{NAVY};--surface2:{SURFACE2};--border:{BORDER};--border2:{BORDER2};"
         f"--text:{TEXT};--muted:{MUTED};--teal:{TEAL};--cyan:{CYAN};--amber:{AMBER};--glow:{TEAL}")
st.markdown(f"<style>:root{{{_vars}}}{CSS}</style>", unsafe_allow_html=True)

DISCLAIMER = ("The match score is a text-similarity indicator based on skill overlap and TF-IDF cosine "
              "similarity. It is not a hiring probability, a prediction of success, or an assessment of "
              "your ability. Use it as a guide for improving your CV.")

JD_PLACEHOLDER = """Example: Data Analyst

About the role
We are looking for a Data Analyst to turn data into insight for our product team.

Responsibilities
- Write SQL queries and clean large datasets with Python and pandas
- Build dashboards in Power BI or Tableau
- Present findings to stakeholders

Requirements
- Experience with SQL, Python and Excel
- Knowledge of statistics and data visualization
- Strong communication and teamwork skills"""

# Real pipeline stages (each one is reported by the actual code as it finishes)
STAGES = [("read", "Reading CV"), ("clean", "Normalizing text"), ("skills", "Detecting skills"),
          ("similarity", "TF-IDF similarity"), ("score", "Scoring results")]


# ---------------------------------------------------------------- helpers
_NICE = {"aws": "AWS", "nlp": "NLP", "sql": "SQL", "gcp": "GCP", "html": "HTML", "css": "CSS", "etl": "ETL", "llm": "LLM",
         "ci/cd": "CI/CD", "tcp/ip": "TCP/IP", "siem": "SIEM", "owasp": "OWASP", "tdd": "TDD", "php": "PHP", "ios": "iOS",
         "power bi": "Power BI", "a/b testing": "A/B Testing", "mysql": "MySQL", "postgresql": "PostgreSQL",
         "mongodb": "MongoDB", "nosql": "NoSQL", "javascript": "JavaScript", "typescript": "TypeScript", "github": "GitHub",
         "gitlab": "GitLab", "tensorflow": "TensorFlow", "pytorch": "PyTorch", "opencv": "OpenCV", "fastapi": "FastAPI",
         "scikit-learn": "scikit-learn", "numpy": "NumPy", "pandas": "pandas", "matlab": "MATLAB", "golang": "Go",
         "node.js": "Node.js", "next.js": "Next.js", "asp.net": "ASP.NET", "rest api": "REST API", "graphql": "GraphQL",
         "wordpress": "WordPress", "junit": "JUnit", "pytest": "pytest", "sqlite": "SQLite", "ansible": "Ansible",
         "c#": "C#", "c++": "C++", "jupyter": "Jupyter", "generative ai": "Generative AI"}


def nice(skill):
    """Display name for a skill (UI only; the analysis data keeps its original values)."""
    return _NICE.get(str(skill).lower(), str(skill).title())


def chips(items, kind):
    bg, fg = CHIP[kind]
    if not items:
        return "<span class='none'>None found</span>"
    return "".join(f"<span class='chip' style='background:{bg};color:{fg}'>{html.escape(nice(i))}</span>" for i in items)


def card_head(ic, title, sub, right=""):
    r = f"<span class='cr'>{right}</span>" if right else ""
    return (f"<div class='card-h'><span class='ic'>{icon(ic, 19)}</span><div><div class='ct'>{title}</div>"
            f"<div class='cs'>{sub}</div></div>{r}</div>")


def sub_head(ic, title, sub):
    return (f"<div class='sub-h'><span class='ic'>{icon(ic, 19)}</span><div><div class='t'>{title}</div>"
            f"<div class='s'>{sub}</div></div></div>")


def note(text):
    return f"<div class='note'>{icon('info', 18)}<div>{text}</div></div>"


def stat_card(label, value, sub, ic, color, bg):
    return (f"<div class='stat' style='--c:{color};--bgc:{bg}'><div class='stat-top'><span class='kl'>{label}</span>"
            f"<span class='stat-i'>{icon(ic, 18)}</span></div><div class='kv'>{value}</div><div class='ks'>{sub}</div></div>")


def score_ring(score, c1, c2):
    circ = 2 * math.pi * 52
    return (f"<div class='ring-w' role='img' aria-label='Match score {score:g} percent'>"
            f"<svg class='ring' viewBox='0 0 120 120' aria-hidden='true'>"
            f"<defs><linearGradient id='rg' x1='0' y1='0' x2='1' y2='1'><stop offset='0%' stop-color='{c1}'/>"
            f"<stop offset='100%' stop-color='{c2}'/></linearGradient></defs>"
            f"<circle class='ring-bg' cx='60' cy='60' r='52' fill='none' stroke-width='10'/>"
            f"<circle class='ring-fg' cx='60' cy='60' r='52' fill='none' stroke='url(#rg)' stroke-width='10' stroke-linecap='round' "
            f"stroke-dasharray='{circ * min(score, 100) / 100:.2f} {circ:.2f}' transform='rotate(-90 60 60)'/></svg>"
            f"<div class='ring-c'><div class='ring-v'>{score:g}<small>%</small></div><div class='ring-l'>Match score</div></div></div>")


def breakdown_row(label, value, pct, note_text):
    return (f"<div class='brow'><div class='bh'><div><b>{label}</b> <span>{note_text}</span></div><div class='bv'>{value}</div></div>"
            f"<div class='bar' role='progressbar' aria-label='{label}' aria-valuemin='0' aria-valuemax='100' aria-valuenow='{pct or 0}'>"
            f"<i style='width:{max(0, min(pct or 0, 100))}%'></i></div></div>")


def status_table(df):
    if df.empty:
        return "<div class='empty'>No skills match the selected filters.</div>"
    rows = []
    for _, x in df.iterrows():
        k = KIND[x["Status"]]
        rows.append(f"<tr class='row-{k}'><td class='sk' data-label='Skill'>{html.escape(nice(x['Skill']))}</td>"
                    f"<td class='cat' data-label='Category'>{html.escape(str(x['Category']))}</td>"
                    f"<td data-label='Status'><span class='badge b-{k}'>{x['Status']}</span></td>"
                    f"<td class='num' data-label='Job mentions'>{int(x['Job mentions'])}</td>"
                    f"<td class='num' data-label='CV mentions'>{int(x['CV mentions'])}</td></tr>")
    return ("<div class='tbl-w'><div class='tbl-wrap'><table class='tbl'><thead><tr><th scope='col'>Skill</th><th scope='col'>Category</th>"
            "<th scope='col'>Status</th><th scope='col' class='num'>Job mentions</th><th scope='col' class='num'>CV mentions</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table></div></div>")


def style(fig, h=330):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT, family="Inter, sans-serif", size=13),
                      hoverlabel=dict(bgcolor="#0E1A33", bordercolor=TEAL, font=dict(color=TEXT, family="Inter, sans-serif")),
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(color=MUTED)))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=MUTED))
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def priority(rank, mentions):
    if mentions >= 2 or rank < 3: return "High", RED
    if rank < 7: return "Medium", CYAN
    return "Low", SLATE


def style_status(df):
    """Subtle status colours for the export table (falls back to plain table if styling is unavailable)."""
    try:
        colors = {"Matched": "background-color:rgba(45,212,191,.16);color:#7CF0E0",
                  "Missing": "background-color:rgba(245,184,75,.16);color:#F9D48A",
                  "Extra": "background-color:rgba(108,182,255,.16);color:#A9D2FF"}
        sty = df.style
        return (getattr(sty, "map", None) or sty.applymap)(lambda v: colors.get(v, ""), subset=["Status"])
    except Exception:
        return df


def stage_detail(stage, info):
    """Human-readable detail for a pipeline stage, built only from values the analysis actually reported."""
    if stage == "clean":
        return f"CV {info['cv_chars']:,} / job {info['jd_chars']:,} chars"
    if stage == "skills":
        return f"{info['cv_skills']} in CV / {info['jd_skills']} in job"
    if stage == "similarity":
        return f"Cosine similarity {info['similarity']}%"
    if stage == "score":
        return f"{info['score']}% / {info['verdict']}"
    return ""


def processing_html(done):
    """The AI processing panel. A stage is 'done' only after the real code reports it."""
    active = next((k for k, _ in STAGES if k not in done), None)
    items = ""
    for k, label in STAGES:
        cls = "ok" if k in done else "run" if k == active else ""
        det = f"<span>{html.escape(done[k])}</span>" if k in done and done[k] else ""
        items += f"<div class='st1 {cls}'><i class='sd'></i><div>{label}{det}</div></div>"
    return ("<div class='proc' role='status' aria-live='polite'><div class='orb' aria-hidden='true'><i></i><i></i><i></i><b></b></div>"
            "<div><div class='proc-t'>Analyzing your CV</div>"
            "<div class='proc-s'>Extracting skills and comparing them with the job description. Everything runs locally.</div>"
            f"<div class='stg'>{items}</div></div></div>")


def build_insights(r):
    """Personalised recommendations derived only from this analysis result (no canned text about skills you do not have)."""
    table, cats = r["table"], r["categories"]
    ttl = lambda xs: [nice(x) for x in xs]
    out = []
    mentions = {s.lower(): int(m) for s, m in zip(table["Skill"], table["Job mentions"])}
    cv_mentions = {s.lower(): int(m) for s, m in zip(table["Skill"], table["CV mentions"])}

    if r["missing"]:
        top = r["missing"][:3]
        if max(mentions.get(s, 1) for s in top) >= 2:
            detail = ", ".join(f"{nice(s)} ({mentions.get(s, 1)}x)" for s in top)
            body = (f"The job description emphasises {detail}. Skills it mentions most often carry the most weight, "
                    "so start with these.")
        else:
            body = ("The job description names each of these once and does not stress any of them more than the others, "
                    "so begin here and work down the roadmap.")
        out.append(("target", "Close the highest-impact gaps first", body, "miss", ttl(top)))
        if not cats.empty:
            gaps = cats[cats["Missing"] > 0].copy()
            if not gaps.empty:
                gaps["cov"] = gaps["Matched"] / (gaps["Matched"] + gaps["Missing"])
                worst = gaps.sort_values(["cov", "Missing"], ascending=[True, False]).index[0]
                row = cats.loc[worst]
                tot = int(row["Matched"] + row["Missing"])
                miss_in = [s for s in r["missing"] if SKILL_TO_CATEGORY[s] == worst]
                out.append(("layers", f"Biggest category gap: {worst}",
                            f"You cover {int(row['Matched'])} of {tot} required skills in this category "
                            f"({row['Matched'] / tot * 100:.0f}%). Focusing here lifts your coverage the most.", "miss", ttl(miss_in[:5])))
        have_cats = {SKILL_TO_CATEGORY[s] for s in r["matched"]}
        quick = [s for s in r["missing"] if SKILL_TO_CATEGORY[s] in have_cats][:4]
        if quick:
            qc = sorted({SKILL_TO_CATEGORY[s] for s in quick})
            out.append(("trend", "Quick wins next to skills you already have",
                        f"You already show related skills in {', '.join(qc)}, so these should be the shortest steps to add.",
                        "tip", ttl(quick)))
    else:
        out.append(("award", "No skill gaps detected", "Every skill found in the job description also appears on your CV. "
                    "Focus on tailoring wording and showing results.", "match", []))

    if not cats.empty:
        full = [c for c in cats.index if cats.loc[c, "Missing"] == 0 and cats.loc[c, "Matched"] > 0]
        if full and r["missing"]:
            strong = [s for s in r["matched"] if SKILL_TO_CATEGORY[s] in full][:5]
            out.append(("check", "Lead with your strengths",
                        f"You cover every required skill in {', '.join(full)}. Put these near the top of your CV and summary.",
                        "match", ttl(strong)))
    thin = sorted((s for s in r["matched"] if mentions.get(s, 0) > cv_mentions.get(s, 0)),
                  key=lambda s: mentions[s] - cv_mentions.get(s, 0), reverse=True)[:4]
    if thin:
        out.append(("file", "Show more evidence for skills you already have",
                    "The job mentions these more often than your CV does. Add a project, result or bullet that proves each one.",
                    "tip", ttl(thin)))
    soft = [s for s in r["missing"] if SKILL_TO_CATEGORY[s] == "Soft Skills"]
    if soft and CATEGORY_TIPS.get("Soft Skills"):
        out.append(("bulb", "Make soft skills visible", CATEGORY_TIPS["Soft Skills"], "tip", ttl(soft)))
    if r["extra"] and r["matched"]:
        out.append(("layers", "Keep your differentiators, but stay on target",
                    f"{len(r['extra'])} skills on your CV were not requested by this job. They can set you apart, "
                    "but make sure the required skills are the easiest to spot.", "extra", ttl(r["extra"][:5])))
    return out


INS_COL = {"miss": (AMBER, "rgba(245,184,75,.14)"), "match": (TEAL, "rgba(45,212,191,.14)"),
           "tip": (CYAN, "rgba(34,211,238,.13)"), "extra": (BLUE, "rgba(108,182,255,.14)")}


def insight_card(ic, title, body, kind, items):
    c, bg = INS_COL[kind]
    chip_kind = {"miss": "miss", "match": "match", "tip": "match", "extra": "extra"}[kind]
    ch = f"<div>{chips(items, chip_kind)}</div>" if items else ""
    return (f"<div class='ins' style='--c:{c};--bgc:{bg}'><div class='ins-top'><span class='ins-i'>{icon(ic, 18)}</span>"
            f"<div class='ins-t'>{title}</div></div><div class='ins-b'>{body}</div>{ch}</div>")


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown(f"<div class='sb-brand'><span class='logo'>{icon('target', 21)}</span><div><div class='sb-t'>SkillGap</div>"
                f"<div class='sb-s'>Career intelligence</div></div></div><div class='sb-h'>Workspace</div>", unsafe_allow_html=True)
    status_slot = st.empty()
    st.markdown("<div class='sb-h'>Quick actions</div>", unsafe_allow_html=True)
    if st.button("Load sample data", width="stretch", icon=":material/science:"):
        st.session_state.use_sample = True
        st.session_state.jd = SAMPLE_JD
        st.session_state.job_title = "Junior Data Scientist"
    if st.button("Clear all", width="stretch", icon=":material/restart_alt:"):
        for k in ("use_sample", "jd", "job_title", "result"):
            st.session_state.pop(k, None)
        st.session_state.jd = ""
    st.markdown("<div class='sb-h'>About</div>", unsafe_allow_html=True)
    st.write("Compare your CV with any job description, see which skills you already have, and get a "
             "learning plan for the gaps.")
    with st.expander("How the score is calculated"):
        st.write(f"Score = {int(SKILL_WEIGHT*100)}% skill coverage (share of the job's skills found in your CV) "
                 f"+ {int(TEXT_WEIGHT*100)}% TF-IDF cosine similarity of the full texts.")
    st.caption("Privacy: files are processed in memory only. Nothing is saved to disk or sent to any API.")

# ---------------------------------------------------------------- header
_up = st.session_state.get("cv_upload")
_cv_ready = _up is not None or st.session_state.get("use_sample", False)
_jd_ready = len((st.session_state.get("jd") or "").strip()) >= 30
_done = st.session_state.get("result") is not None
_cv_sub = html.escape(_up.name) if _up is not None else ("Sample CV loaded" if _cv_ready else "PDF or DOCX, max 5 MB")
_flags = [_cv_ready, _jd_ready, _done]
_first_open = next((i for i, f in enumerate(_flags) if not f), None)
_steps = [("file", "1. Add your CV", _cv_sub), ("briefcase", "2. Add the job", "Job description added" if _jd_ready else "Paste the role requirements"),
          ("report", "3. Review results", "Report ready below" if _done else "Click Analyze Match")]
_flow = ""
for i, (ic_, t_, s_) in enumerate(_steps):
    cls = "done" if _flags[i] else "active" if i == _first_open else ""
    _flow += (f"<div class='fstep {cls}'><span class='fi'>{icon('check' if _flags[i] else ic_, 19)}</span>"
              f"<div><div class='ft'>{t_}</div><div class='fs'>{s_}</div></div></div>")
    if i < 2:
        _flow += "<span class='fline'></span>"

_ws = [("CV", _cv_ready, "Ready" if _cv_ready else "Missing"), ("Job description", _jd_ready, "Ready" if _jd_ready else "Missing"),
       ("Analysis", _done, "Complete" if _done else "Not run")]
status_slot.markdown("<div class='ws'>" + "".join(
    f"<div class='ws-i {'on' if ok else ''}'><span class='dot'></span><b>{n}</b><span class='v'>{v}</span></div>" for n, ok, v in _ws)
    + "</div>", unsafe_allow_html=True)

st.markdown(
    f"<div class='topbar'><div class='brand'><span class='logo'>{icon('target', 19)}</span>"
    f"<span class='brand-n'>SkillGap <span>Analyzer</span></span></div>"
    f"<div class='pills'><span class='pill'><i class='live'></i>Local analysis engine</span>"
    f"<span class='pill'>{icon('lock', 14)}Processed in memory. Nothing is stored.</span></div></div>"
    f"<div class='hero'><div class='eyebrow'>{icon('sparkle', 13)}Career intelligence</div>"
    f"<div class='h1'>Job Match and <span class='grad'>Skill Gap</span> Analyzer</div>"
    f"<div class='sub'>Compare your CV with a job description to see the skills you already have, the skills you are "
    f"missing, and what to learn next.</div>"
    f"<div class='flow'>{_flow}</div></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- inputs
use_sample = st.session_state.get("use_sample", False)
with st.container(key="inputs"):
    c1, c2 = st.columns(2, gap="large")
    with c1:
        with st.container(key="card_cv"):
            st.markdown(card_head("upload", "Your CV", "Upload a PDF or DOCX file", "Max 5 MB"), unsafe_allow_html=True)
            upload = st.file_uploader("Upload a PDF or DOCX file (max 5 MB)", type=["pdf", "docx"], key="cv_upload",
                                      label_visibility="collapsed")
            if use_sample and not upload:
                st.success("Using the built-in sample CV.", icon=":material/check_circle:")
                with st.expander("Preview sample CV"):
                    st.text(SAMPLE_CV)
            st.markdown("<div class='hint'>Your file is read in memory and is never stored.</div>", unsafe_allow_html=True)
    with c2:
        with st.container(key="card_jd"):
            st.markdown(card_head("briefcase", "Job description", "Paste the role you are applying for"), unsafe_allow_html=True)
            job_title = st.text_input("Job title (optional)", key="job_title", placeholder="e.g. Data Analyst")
            jd_text = st.text_area("Paste the full job description", key="jd", height=280, placeholder=JD_PLACEHOLDER)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
if st.button("Analyze Match", type="primary", width="stretch", icon=":material/auto_awesome:", key="analyze"):
    panel = st.empty()
    done = {}
    ok = False
    t0 = time.perf_counter()

    def on_stage(stage, info):  # called by matcher.analyze as each real stage completes
        done[stage] = stage_detail(stage, info)
        panel.markdown(processing_html(done), unsafe_allow_html=True)

    try:
        panel.markdown(processing_html(done), unsafe_allow_html=True)
        if upload is not None:
            cv_text = extract_text(upload.name, upload.getvalue())
            done["read"] = f"{len(cv_text):,} characters extracted"
        elif use_sample:
            cv_text = SAMPLE_CV
            done["read"] = "Built-in sample CV"
        else:
            raise CVExtractionError("Please upload a CV, or load the sample data from the sidebar.")
        if len((jd_text or "").strip()) < 30:
            raise CVExtractionError("Please paste a longer job description (at least a few sentences).")
        panel.markdown(processing_html(done), unsafe_allow_html=True)
        res = analyze(cv_text, jd_text, progress=on_stage)
        res["title"] = (job_title or "").strip() or "this role"
        res["pipeline"] = dict(done)
        res["elapsed"] = time.perf_counter() - t0
        st.session_state.result = res
        panel.empty()
        ok = True
    except CVExtractionError as e:
        panel.empty()
        st.session_state.pop("result", None)
        st.error(str(e), icon=":material/error:")
    except Exception as e:
        panel.empty()
        st.session_state.pop("result", None)
        st.error(f"Something went wrong: {e}", icon=":material/error:")
    if ok:
        st.rerun()  # redraw the header and sidebar status with the finished analysis

# ---------------------------------------------------------------- results
r = st.session_state.get("result")
if r:
    pipe = r.get("pipeline", {})
    st.markdown(
        f"<div class='donebar' role='status'><span class='ic'>{icon('check', 18)}</span><div><b>Analysis complete</b>"
        f"<div class='m'>Finished in {r.get('elapsed', 0):.2f} s, all processing on this machine</div></div>"
        f"<div class='chips2'><span>{len(pipe)} stages</span><span>{len(r['matched']) + len(r['extra'])} CV skills</span>"
        f"<span>{r['jd_skill_count']} job skills</span></div></div>", unsafe_allow_html=True)
    role = f"<span class='role'>{icon('briefcase', 13)} {html.escape(str(r['title']))}</span>" if r.get("title") else ""
    st.markdown(f"<div class='sec-h'><div><div class='st'>Dashboard</div>"
                f"<div class='ss'>Results for {html.escape(str(r['title']))}</div></div>{role}</div>", unsafe_allow_html=True)
    if r["jd_skill_count"] == 0:
        st.warning("No known technical skills were found in the job description, so the score uses text "
                   "similarity only. Try a more detailed description.", icon=":material/warning:")

    score = r["score"]
    c1_, c2_ = ((TEAL, CYAN) if score >= 60 else (AMBER, "#FBD38D") if score >= 35 else ("#FB8F6B", AMBER))
    color = c1_
    cov = "n/a" if r["skill_coverage"] is None else f"{r['skill_coverage']}%"
    has_cov = r["skill_coverage"] is not None
    sk_note = f"{int(SKILL_WEIGHT * 100)}% of score" if has_cov else "not used"
    tx_note = f"{int(TEXT_WEIGHT * 100)}% of score" if has_cov else "100% of score"
    st.markdown(
        f"<div class='dash'><div class='dcard score' style='--glow:{color}'>" + score_ring(score, c1_, c2_)
        + f"<div class='verdict' style='color:{c2_};border-color:{color}66;background:{color}1F'>{r['verdict']}</div></div>"
        + "<div class='dright'><div class='stats'>"
        + stat_card("Matched", len(r["matched"]), "skills in both", "check", TEAL, "rgba(45,212,191,.16)")
        + stat_card("Missing", len(r["missing"]), "skills to build", "alert", AMBER, "rgba(245,184,75,.16)")
        + stat_card("Extra", len(r["extra"]), "additional CV skills", "layers", BLUE, "rgba(108,182,255,.16)")
        + "</div><div class='dcard break'>"
        + breakdown_row("Skill coverage", cov, r["skill_coverage"], sk_note)
        + breakdown_row("Text similarity", f"{r['text_similarity']}%", r["text_similarity"], tx_note + " &middot; TF-IDF cosine")
        + "</div></div></div>", unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs([":material/space_dashboard: Overview", ":material/compare_arrows: Skill Comparison",
                              ":material/route: Learning Roadmap", ":material/download: Data and Export"])
    table: pd.DataFrame = r["table"]
    cats: pd.DataFrame = r["categories"]

    with t1:
        req = table[table["Status"] != "Extra"].sort_values("Job mentions", ascending=False).head(12)
        H = max(360, 90 + 28 * len(req))
        a, b = st.columns(2, gap="large")
        with a:
            with st.container(key="card_dist"):
                st.markdown(card_head("layers", "Skill distribution", "Matched, missing and additional skills"), unsafe_allow_html=True)
                vals = [len(r["matched"]), len(r["missing"]), len(r["extra"])]
                if sum(vals):
                    donut = go.Figure(go.Pie(labels=["Matched", "Missing", "Extra"], values=vals, hole=.68, sort=False,
                                             marker=dict(colors=[TEAL, AMBER, BLUE], line=dict(color="#0B1530", width=3)),
                                             textinfo="value", textfont=dict(color="#04121F", size=14),
                                             hovertemplate="%{label}: %{value} skills (%{percent})<extra></extra>"))
                    donut.add_annotation(text=f"<b>{sum(vals)}</b><br><span style='font-size:12px;color:{MUTED}'>skills</span>",
                                         showarrow=False, font=dict(size=30, color=TEXT))
                    show(style(donut, 340).update_layout(legend=dict(orientation="h", yanchor="top", y=-0.02, xanchor="center", x=.5)))
                    st.markdown(f"<div class='chart-sum'>{vals[0]} matched, {vals[1]} missing and {vals[2]} additional skills.</div>",
                                unsafe_allow_html=True)
                else:
                    st.markdown("<div class='empty'>No known skills were detected in either document.</div>", unsafe_allow_html=True)
        with b:
            with st.container(key="card_bar"):
                st.markdown(card_head("compare", "Required skills by category", "Matched and missing skills per category"), unsafe_allow_html=True)
                if not cats.empty:
                    order = (cats["Matched"] + cats["Missing"]).sort_values().index.tolist()
                    bar = go.Figure()
                    for key, col in (("Matched", TEAL), ("Missing", AMBER)):
                        bar.add_bar(name=key, y=order, x=cats.loc[order, key].tolist(), orientation="h", marker_color=col,
                                    hovertemplate="%{y}: %{x} " + key.lower() + "<extra></extra>")
                    bar.update_layout(barmode="stack", bargap=.35, legend=dict(traceorder="normal"))
                    show(style(bar, 340).update_xaxes(dtick=1, rangemode="tozero"))
                    st.markdown("<div class='chart-sum'>Counts of required skills per category.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='empty'>No required skills were detected.</div>", unsafe_allow_html=True)
        c, d = st.columns(2, gap="large")
        with c:
            with st.container(key="card_radar"):
                if len(cats) >= 3:
                    st.markdown(card_head("target", "Coverage by category", "Share of required skills you already have (%)"), unsafe_allow_html=True)
                    cov_pct = (cats["Matched"] / (cats["Matched"] + cats["Missing"]) * 100).round(0)
                    wrapped = ["<br>".join(textwrap.wrap(x, 14)) for x in cats.index.tolist()]  # display-only label wrapping
                    radar = go.Figure(go.Scatterpolar(r=cov_pct.tolist() + [cov_pct.iloc[0]], theta=wrapped + [wrapped[0]],
                                                      fill="toself", line=dict(color=CYAN, width=2), fillcolor="rgba(45,212,191,0.26)",
                                                      hovertemplate="%{theta}: %{r}%<extra></extra>"))
                    radar.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                                   radialaxis=dict(range=[0, 100], gridcolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED, size=10)),
                                                   angularaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=12, color=TEXT))))
                    show(style(radar, H).update_layout(margin=dict(l=105, r=105, t=20, b=20)))
                else:
                    st.markdown(card_head("target", "Coverage by category", "Share of required skills you already have (%)"), unsafe_allow_html=True)
                    if not cats.empty:
                        cov_pct = (cats["Matched"] / (cats["Matched"] + cats["Missing"]) * 100).round(0)
                        cb = go.Figure(go.Bar(y=cov_pct.index.tolist(), x=cov_pct.tolist(), orientation="h", marker_color=CYAN,
                                              hovertemplate="%{y}: %{x}%<extra></extra>"))
                        show(style(cb, H).update_xaxes(range=[0, 100]))
                    else:
                        st.markdown("<div class='empty'>No required skills were detected.</div>", unsafe_allow_html=True)
        with d:
            with st.container(key="card_imp"):
                st.markdown(card_head("report", "Most emphasised skills in the job description", "Ranked by number of mentions"),
                            unsafe_allow_html=True)
                if not req.empty:
                    st.markdown(f"<div class='legend'><span><i style='background:{TEAL}'></i>You have it</span>"
                                f"<span><i style='background:{AMBER}'></i>Missing</span></div>", unsafe_allow_html=True)
                    imp = go.Figure(go.Bar(y=[nice(x) for x in req["Skill"][::-1]], x=req["Job mentions"][::-1], orientation="h",
                                           marker_color=[TEAL if s == "Matched" else AMBER for s in req["Status"][::-1]],
                                           hovertemplate="%{y}: %{x} mentions<extra></extra>"))
                    show(style(imp, H - 40).update_xaxes(dtick=1, rangemode="tozero"))
                else:
                    st.markdown("<div class='empty'>No required skills were detected.</div>", unsafe_allow_html=True)

    with t2:
        g1, g2, g3 = st.columns(3, gap="medium")
        for col, key, label, sub, kind in ((g1, "matched", "Matched skills", "found in both", "match"),
                                           (g2, "missing", "Missing skills", "requested, not on your CV", "miss"),
                                           (g3, "extra", "Additional CV skills", "not requested", "extra")):
            with col:
                with st.container(key=f"card_grp_{key}"):
                    bg, fg = CHIP[kind]
                    st.markdown(f"<div class='grp-h'><b>{label}<span class='cnt' style='background:{bg};color:{fg}'>{len(r[key])}</span></b>"
                                f"<span>{sub}</span></div>" + chips(r[key], kind), unsafe_allow_html=True)
        with st.container(key="card_cmp"):
            st.markdown(card_head("table", "Skill comparison table", "Every detected skill, with its status and mention counts"),
                        unsafe_allow_html=True)
            cmp_status = st.multiselect("Filter by status", ["Matched", "Missing", "Extra"],
                                        default=["Matched", "Missing", "Extra"], key="cmp_filter")
            cview = table[table["Status"].isin(cmp_status)]
            st.markdown(status_table(cview) + f"<div class='count'>Showing {len(cview)} of {len(table)} skills</div>",
                        unsafe_allow_html=True)

    with t3:
        insights = build_insights(r)
        if insights:
            st.markdown(sub_head("sparkle", "Personalized recommendations", "Generated from your own CV and this job description"),
                        unsafe_allow_html=True)
            st.markdown("<div class='ins-grid'>" + "".join(insight_card(*x) for x in insights) + "</div>", unsafe_allow_html=True)

        st.markdown(sub_head("route", "Learning roadmap", "Missing skills grouped into phases, most emphasised first"),
                    unsafe_allow_html=True)
        if not r["missing"]:
            st.success("No missing skills detected. Focus on tailoring your CV wording to the job description.",
                       icon=":material/check_circle:")
        else:
            st.markdown("<div class='ss' style='margin:0 0 14px;color:#9AA9C2'>Skills are ranked by how strongly the job "
                        "description emphasises them. Work through the phases from the top.</div>", unsafe_allow_html=True)
        mentions = {s.lower(): m for s, m in zip(table["Skill"], table["Job mentions"])}
        phases = {"High": [], "Medium": [], "Low": []}
        for i, (skill, links) in enumerate(r["recommendations"].items()):
            label, pcolor = priority(i, mentions.get(skill, 1))
            phases[label].append((i, skill, links, pcolor))
        meta = {"High": ("Start here", "Most emphasised by the job description.", AMBER, "rgba(245,184,75,.14)"),
                "Medium": ("Build next", "Learn these once the essentials are covered.", CYAN, "rgba(34,211,238,.13)"),
                "Low": ("Round out", "Lower emphasis. Good for a well-rounded profile.", SLATE, "rgba(147,164,192,.14)")}
        active = [k for k in ("High", "Medium", "Low") if phases[k]]
        # Skill coverage after each phase = (matched + skills learned so far) / skills the job asks for (same formula as the analysis)
        jd_n, have, nodes, cum = r["jd_skill_count"], len(r["matched"]), "", 0
        for n, k in enumerate(active):
            before = have + cum
            cum += len(phases[k])
            cov_line = ""
            if jd_n:
                cov_line = (f"<div class='rn4'>Skill coverage <b>{before / jd_n * 100:.0f}%</b> &rarr; <b>{(have + cum) / jd_n * 100:.0f}%</b></div>")
            nodes += (f"<div class='rnode' style='--c:{meta[k][2]}'><div class='rn1'>Phase {n + 1}</div><div class='rn2'>{meta[k][0]}</div>"
                      f"<div class='rn3'>{k} priority &middot; {len(phases[k])} skill{'s' if len(phases[k]) != 1 else ''}</div>{cov_line}</div>")
        if active:
            st.markdown(f"<div class='road'>{nodes}</div>", unsafe_allow_html=True)
        for n, k in enumerate(active):
            ttl, desc, pc, pbg = meta[k]
            cards = ""
            for i, skill, links, _ in phases[k]:
                cat = SKILL_TO_CATEGORY[skill]
                res_html = "".join(f"<a class='res' href='{html.escape(url, quote=True)}' target='_blank' rel='noopener noreferrer'>"
                                   f"{icon('link', 15)}<span>{html.escape(text)}</span></a>" for text, url in links)
                tip = CATEGORY_TIPS.get(cat)
                tip_html = f"<div class='lp-tip'>{html.escape(tip)}</div>" if tip else ""
                cards += (f"<div class='lp' style='--c:{pc};--bgc:{pbg}'><div class='lp-top'><span class='lp-n'>{i + 1}</span>"
                          f"<div><div class='lp-name'>{html.escape(nice(skill))}</div><div class='lp-cat'>{html.escape(cat)}</div></div>"
                          f"<span class='pri'>{k} priority</span></div><div class='lp-links'>{res_html}</div>{tip_html}</div>")
            st.markdown(f"<div class='phase{' last' if n == len(active) - 1 else ''}' style='--c:{pc}'><span class='pdot'>{n + 1}</span><div class='ph-t'>{ttl}</div>"
                        f"<div class='ph-s'>{desc}</div><div class='lp-grid'>{cards}</div></div>", unsafe_allow_html=True)
        if len(r["missing"]) > len(r["recommendations"]):
            st.caption(f"The roadmap covers the {len(r['recommendations'])} most emphasised of {len(r['missing'])} missing skills.")
        st.info("Only list skills you genuinely have. Build a small project with each new skill first, then add it to your CV.",
                icon=":material/lightbulb:")

    with t4:
        summary = (f"Job Match and Skill Gap Analysis for {r['title']}\nMatch score: {r['score']}% ({r['verdict']})\n"
                   f"Skill coverage: {r['skill_coverage']}%  |  Text similarity: {r['text_similarity']}%\n\n"
                   f"Matched: {', '.join(r['matched']) or 'none'}\nMissing: {', '.join(r['missing']) or 'none'}\n"
                   f"Extra: {', '.join(r['extra']) or 'none'}\n\nNote: {DISCLAIMER}\n")
        d1, d2 = st.columns(2, gap="medium")
        with d1:
            with st.container(key="card_dl_csv"):
                st.markdown(card_head("table", "Skill gap table", f"CSV &middot; {len(table)} rows, opens in Excel or Sheets"), unsafe_allow_html=True)
                st.download_button("Download table (CSV)", table.to_csv(index=False).encode("utf-8"),
                                   file_name="skill_gap_analysis.csv", mime="text/csv", width="stretch",
                                   icon=":material/download:", key="dl_csv")
        with d2:
            with st.container(key="card_dl_txt"):
                st.markdown(card_head("text", "Match summary", "TXT &middot; score, verdict and skill lists"), unsafe_allow_html=True)
                st.download_button("Download summary (TXT)", summary.encode("utf-8"),
                                   file_name="match_summary.txt", mime="text/plain", width="stretch",
                                   icon=":material/download:", key="dl_txt")
        with st.container(key="card_data"):
            st.markdown(card_head("table", "Data table", "Filter the full skill-gap data"), unsafe_allow_html=True)
            status = st.multiselect("Filter by status", ["Matched", "Missing", "Extra"], default=["Matched", "Missing", "Extra"])
            view = table[table["Status"].isin(status)]
            st.dataframe(style_status(view), width="stretch", hide_index=True)
        if pipe:
            with st.container(key="card_pipe"):
                st.markdown(card_head("cpu", "How this result was produced", "Each stage reported by the analysis as it ran"), unsafe_allow_html=True)
                st.markdown("<div class='kvlist'>" + "".join(
                    f"<div class='kvi'><span>{lbl}</span><b>{html.escape(pipe.get(k, '') or 'Done')}</b></div>" for k, lbl in STAGES if k in pipe)
                    + "</div>", unsafe_allow_html=True)
