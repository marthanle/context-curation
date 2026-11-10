import re
from pathlib import Path
page = Path("docs/index.html")
html = page.read_text()
seal = Path("assets/wax-seal.svg").read_text().strip()
html = re.sub(r'<span class="ml-seal-wrap">.*?</span><!--/ml-seal-->', '', html, flags=re.S)
html = re.sub(r'<style id="ml-seal-style">.*?</style>', '', html, flags=re.S)
html = html.replace('<span id="wax-seal"></span>', '')
if "</h1>" not in html:
    raise SystemExit("No title found, tell Claude.")
html = html.replace("</h1>", f'<span class="ml-seal-wrap">{seal}</span><!--/ml-seal--></h1>', 1)
style = """<style id="ml-seal-style">
[class*="seal"]:not(.ml-seal):not(.ml-seal-wrap):not(:has(h1)), [id*="seal"]:not(:has(h1)) { display: none !important; }
.ml-seal-wrap { display: inline-block; margin-left: 28px; vertical-align: top; position: relative; top: -18px; line-height: 0; }
@media (max-width: 600px) { .ml-seal { width: 46px; height: 46px; } .ml-seal-wrap { margin-left: 12px; top: -8px; } }
</style>"""
html = html.replace("</head>", style + "\n</head>", 1)
page.write_text(html)
print("Added ML wax seal")
