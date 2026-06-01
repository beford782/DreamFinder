#!/usr/bin/env python3
"""
Generate PDF versions of the onboarding documents.

Usage:
    python tools/md_to_pdf.py            # build all (default)
    python tools/md_to_pdf.py guide      # just customer guide
    python tools/md_to_pdf.py runbook    # just internal runbook
    python tools/md_to_pdf.py drive      # just Drive folder README

    python tools/md_to_pdf.py --backend edge        # force Edge headless
    python tools/md_to_pdf.py --backend weasyprint  # force WeasyPrint

Outputs to onboarding/*.pdf

Backends
--------
Two rendering backends produce visually equivalent PDFs (Letter, 0.75in
margins, doc-name + "Page X of Y" footer):

  weasyprint  -- the original path. Needs native GTK libraries, so it only
                 works on Linux / WSL / macOS. Footer comes from CSS @page
                 margin boxes.
  edge        -- a Windows-native path that drives Microsoft Edge in headless
                 mode over the DevTools protocol (Page.printToPDF) using only
                 the Python standard library (no extra pip packages). Footer
                 comes from a printToPDF footerTemplate. Works anywhere Edge
                 (or Chrome) is installed.

Default selection is automatic: if weasyprint imports cleanly it is used;
otherwise the Edge backend is used. Override with --backend or the
DF_PDF_BACKEND environment variable.
"""
import os
import sys
import base64
import json
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
import urllib.error

import markdown

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONBOARDING = os.path.join(REPO_ROOT, 'onboarding')

# ---------------------------------------------------------------------------
# Documents to render
# ---------------------------------------------------------------------------
# kind:
#   'md'  -> render markdown to HTML, themed
#   'txt' -> render as preformatted monospaced text (preserves the original
#            ASCII layout of README-style files)
DOCS = {
    'guide': {
        'src': os.path.join(ONBOARDING, 'Onboarding_Guide.md'),
        'out': os.path.join(ONBOARDING, 'DreamFinder_Onboarding_Guide.pdf'),
        'kind': 'md',
        'header_left': 'DreamFinder Onboarding',
    },
    'runbook': {
        'src': os.path.join(ONBOARDING, 'Build_Runbook.md'),
        'out': os.path.join(ONBOARDING, 'DreamFinder_Build_Runbook.pdf'),
        'kind': 'md',
        'header_left': 'DreamFinder Build Runbook (Internal)',
    },
    'drive': {
        'src': os.path.join(ONBOARDING, 'Drive_Folder_README.txt'),
        'out': os.path.join(ONBOARDING, 'DreamFinder_Image_Upload_Guide.pdf'),
        'kind': 'txt',
        'header_left': 'DreamFinder Image Upload Guide',
    },
}


def base_css(header_left):
    return f"""
@page {{
  size: Letter;
  margin: 0.75in;
  @bottom-right {{
    content: "Page " counter(page) " of " counter(pages);
    font-family: 'Helvetica', sans-serif;
    font-size: 9pt;
    color: #888;
  }}
  @bottom-left {{
    content: "{header_left}";
    font-family: 'Helvetica', sans-serif;
    font-size: 9pt;
    color: #888;
  }}
}}
body {{
  font-family: 'Helvetica', 'Arial', sans-serif;
  font-size: 10.5pt;
  line-height: 1.5;
  color: #1a1a1a;
}}
h1 {{
  font-size: 22pt;
  color: #0f1f33;
  border-bottom: 3px solid #d4a84b;
  padding-bottom: 0.3em;
  margin-top: 0;
}}
h2 {{
  font-size: 15pt;
  color: #0f1f33;
  margin-top: 1.5em;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.2em;
}}
h3 {{
  font-size: 12pt;
  color: #1f3a5c;
  margin-top: 1.2em;
}}
hr {{
  border: none;
  border-top: 1px solid #ccc;
  margin: 1.5em 0;
}}
a {{ color: #1f3a5c; text-decoration: none; }}
code {{
  background: #f4f1e8;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 9.5pt;
  color: #8B1A1A;
}}
pre {{
  background: #f4f1e8;
  padding: 0.75em;
  border-radius: 6px;
  border-left: 3px solid #d4a84b;
  font-size: 9pt;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}}
pre code {{ background: none; padding: 0; color: #1a1a1a; }}
table {{
  border-collapse: collapse;
  width: 100%;
  margin: 0.75em 0;
  font-size: 10pt;
}}
th, td {{
  border: 1px solid #ccc;
  padding: 0.5em 0.7em;
  text-align: left;
  vertical-align: top;
}}
th {{
  background: #0f1f33;
  color: #fff;
  font-weight: 600;
}}
tr:nth-child(even) td {{ background: #fafaf6; }}
ul, ol {{ padding-left: 1.5em; }}
li {{ margin-bottom: 0.25em; }}
blockquote {{
  border-left: 3px solid #d4a84b;
  background: #fefcf6;
  padding: 0.5em 1em;
  margin: 1em 0;
  color: #555;
  font-style: italic;
}}
strong {{ color: #0f1f33; }}
"""


def render_md(src, header_left):
    with open(src, 'r', encoding='utf-8') as f:
        md_text = f.read()
    html_body = markdown.markdown(
        md_text,
        extensions=['extra', 'sane_lists', 'tables', 'fenced_code'],
    )
    html_doc = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    return html_doc, base_css(header_left)


def render_txt(src, header_left):
    """Render a structured plain-text README as a styled PDF.
    Preserves the existing ASCII layout via a single <pre> block, but
    detects underlined section headings (==== / ----) and styles them."""
    with open(src, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    # Walk lines looking for heading patterns. Markdown's setext headings
    # already use === / --- under text — feed it through markdown for nice
    # heading + paragraph styling, but keep the indented blocks as <pre>.
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        next_line = lines[i + 1] if i + 1 < len(lines) else ''
        # Setext heading: text followed by === or ---
        if next_line and (set(next_line) == {'='} or set(next_line) == {'-'}) and len(next_line) >= 3 and line.strip():
            level = '#' if '=' in next_line else '##'
            out_lines.append(f"{level} {line.strip()}")
            i += 2
            continue
        # Indented block (2+ spaces) → preserve as code block lines
        if line.startswith('  '):
            block = []
            while i < len(lines) and (lines[i].startswith('  ') or lines[i] == ''):
                block.append(lines[i])
                i += 1
            # Strip trailing blanks
            while block and block[-1] == '':
                block.pop()
            if block:
                out_lines.append('```')
                out_lines.extend(block)
                out_lines.append('```')
            continue
        out_lines.append(line)
        i += 1

    md_text = '\n'.join(out_lines)
    html_body = markdown.markdown(md_text, extensions=['extra', 'fenced_code'])
    html_doc = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    return html_doc, base_css(header_left)


def render(cfg):
    """Return (html_doc, css) for a document config."""
    if cfg['kind'] == 'md':
        return render_md(cfg['src'], cfg['header_left'])
    return render_txt(cfg['src'], cfg['header_left'])


# ===========================================================================
# Backend: WeasyPrint (Linux / WSL / macOS)
# ===========================================================================
def build_weasyprint(cfg):
    from weasyprint import HTML, CSS  # imported lazily so Edge-only boxes work
    html_doc, css = render(cfg)
    HTML(string=html_doc, base_url=os.path.dirname(cfg['src'])).write_pdf(
        cfg['out'], stylesheets=[CSS(string=css)],
    )
    size_kb = os.path.getsize(cfg['out']) / 1024
    print(f"  {os.path.basename(cfg['out'])}  ({size_kb:.0f} KB)  [weasyprint]")


# ===========================================================================
# Backend: Edge / Chrome headless via DevTools protocol (Windows-native)
#
# Implemented with the Python standard library only -- a minimal WebSocket
# client (RFC 6455) speaking just enough Chrome DevTools Protocol to navigate
# a page and call Page.printToPDF. No extra pip packages required.
# ===========================================================================

def _find_browser():
    """Locate a Chromium-family browser. Edge preferred (ships with Win11)."""
    env = os.environ.get('DF_BROWSER') or os.environ.get('EDGE')
    if env and os.path.exists(env):
        return env
    candidates = [
        os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'),
                     'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
                     'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'),
                     'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
                     'Google', 'Chrome', 'Application', 'chrome.exe'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # Linux/macOS fallbacks (so --backend edge works there too if desired)
    for name in ('microsoft-edge', 'google-chrome', 'chromium', 'chromium-browser'):
        from shutil import which
        path = which(name)
        if path:
            return path
    raise RuntimeError(
        "No Chromium-family browser found. Install Microsoft Edge or Google "
        "Chrome, or set DF_BROWSER to the executable path.")


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _footer_template(header_left):
    # Chrome footer templates ignore page CSS; styles must be inline and sizes
    # in px. Padding matches the 0.75in page margin so the text aligns under
    # the body content. Class spans are substituted by Chrome at print time.
    left = (header_left.replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))
    return (
        '<div style="font-size:9px; color:#888; width:100%; '
        'font-family:Helvetica,Arial,sans-serif; padding:0 0.75in; '
        'display:flex; justify-content:space-between;">'
        f'<span>{left}</span>'
        '<span>Page <span class="pageNumber"></span> of '
        '<span class="totalPages"></span></span>'
        '</div>'
    )


class _WS:
    """Tiny RFC 6455 WebSocket client (text frames only)."""

    def __init__(self, host, port, path, timeout=60):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        resp = b''
        while b'\r\n\r\n' not in resp:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise IOError('WebSocket handshake failed (connection closed)')
            resp += chunk
        if b' 101 ' not in resp.split(b'\r\n', 1)[0]:
            raise IOError('WebSocket handshake rejected: '
                          + resp.split(b'\r\n', 1)[0].decode('latin-1'))

    def _recv_exact(self, n):
        buf = b''
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise IOError('WebSocket connection closed')
            buf += chunk
        return buf

    def send(self, text):
        payload = text.encode('utf-8')
        header = bytearray([0x81])  # FIN + text opcode
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack('>H', n)
        else:
            header.append(0x80 | 127)
            header += struct.pack('>Q', n)
        mask = os.urandom(4)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def recv(self):
        """Receive one full (possibly fragmented) text message."""
        data = bytearray()
        while True:
            b0, b1 = self._recv_exact(2)
            fin = b0 & 0x80
            opcode = b0 & 0x0f
            masked = b1 & 0x80
            length = b1 & 0x7f
            if length == 126:
                length = struct.unpack('>H', self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', self._recv_exact(8))[0]
            mask = self._recv_exact(4) if masked else b''
            payload = self._recv_exact(length) if length else b''
            if masked:
                payload = bytes(c ^ mask[i % 4] for i, c in enumerate(payload))
            if opcode == 0x8:        # close
                raise IOError('WebSocket closed by server')
            if opcode == 0x9:        # ping -> ignore (short-lived session)
                continue
            if opcode == 0xA:        # pong
                continue
            data += payload
            if fin:
                return bytes(data).decode('utf-8')

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class EdgeSession:
    """Launch one headless browser and reuse it to print many documents."""

    def __init__(self):
        self.exe = _find_browser()
        self.port = _free_port()
        self.profile = tempfile.mkdtemp(prefix='df_pdf_')
        self.proc = None
        self.ws = None
        self._id = 0
        self._events = []

    def __enter__(self):
        self.proc = subprocess.Popen(
            [
                self.exe,
                '--headless=new',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-extensions',
                '--remote-allow-origins=*',
                f'--remote-debugging-port={self.port}',
                f'--user-data-dir={self.profile}',
                'about:blank',
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ws_url = self._discover_page_ws()
        # ws://127.0.0.1:PORT/devtools/page/ID  ->  path after the host
        path = ws_url.split('127.0.0.1:%d' % self.port, 1)[1]
        self.ws = _WS('127.0.0.1', self.port, path)
        self._call('Page.enable')
        return self

    def __exit__(self, *exc):
        if self.ws:
            self.ws.close()
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        # Best-effort profile cleanup
        try:
            import shutil
            shutil.rmtree(self.profile, ignore_errors=True)
        except OSError:
            pass
        return False

    def _discover_page_ws(self, timeout=25):
        """Poll the DevTools HTTP endpoint until a page target appears."""
        deadline = time.time() + timeout
        last_err = None
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError('Browser exited before DevTools came up')
            try:
                with urllib.request.urlopen(
                        f'http://127.0.0.1:{self.port}/json', timeout=2) as r:
                    targets = json.loads(r.read().decode('utf-8'))
                for t in targets:
                    if t.get('type') == 'page' and t.get('webSocketDebuggerUrl'):
                        return t['webSocketDebuggerUrl']
            except (urllib.error.URLError, ConnectionError, OSError) as e:
                last_err = e
            time.sleep(0.25)
        raise RuntimeError(f'DevTools endpoint never came up: {last_err}')

    def _call(self, method, params=None):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({'id': mid, 'method': method,
                                 'params': params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == mid:
                if 'error' in msg:
                    raise RuntimeError(f"{method} failed: {msg['error']}")
                return msg.get('result', {})
            if 'method' in msg:
                self._events.append(msg['method'])

    def _wait_event(self, name):
        if name in self._events:
            self._events.remove(name)
            return
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('method') == name:
                return

    def print_doc(self, cfg):
        html_doc, css = render(cfg)
        # Inline the stylesheet (Chrome loads no external CSS here) and zero the
        # default body margin so it does not stack on the printToPDF margins.
        styled = html_doc.replace(
            '</head>', f'<style>body{{margin:0;}}{css}</style></head>', 1)
        tmp_html = cfg['out'] + '.render.html'
        with open(tmp_html, 'w', encoding='utf-8') as f:
            f.write(styled)
        try:
            file_url = 'file:' + urllib.request.pathname2url(
                os.path.abspath(tmp_html))
            self._events.clear()
            self._call('Page.navigate', {'url': file_url})
            self._wait_event('Page.loadEventFired')
            result = self._call('Page.printToPDF', {
                'landscape': False,
                'printBackground': True,
                'preferCSSPageSize': False,
                'paperWidth': 8.5,
                'paperHeight': 11.0,
                'marginTop': 0.75,
                'marginBottom': 0.75,
                'marginLeft': 0.75,
                'marginRight': 0.75,
                'displayHeaderFooter': True,
                'headerTemplate': '<div></div>',
                'footerTemplate': _footer_template(cfg['header_left']),
            })
            pdf = base64.b64decode(result['data'])
            with open(cfg['out'], 'wb') as f:
                f.write(pdf)
        finally:
            try:
                os.remove(tmp_html)
            except OSError:
                pass
        size_kb = os.path.getsize(cfg['out']) / 1024
        print(f"  {os.path.basename(cfg['out'])}  ({size_kb:.0f} KB)  [edge]")


# ===========================================================================
# Backend selection + entrypoint
# ===========================================================================
def _weasyprint_available():
    # Importing weasyprint without its native GTK libraries prints a multi-line
    # warning to stderr from a stream captured at its own import time, which an
    # in-process redirect can't reliably suppress. Probe in a subprocess with
    # stderr discarded so an auto-fallback to the Edge backend stays quiet.
    try:
        rc = subprocess.run(
            [sys.executable, '-c', 'import weasyprint'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode
        return rc == 0
    except Exception:
        return False


def resolve_backend(requested):
    if requested in ('weasyprint', 'edge'):
        return requested
    # auto: prefer weasyprint where it imports cleanly (Linux/WSL/macOS),
    # otherwise fall back to the Windows-native Edge backend.
    return 'weasyprint' if _weasyprint_available() else 'edge'


def main():
    argv = sys.argv[1:]
    backend = os.environ.get('DF_PDF_BACKEND', 'auto')
    targets = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--backend':
            backend = argv[i + 1]
            i += 2
            continue
        if a.startswith('--backend='):
            backend = a.split('=', 1)[1]
            i += 1
            continue
        targets.append(a)
        i += 1

    if not targets:
        targets = list(DOCS.keys())
    invalid = [t for t in targets if t not in DOCS]
    if invalid:
        print(f"Unknown target(s): {invalid}. Valid: {list(DOCS.keys())}")
        sys.exit(1)

    backend = resolve_backend(backend)
    print(f"Building PDFs (backend: {backend}):")
    if backend == 'weasyprint':
        for t in targets:
            build_weasyprint(DOCS[t])
    else:
        with EdgeSession() as edge:
            for t in targets:
                edge.print_doc(DOCS[t])


if __name__ == '__main__':
    main()
