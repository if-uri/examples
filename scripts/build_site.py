#!/usr/bin/env python3
"""Build a static, brand-styled site for the ifURI examples (-> examples.ifuri.com).

Usage: python3 scripts/build_site.py [OUT_DIR]   (default: _site)
"""
import os, re, shutil, html, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
GH = "https://github.com/if-uri/examples"
SKIP = {".git", "__pycache__", "generated", ".venv", "node_modules", "dist", "build", ".pytest_cache", ".idea", "_site"}

def md(text):
    out=[]; i=0; lines=text.replace("\r","").split("\n"); n=len(lines)
    def inline(s):
        s=html.escape(s)
        s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m:f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
        s=re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        s=re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
        return s
    while i<n:
        ln=lines[i]
        if ln.startswith("```"):
            i+=1; buf=[]
            while i<n and not lines[i].startswith("```"): buf.append(html.escape(lines[i])); i+=1
            i+=1; out.append("<pre><code>"+"\n".join(buf)+"</code></pre>"); continue
        m=re.match(r'(#{1,6})\s+(.*)', ln)
        if m: lvl=len(m.group(1)); out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>"); i+=1; continue
        if ln.strip().startswith("|") and i+1<n and re.match(r'^\s*\|?[\s:|-]+\|?\s*$', lines[i+1]):
            head=[c.strip() for c in ln.strip().strip("|").split("|")]; i+=2; rows=[]
            while i<n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i+=1
            t="<table><thead><tr>"+"".join(f"<th>{inline(c)}</th>" for c in head)+"</tr></thead><tbody>"
            for r in rows: t+="<tr>"+"".join(f"<td>{inline(c)}</td>" for c in r)+"</tr>"
            out.append(t+"</tbody></table>"); continue
        if re.match(r'\s*[-*]\s+', ln):
            items=[]
            while i<n and re.match(r'\s*[-*]\s+', lines[i]): items.append(inline(re.sub(r'\s*[-*]\s+','',lines[i],count=1))); i+=1
            out.append("<ul>"+"".join(f"<li>{x}</li>" for x in items)+"</ul>"); continue
        if re.match(r'\s*\d+\.\s+', ln):
            items=[]
            while i<n and re.match(r'\s*\d+\.\s+', lines[i]): items.append(inline(re.sub(r'\s*\d+\.\s+','',lines[i],count=1))); i+=1
            out.append("<ol>"+"".join(f"<li>{x}</li>" for x in items)+"</ol>"); continue
        if ln.strip()=="": i+=1; continue
        para=[ln]; i+=1
        while i<n and lines[i].strip() and not re.match(r'(#{1,6}\s|```|\s*[-*]\s|\s*\d+\.\s|\s*\|)', lines[i]): para.append(lines[i]); i+=1
        out.append("<p>"+inline(" ".join(para))+"</p>")
    return "\n".join(out)

def page(title, body, depth):
    base="../" if depth else ""
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><meta name="theme-color" content="#1E1B4B">
<link rel="icon" href="https://ifuri.com/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{base}style.css">
</head><body>
<header><a class="brand" href="{base}index.html">ifURI <span>examples</span></a>
<nav><a href="https://ifuri.com/">ifuri.com</a><a href="https://ifuri.com/docs/">Docs</a><a href="{GH}">GitHub</a></nav></header>
<main>{body}</main>
<footer>ifURI examples · runnable examples for <a href="https://github.com/tellmesh/urirun">urirun</a> · <a href="https://ifuri.com/">ifuri.com</a></footer>
<script src="{base}copy.js"></script>
</body></html>"""

def first_title_desc(readme):
    t=None; d=None
    for ln in readme.split("\n"):
        if t is None and ln.startswith("# "): t=ln[2:].strip(); continue
        if t is not None and ln.strip() and not ln.startswith("#") and not ln.startswith("```"):
            d=re.sub(r'`([^`]+)`',r'\1',ln.strip()); break
    return t,d

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)

(OUT/"style.css").write_text(""":root{--bg:#1E1B4B;--card:rgba(255,255,255,.06);--text:#EEF2FF;--muted:#A5B4FC;--line:rgba(255,255,255,.14);--green:#34D399;--violet:#4F46E5}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(900px 520px at 88% -8%,rgba(79,70,229,.2),transparent 60%),linear-gradient(180deg,#1E1B4B,#191640);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Arial,sans-serif;line-height:1.6;min-height:100vh}
a{color:var(--green);text-decoration:none}a:hover{text-decoration:underline}
header{position:sticky;top:0;display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;padding:14px 24px;border-bottom:1px solid var(--line);background:rgba(30,27,75,.82);backdrop-filter:blur(12px)}
.brand{font-weight:800;font-size:18px;color:var(--text)}.brand span{color:var(--green)}
header nav a{color:var(--muted);font-weight:700;font-size:14px;margin-left:16px}header nav a:hover{color:var(--text);text-decoration:none}
main{max-width:960px;margin:0 auto;padding:40px 24px 72px}
h1{font-size:clamp(30px,4vw,44px);letter-spacing:-.02em;margin:0 0 6px}h2{font-size:24px;letter-spacing:-.01em;margin:30px 0 0}h3{font-size:18px;margin:22px 0 0}
p,li{color:#cdd6ee}.lead{font-size:18px;color:#cdd6ee;margin:8px 0 0}
code{background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.2);color:#6EE7B7;border-radius:6px;padding:.06rem .35rem;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.92em}
pre{position:relative;background:#0F172A;border:1px solid var(--line);border-radius:12px;padding:18px;overflow:auto}pre code{background:none;border:0;color:#E0E7FF;padding:0}
.copy-btn{position:absolute;top:10px;right:10px;font-size:11px;font-weight:800;letter-spacing:.04em;color:#0F172A;background:var(--green);border:0;border-radius:999px;padding:5px 11px;cursor:pointer;opacity:.6;transition:opacity .15s}
.copy-btn:hover,.copy-btn:focus-visible{opacity:1}
table{border-collapse:collapse;width:100%;margin:18px 0 0;font-size:14px}th,td{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}th{color:var(--green)}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:24px}
.card{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:18px}.card:hover{border-color:var(--green);text-decoration:none}
.card .n{font-family:ui-monospace,monospace;color:var(--green);font-size:13px}.card strong{display:block;font-size:17px;margin:4px 0;color:var(--text)}.card em{color:var(--muted);font-size:14px;font-style:normal}
.files{margin-top:8px}.files a{display:inline-block;margin:0 10px 6px 0;font-family:ui-monospace,monospace;font-size:13px}
.back{display:inline-block;margin-bottom:14px;color:var(--muted);font-size:14px}
footer{max-width:960px;margin:0 auto;padding:24px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
@media(max-width:720px){.grid{grid-template-columns:1fr}header{padding:12px 16px}main{padding:28px 16px 56px}}""", encoding="utf-8")

(OUT/"copy.js").write_text("""(function(){var en=document.documentElement.lang==='en';var L=en?'Copy':'Kopiuj',D=en?'Copied':'Skopiowano';
document.querySelectorAll('pre').forEach(function(pre){if(pre.querySelector('.copy-btn'))return;var code=pre.querySelector('code');
var b=document.createElement('button');b.type='button';b.className='copy-btn';b.textContent=L;b.setAttribute('aria-label',en?'Copy to clipboard':'Kopiuj do schowka');
b.addEventListener('click',function(){navigator.clipboard.writeText((code||pre).textContent).then(function(){b.textContent=D;setTimeout(function(){b.textContent=L},1200);}).catch(function(){});});
pre.appendChild(b);});})();""", encoding="utf-8")

dirs=sorted([d for d in os.listdir(ROOT) if re.match(r'\d+-', d) and (ROOT/d).is_dir()])
cards=[]
for d in dirs:
    src=ROOT/d; dst=OUT/d
    for r,subs,files in os.walk(src):
        subs[:]=[s for s in subs if s not in SKIP]
        rel=os.path.relpath(r,src); td=dst if rel=="." else dst/rel; td.mkdir(parents=True,exist_ok=True)
        for f in files: shutil.copy2(os.path.join(r,f), td/f)
    readme=(src/"README.md").read_text(encoding="utf-8") if (src/"README.md").exists() else f"# {d}"
    title,desc=first_title_desc(readme); title=title or d; desc=desc or ""
    if (dst/"index.html").exists(): (dst/"index.html").rename(dst/"original-index.html")
    flist=sorted([f for f in os.listdir(dst) if (dst/f).is_file() and f!="index.html"]) + sorted([f+"/" for f in os.listdir(dst) if (dst/f).is_dir()])
    files_html="".join(f'<a href="{html.escape(f)}">{html.escape(f)}</a>' for f in flist)
    body=f'<a class="back" href="../index.html">&larr; all examples</a>{md(readme)}<h2>Files</h2><div class="files">{files_html}</div>'
    body+=f'<p style="margin-top:18px"><a href="{GH}/tree/main/{d}">View on GitHub &rarr;</a></p>'
    (dst/"index.html").write_text(page(f"{title} · ifURI examples", body, 1), encoding="utf-8")
    cards.append((d,title,desc))

grid="".join(f'<a class="card" href="{d}/index.html"><span class="n">{d.split("-")[0]}</span><strong>{html.escape(t)}</strong><em>{html.escape(de)}</em></a>' for d,t,de in cards)
body=f'''<h1>ifURI examples</h1><p class="lead">Runnable examples for <code>urirun</code> and ifURI-style URI workflows &mdash; from a JSON binding to multi-computer Docker flows.</p>
<div class="grid">{grid}</div><h2>Run them locally</h2><pre><code>git clone {GH}.git
cd examples
make test</code></pre>'''
(OUT/"index.html").write_text(page("ifURI examples", body, 0), encoding="utf-8")
print(f"built {len(cards)} examples -> {OUT}")
