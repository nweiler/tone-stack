import http.server
import socketserver
import json
import os
import sys
import yaml
import traceback
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).parent))
import adapters
from meta_patch import MetaPatch

PORT = 8000
PATCH_DIR = Path("./patches")


def generate_preview(yaml_content, platform):
    """Convert a YAML patch string to a platform-specific export string.

    Returns (output_string, None) on success or (None, error_message) on failure.
    """
    try:
        patch = MetaPatch.from_yaml(yaml_content)
    except Exception as e:
        return None, f"YAML parse error: {e}"

    try:
        adapter = adapters.get_adapter(platform)
    except ValueError as e:
        return None, str(e)

    try:
        result = adapter.export_patch(patch)
        return result, None
    except Exception as e:
        return None, f"Export error: {e}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Meta-Patch | TONE-IDE</title>
    <style>
        :root {
            --bg: #002b36;
            --panel: #073642;
            --text: #839496;
            --text-bright: #93a1a1;
            --border: #586e75;
            --accent: #268bd2;
            --pedal: #6c71c4;
            --amp: #dc322f;
            --cab: #859900;
            --warning: #cb4b16;
        }
        
        body { 
            font-family: 'ui-monospace', 'Cascadia Code', 'Source Code Pro', Menlo, monospace; 
            background: var(--bg); 
            color: var(--text); 
            margin: 0; 
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            padding: 12px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--panel);
            color: var(--text-bright);
        }

        .main-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .editor-pane {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            border-right: 1px solid var(--border);
        }

        .text-pane {
            flex: 1;
            background: #001e26;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }

        pre, textarea {
            font-family: inherit;
            background: transparent;
            color: #2aa198; 
            border: none;
            width: 100%;
            height: 100%;
            resize: none;
            outline: none;
            font-size: 14px;
            line-height: 1.5;
        }

        .signal-chain {
            display: flex;
            flex-direction: column;
            gap: 12px;
            align-items: center;
        }

        .component {
            width: 90%;
            max-width: 450px;
            border: 1px solid var(--border);
            padding: 18px;
            position: relative;
            background: var(--panel);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            cursor: grab;
        }
        .component:active { cursor: grabbing; }
        .component.dragging { opacity: 0.4; border-style: dashed; }
        
        .pedal { border-left: 4px solid var(--pedal); }
        .amp { border-left: 4px solid var(--amp); }
        .cab { border-left: 4px solid var(--cab); }

        .comp-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            font-size: 0.75em;
            letter-spacing: 1px;
            color: var(--text-bright);
        }

        .comp-header select, .comp-header span, .comp-header div {
            pointer-events: auto;
        }

        input, select, textarea.meta-input {
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text-bright);
            padding: 6px 10px;
            font-family: inherit;
            border-radius: 2px;
        }

        .setting-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
            font-size: 0.9em;
        }
        .setting-row input {
            border: none;
            background: transparent;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            width: 45%;
            text-align: right;
            color: var(--accent);
        }

        .btn {
            background: transparent;
            border: 1px solid var(--accent);
            color: var(--accent);
            padding: 6px 18px;
            cursor: pointer;
            font-family: inherit;
            text-transform: uppercase;
            font-size: 0.85em;
            transition: all 0.2s;
        }
        .btn:hover {
            background: var(--accent);
            color: var(--panel);
        }
        .btn-danger { color: var(--warning); border-color: var(--warning); }
        .btn-danger:hover { background: var(--warning); color: var(--panel); }

        .arrow { color: var(--border); font-size: 20px; margin: 5px 0; }
        
        .toast { position: fixed; bottom: 20px; right: 20px; border: 1px solid var(--accent); background: var(--panel); color: var(--accent); padding: 12px 24px; display: none; }

        label { font-size: 0.7em; color: var(--border); font-weight: bold; text-transform: uppercase; }

        .drag-handle { color: var(--border); cursor: grab; font-size: 1.2em; margin-right: 10px; }

        .pane-tabs {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }
        .pane-tab {
            background: transparent;
            border: 1px solid transparent;
            color: var(--border);
            font-family: inherit;
            font-size: 0.7em;
            font-weight: bold;
            letter-spacing: 1px;
            padding: 4px 12px;
            cursor: pointer;
            text-transform: uppercase;
        }
        .pane-tab.active {
            color: var(--accent);
            border-color: var(--accent);
        }
        .pane-tab:hover:not(.active) { color: var(--text-bright); }
        #export-platform {
            margin-left: auto;
            font-size: 0.7em;
            padding: 4px 8px;
            display: none;
        }
        #export-output {
            flex: 1;
            overflow-y: auto;
            color: #2aa198;
            font-size: 13px;
            line-height: 1.5;
            white-space: pre;
            margin: 0;
            display: none;
        }
        .export-error { color: var(--warning); }
    </style>
</head>
<body>
    <header>
        <div style="font-weight: bold;">META-PATCH_IDE // [[FILENAME]]</div>
        <div>
            <button class="btn" onclick="savePatch()">[ SAVE ]</button>
            <a href="/" class="btn" style="text-decoration: none;">[ EXIT ]</a>
        </div>
    </header>

    <div class="main-container">
        <div class="editor-pane">
            <div style="margin-bottom: 30px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div style="grid-column: span 2;">
                    <label>PATCH NAME</label><br>
                    <input id="patch-name" style="width: 100%; font-size: 1.2em; color: var(--accent);" value="[[PATCH_NAME]]">
                </div>
                <div style="grid-column: span 2;">
                    <label>DESCRIPTION</label><br>
                    <textarea id="patch-desc" class="meta-input" style="width: 100%;" rows="2">[[PATCH_DESC]]</textarea>
                </div>
                <div style="grid-column: span 2;">
                    <label>TAGS (COMMA SEPARATED)</label><br>
                    <input id="patch-tags" style="width: 100%;" value="[[PATCH_TAGS]]">
                </div>
            </div>
            
            <div id="signal-chain" class="signal-chain"></div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button class="btn" style="border-style: dashed; width: 90%; max-width: 450px;" onclick="addComponent()">+ ADD COMPONENT</button>
            </div>
        </div>

        <div class="text-pane">
            <div class="pane-tabs">
                <button class="pane-tab active" id="tab-yaml" onclick="switchTab('yaml')">YAML</button>
                <button class="pane-tab" id="tab-export" onclick="switchTab('export')">EXPORT</button>
                <select id="export-platform" onchange="refreshExport()">
                    <option value="podgo">POD GO</option>
                    <option value="biasfx">BIAS FX</option>
                    <option value="amplitube">AMPLITUBE</option>
                </select>
            </div>
            <textarea id="yaml-output" readonly></textarea>
            <pre id="export-output"></pre>
        </div>
    </div>

    <div id="toast" class="toast">DATA_SAVED_SUCCESS</div>

    <script>
        let currentPatch = [[PATCH_JSON]];
        const filename = "[[FILENAME]]";
        let dragSrcIndex = null;

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => { t.style.display = 'none'; }, 3000);
        }

        function jsonToYaml(obj, indent = 0) {
            let yaml = '';
            const spaces = '  '.repeat(indent);
            if (obj === null) { return 'null\\n'; }
            for (const key in obj) {
                const val = obj[key];
                if (Array.isArray(val)) {
                    yaml += `${spaces}${key}:\\n`;
                    val.forEach(item => {
                        if (typeof item === 'object' && item !== null) {
                            yaml += `${spaces}- ${jsonToYaml(item, indent + 1).trim()}\\n`;
                        } else {
                            yaml += `${spaces}- ${typeof item === 'string' ? '"' + item + '"' : item}\\n`;
                        }
                    });
                } else if (typeof val === 'object' && val !== null) {
                    yaml += `${spaces}${key}:\\n${jsonToYaml(val, indent + 1)}`;
                } else {
                    yaml += `${spaces}${key}: ${typeof val === 'string' ? '"' + val + '"' : val}\\n`;
                }
            }
            return yaml;
        }

        let activeTab = 'yaml';

        function switchTab(tab) {
            activeTab = tab;
            document.getElementById('tab-yaml').classList.toggle('active', tab === 'yaml');
            document.getElementById('tab-export').classList.toggle('active', tab === 'export');
            document.getElementById('yaml-output').style.display = tab === 'yaml' ? 'block' : 'none';
            document.getElementById('export-output').style.display = tab === 'export' ? 'block' : 'none';
            document.getElementById('export-platform').style.display = tab === 'export' ? 'block' : 'none';
            if (tab === 'export') refreshExport();
        }

        async function refreshExport() {
            if (activeTab !== 'export') return;
            const platform = document.getElementById('export-platform').value;
            const yamlContent = document.getElementById('yaml-output').value;
            const out = document.getElementById('export-output');
            out.className = '';
            out.textContent = '...';
            try {
                const res = await fetch('/api/export-preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ yaml_content: yamlContent, platform })
                });
                const data = await res.json();
                if (data.error) {
                    out.className = 'export-error';
                    out.textContent = data.error;
                } else {
                    out.textContent = data.output;
                }
            } catch (e) {
                out.className = 'export-error';
                out.textContent = 'Connection error: ' + e.message;
            }
        }

        function updateYamlView() {
            currentPatch.name = document.getElementById('patch-name').value;
            currentPatch.description = document.getElementById('patch-desc').value;
            currentPatch.tags = document.getElementById('patch-tags').value.split(',').map(t => t.trim()).filter(t => t !== "");
            document.getElementById('yaml-output').value = jsonToYaml(currentPatch);
            refreshExport();
        }

        function handleDragStart(e, index) {
            dragSrcIndex = index;
            e.target.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }

        function handleDragOver(e) {
            if (e.preventDefault) { e.preventDefault(); }
            return false;
        }

        function handleDrop(e, targetIndex) {
            if (e.stopPropagation) { e.stopPropagation(); }
            if (dragSrcIndex !== targetIndex) {
                const item = currentPatch.chain.splice(dragSrcIndex, 1)[0];
                currentPatch.chain.splice(targetIndex, 0, item);
                renderEditor();
            }
            return false;
        }

        function handleDragEnd(e) {
            e.target.classList.remove('dragging');
        }

        function addComponent() {
            currentPatch.chain.push({
                type: 'pedal',
                model: 'NEW_COMPONENT',
                settings: { gain: 0.5, tone: 0.5 }
            });
            renderEditor();
        }

        function removeComponent(idx) {
            currentPatch.chain.splice(idx, 1);
            renderEditor();
        }

        function updateComp(idx, field, val) {
            currentPatch.chain[idx][field] = val;
            if (field === 'type') {
                renderEditor();
            } else {
                updateYamlView();
            }
        }

        function updateSetting(compIdx, key, newVal, isKey = false) {
            const settings = currentPatch.chain[compIdx].settings;
            if (isKey) {
                const val = settings[key];
                delete settings[key];
                settings[newVal] = val;
            } else {
                const num = parseFloat(newVal);
                settings[key] = isNaN(num) ? newVal : num;
            }
            updateYamlView();
        }

        async function savePatch() {
            updateYamlView(); 
            const res = await fetch('/save?file=' + filename, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentPatch)
            });
            if (res.ok) { showToast('DATA_SAVED_SUCCESS'); }
        }

        function renderEditor() {
            const chainDiv = document.getElementById('signal-chain');
            if (!chainDiv) { return; }
            chainDiv.innerHTML = '';
            
            if (!currentPatch.chain) currentPatch.chain = [];

            currentPatch.chain.forEach((comp, idx) => {
                const block = document.createElement('div');
                block.className = `component ${comp.type.toLowerCase()}`;
                block.draggable = true;
                block.setAttribute('ondragstart', `handleDragStart(event, ${idx})`);
                block.setAttribute('ondragover', `handleDragOver(event)`);
                block.setAttribute('ondrop', `handleDrop(event, ${idx})`);
                block.setAttribute('ondragend', `handleDragEnd(event)`);
                
                let settingsHtml = '';
                for (let k in comp.settings) {
                    settingsHtml += `
                        <div class="setting-row">
                            <input value="${k}" oninput="updateSetting(${idx}, '${k}', this.value, true)">
                            <input value="${comp.settings[k]}" oninput="updateSetting(${idx}, '${k}', this.value)">
                        </div>
                    `;
                }

                block.innerHTML = `
                    <div class="comp-header">
                        <div style="display:flex; align-items:center;">
                            <span class="drag-handle">&#9776;</span>
                            <select onchange="updateComp(${idx}, 'type', this.value)">
                                <option value="pedal" ${comp.type==='pedal'?'selected':''}>PEDAL</option>
                                <option value="amp" ${comp.type==='amp'?'selected':''}>AMP</option>
                                <option value="cab" ${comp.type==='cab'?'selected':''}>CAB</option>
                            </select>
                        </div>
                        <span style="cursor:pointer; color:var(--warning)" onclick="removeComponent(${idx})">[ REMOVE ]</span>
                    </div>
                    <input style="width:100%; margin-bottom:15px; font-weight:bold; border:none; background:transparent; font-size:1.1em; padding:0; color:var(--text-bright);" 
                           value="${comp.model}" oninput="updateComp(${idx}, 'model', this.value)">
                    <div class="settings-editor">
                        ${settingsHtml}
                    </div>
                `;
                chainDiv.appendChild(block);
                if (idx < currentPatch.chain.length - 1) {
                    const arrow = document.createElement('div');
                    arrow.className = 'arrow';
                    arrow.innerHTML = '&darr;';
                    chainDiv.appendChild(arrow);
                }
            });
            updateYamlView();
        }

        document.getElementById('patch-name').oninput = updateYamlView;
        document.getElementById('patch-desc').oninput = updateYamlView;
        document.getElementById('patch-tags').oninput = updateYamlView;
        
        window.onload = renderEditor;
    </script>
</body>
</html>
"""

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Meta-Patch Library</title>
    <style>
        :root {
            --bg: #002b36;
            --panel: #073642;
            --text: #839496;
            --accent: #268bd2;
            --border: #586e75;
        }
        body { font-family: 'ui-monospace', monospace; background: var(--bg); color: var(--text); padding: 50px; line-height: 1.6; }
        h1 { border-bottom: 1px solid var(--border); padding-bottom: 15px; color: #93a1a1; display: flex; justify-content: space-between; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; margin-top: 30px; }
        .card { border: 1px solid var(--border); padding: 20px; cursor: pointer; background: var(--panel); transition: all 0.2s; }
        .card:hover { border-color: var(--accent); transform: translateY(-2px); }
        .btn { border: 1px solid var(--accent); color: var(--accent); background: transparent; padding: 10px 25px; cursor: pointer; text-decoration: none; font-size: 0.9em; }
        .btn:hover { background: var(--accent); color: var(--bg); }
        .tag { font-size: 0.7em; background: #586e75; color: #eee; padding: 3px 8px; margin-right: 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>META-PATCH_LIBRARY <a href="/?new=true" class="btn">[ + NEW_PATCH ]</a></h1>
    <div class="grid">[[CARDS]]</div>
</body>
</html>
"""

class PatchHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            url = urlparse(self.path)
            params = parse_qs(url.query)
            if url.path == "/":
                if "patch" in params:
                    self.render_editor(params["patch"][0])
                elif "new" in params:
                    self.render_editor(None)
                else:
                    self.render_index()
            else:
                super().do_GET()
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"SERVER_ERROR:\\n{traceback.format_exc()}".encode("utf-8"))

    def do_POST(self):
        if self.path.startswith("/save"):
            params = parse_qs(urlparse(self.path).query)
            filename = params.get("file", ["new-patch.yaml"])[0]
            content_length = int(self.headers['Content-Length'])
            patch_data = json.loads(self.rfile.read(content_length))
            with open(PATCH_DIR / filename, "w", encoding="utf-8") as f:
                yaml.dump(patch_data, f, sort_keys=False)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        elif self.path == "/api/export-preview":
            content_length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(content_length))
            result, error = generate_preview(body.get("yaml_content", ""), body.get("platform", "podgo"))
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            payload = {"error": error} if error else {"output": result}
            self.wfile.write(json.dumps(payload).encode("utf-8"))

    def render_index(self):
        files = sorted(list(PATCH_DIR.glob("*.yaml")) + list(PATCH_DIR.glob("*.yml")))
        cards = []
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as stream:
                    data = yaml.safe_load(stream)
                    tags = "".join([f'<span class="tag">{t}</span>' for t in data.get("tags", [])])
                    cards.append(f"""
                    <div class="card" onclick="window.location.href='/?patch={f.name}'">
                        <div style="font-weight:bold; color:var(--accent); font-size: 1.1em;">{data.get('name', f.name)}</div>
                        <div style="font-size:0.85em; margin: 15px 0; min-height: 40px;">{data.get('description', '')}</div>
                        <div>{tags}</div>
                    </div>
                    """)
            except Exception as e:
                print(f"Error loading {f}: {e}")
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(INDEX_TEMPLATE.replace("[[CARDS]]", "".join(cards)).encode("utf-8"))

    def render_editor(self, filename):
        if filename:
            with open(PATCH_DIR / filename, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            file_val = filename
        else:
            data = {"name": "NEW_PATCH", "description": "", "tags": [], "chain": []}
            file_val = "new-patch.yaml"

        tags_str = ", ".join(data.get("tags", []))
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        # Consistent placeholder replacement
        html = HTML_TEMPLATE.replace("[[FILENAME]]", file_val)
        html = html.replace("[[PATCH_NAME]]", str(data.get('name', '')))
        html = html.replace("[[PATCH_DESC]]", str(data.get('description', '')))
        html = html.replace("[[PATCH_TAGS]]", tags_str)
        html = html.replace("[[PATCH_JSON]]", json.dumps(data))
        
        self.wfile.write(html.encode("utf-8"))

if __name__ == "__main__":
    PATCH_DIR.mkdir(exist_ok=True)
    with socketserver.TCPServer(("", PORT), PatchHandler) as httpd:
        print(f"TONE-IDE running at http://localhost:{PORT}")
        httpd.serve_forever()
