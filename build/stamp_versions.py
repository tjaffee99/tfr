"""Append ?v=<content hash> to local CSS/JS links in index.html so browsers fetch new code after each deploy."""
import hashlib, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
page = os.path.join(ROOT, "index.html")
html = open(page).read()
for f in ("style.css", "projection.js", "app.js"):
    v = hashlib.md5(open(os.path.join(ROOT, f), "rb").read()).hexdigest()[:8]
    html = re.sub(r'(["\'])' + re.escape(f) + r'(\?v=[0-9a-f]+)?\1', lambda m: f"{m.group(1)}{f}?v={v}{m.group(1)}", html)
open(page, "w").write(html)
print("stamped")
