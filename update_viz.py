file_path = r"d:\code\aircraft-design-skill\aircraft_design\visualization_3d.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.strip().startswith("def generate_three_view_html"):
        start_idx = i
    if line.strip().startswith("def build_vertical_tail_airfoil_loft_mesh"):
        end_idx = i
        break

if start_idx == -1 or end_idx == -1:
    print("Could not find start or end markers.")
    exit(1)

# Keep lines before start_idx
# Keep lines from end_idx onwards
# Insert new code in between

new_code = r'''def generate_three_view_html(geometry: dict, output_path: str):
    """
    Generate a standalone HTML file visualizing the geometry with Three.js.

    Args:
        geometry (dict): The geometry dictionary containing 'fuselage', 'wing', 'tail', etc.
        output_path (str): The path to save the generated HTML file.
    """
    import json

    # 1. Build Mesh Parts
    mesh_parts = []

    # Fuselage
    fus_st = geometry.get("fuselage", {}).get("stations")
    if fus_st:
        # Increase resolution for better visualization
        mesh_parts.append(build_fuselage_loft(stations=fus_st, n_circ=48))

    # Wing
    wing = geometry.get("wing", {})
    wing_pf = wing.get("planform")
    if wing_pf:
        root_af = wing.get("root_airfoil", {}).get("coords")
        tip_af = wing.get("tip_airfoil", {}).get("coords")
        if not root_af:
            from .geometry_detailed import naca4_coordinates
            root_af = naca4_coordinates("0012")

        mesh_parts.extend(build_wing_airfoil_loft_mesh(
            root_airfoil_coords=root_af,
            tip_airfoil_coords=tip_af,
            s_ref_m2=wing_pf.get("s_ref_m2", 10.0),
            aspect_ratio=wing_pf.get("aspect_ratio", 6.0),
            taper_ratio=wing_pf.get("taper_ratio", 1.0),
            sweep_quarter_chord_deg=wing_pf.get("sweep_quarter_chord_deg", 0.0),
            x_offset_m=wing_pf.get("x_offset_m", 0.0),
            y_offset_m=wing_pf.get("y_offset_m", 0.0),
            z_offset_m=wing_pf.get("z_offset_m", 0.0),
            dihedral_deg=wing_pf.get("dihedral_deg", 0.0),
            incidence_deg=wing_pf.get("incidence_deg", 0.0),
            control_surfaces=wing.get("controls", {}).get("control_surfaces"),
            name_prefix="wing"
        ))

    # Tail
    tail = geometry.get("tail", {})
    for surf in tail.get("surfaces", []):
        source = surf.get("source", "horizontal")
        src_def = tail.get(source, {})
        root_af_t = src_def.get("root_airfoil", {}).get("coords")
        tip_af_t = src_def.get("tip_airfoil", {}).get("coords")

        if not root_af_t:
            from .geometry_detailed import naca4_coordinates
            root_af_t = naca4_coordinates("0012")

        builder = surf.get("builder", "wing_loft")

        if builder == "wing_loft":
            mesh_parts.extend(build_wing_airfoil_loft_mesh(
                root_airfoil_coords=root_af_t,
                tip_airfoil_coords=tip_af_t,
                s_ref_m2=surf.get("s_ref_m2", 1.0),
                aspect_ratio=surf.get("aspect_ratio", 4.0),
                taper_ratio=surf.get("taper_ratio", 0.6),
                sweep_quarter_chord_deg=surf.get("sweep_quarter_chord_deg", 0.0),
                x_offset_m=surf.get("x_offset_m", 0.0),
                y_offset_m=surf.get("y_offset_m", 0.0),
                z_offset_m=surf.get("z_offset_m", 0.0),
                dihedral_deg=surf.get("dihedral_deg", 0.0),
                incidence_deg=surf.get("incidence_deg", 0.0),
                name_prefix=surf.get("name_prefix", "tail"),
                color="#e377c2"
            ))
        elif builder == "vertical_loft":
             pass

    # 2. Serialize parts to JSON
    parts_data = []
    for p in mesh_parts:
        parts_data.append({
            "name": p.name,
            "color": p.color,
            "vertices": p.vertices,
            "indices": p.indices
        })

    parts_json = json.dumps(parts_data)

    # 3. Enhanced Template
    html_template = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Aircraft Geometry Analysis</title>
  <style>
    :root { --bg: #1a1a1a; --panel: #2d2d2d; --text: #e0e0e0; --accent: #4a90e2; }
    body { margin: 0; background: var(--bg); color: var(--text); font-family: 'Segoe UI', Roboto, sans-serif; overflow: hidden; height: 100vh; display: flex; flex-direction: column; }

    #toolbar {
        height: 40px; background: var(--panel); border-bottom: 1px solid #444;
        display: flex; align-items: center; padding: 0 16px; gap: 16px; font-size: 14px;
    }
    .btn {
        background: #444; border: none; color: #fff; padding: 4px 12px; border-radius: 4px; cursor: pointer; transition: background 0.2s;
    }
    .btn:hover { background: #555; }
    .btn.active { background: var(--accent); }
    .info-tag { font-family: monospace; color: #aaa; }

    #workspace {
        flex: 1; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 2px; background: #000;
    }
    .view-container { position: relative; background: #151515; overflow: hidden; }
    .view-label {
        position: absolute; left: 8px; top: 8px;
        background: rgba(0,0,0,0.6); color: #ccc; padding: 2px 8px; border-radius: 4px;
        font-size: 12px; pointer-events: none; user-select: none;
    }
    canvas { display: block; width: 100%; height: 100%; outline: none; }

    /* Loading overlay */
    #loader {
        position: fixed; inset: 0; background: var(--bg); display: flex; justify-content: center; align-items: center; z-index: 999; transition: opacity 0.5s;
    }
  </style>
  <script type="importmap">
  {
    "imports": {
      "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
      "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
    }
  }
  </script>
</head>
<body>
  <div id="loader">Loading Geometry...</div>

  <div id="toolbar">
    <b>Aircraft Viz</b>
    <span class="info-tag" id="dims"></span>
    <div style="flex:1"></div>
    <button class="btn" id="btn-wireframe" title="Toggle Wireframe (W)">Wireframe</button>
    <button class="btn" id="btn-grid" title="Toggle Grid (G)">Grid</button>
    <button class="btn" id="btn-reset" title="Reset Views (R)">Reset</button>
  </div>

  <div id="workspace">
    <div class="view-container">
        <div class="view-label">Top (X-Y)</div>
        <canvas id="cv_top"></canvas>
    </div>
    <div class="view-container">
        <div class="view-label">Side (X-Z)</div>
        <canvas id="cv_side"></canvas>
    </div>
    <div class="view-container">
        <div class="view-label">Front (Y-Z)</div>
        <canvas id="cv_front"></canvas>
    </div>
    <div class="view-container">
        <div class="view-label">Perspective</div>
        <canvas id="cv_iso"></canvas>
    </div>
  </div>

  <script type="module">
    import * as THREE from 'three';
    import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

    // Data injected from Python
    const parts = PARAMS_PLACEHOLDER;

    // State
    const state = {
        wireframe: false,
        showGrid: true
    };

    // Scene Setup
    const scenes = {
        ortho: new THREE.Scene(),
        iso: new THREE.Scene()
    };
    scenes.ortho.background = new THREE.Color(0x151515);
    scenes.iso.background = new THREE.Color(0x202025);

    // Lights
    function setupLights(scene) {
        const ambient = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambient);
        const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.6);
        hemi.position.set(0, 0, 20);
        scene.add(hemi);
        const dir = new THREE.DirectionalLight(0xffffff, 1.0);
        dir.position.set(10, -20, 30);
        scene.add(dir);
    }
    setupLights(scenes.ortho);
    setupLights(scenes.iso);

    // Geometry Processing
    const materials = [];
    const mainGroup = new THREE.Group();

    // Calculate bounds
    let bounds = {minX:Infinity, maxX:-Infinity, minY:Infinity, maxY:-Infinity, minZ:Infinity, maxZ:-Infinity};

    parts.forEach(p => {
        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(p.vertices), 3));
        geo.setIndex(new THREE.BufferAttribute(new Uint32Array(p.indices), 1));
        geo.computeVertexNormals();

        const mat = new THREE.MeshStandardMaterial({
            color: new THREE.Color(p.color),
            metalness: 0.1,
            roughness: 0.7,
            side: THREE.DoubleSide,
            polygonOffset: true,
            polygonOffsetFactor: 1,
            polygonOffsetUnits: 1
        });
        materials.push(mat);

        const mesh = new THREE.Mesh(geo, mat);
        mainGroup.add(mesh);

        // Edges for better definition
        const edges = new THREE.EdgesGeometry(geo, 30);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.2 }));
        mesh.add(line);

        // Bounds calc
        for(let i=0; i<p.vertices.length; i+=3) {
            const x=p.vertices[i], y=p.vertices[i+1], z=p.vertices[i+2];
            bounds.minX = Math.min(bounds.minX, x); bounds.maxX = Math.max(bounds.maxX, x);
            bounds.minY = Math.min(bounds.minY, y); bounds.maxY = Math.max(bounds.maxY, y);
            bounds.minZ = Math.min(bounds.minZ, z); bounds.maxZ = Math.max(bounds.maxZ, z);
        }
    });

    // Center geometry
    const size = new THREE.Vector3(bounds.maxX-bounds.minX, bounds.maxY-bounds.minY, bounds.maxZ-bounds.minZ);
    const center = new THREE.Vector3((bounds.minX+bounds.maxX)*0.5, (bounds.minY+bounds.maxY)*0.5, (bounds.minZ+bounds.maxZ)*0.5);
    mainGroup.position.sub(center); // Center at origin

    // Clone for both scenes
    scenes.iso.add(mainGroup);
    scenes.ortho.add(mainGroup.clone());

    // Info Update
    document.getElementById('dims').textContent = `L:${size.x.toFixed(2)}m W:${size.y.toFixed(2)}m H:${size.z.toFixed(2)}m`;

    // Helpers (Grids/Axes)
    const helpers = new THREE.Group();
    const gridColor = 0x333333;
    const axisSize = Math.max(size.x, size.y, size.z) * 1.5;

    // Top Grid (XY)
    const gridXY = new THREE.GridHelper(axisSize, 20, 0x555555, gridColor);
    gridXY.rotation.x = Math.PI/2;
    helpers.add(gridXY);

    // Axes
    helpers.add(new THREE.AxesHelper(axisSize * 0.1));

    scenes.ortho.add(helpers);
    scenes.iso.add(helpers.clone());

    // Cameras & Renderers
    const viewRadius = Math.max(size.x, size.y, size.z) * 0.8;

    const views = [
        { id: 'cv_top',   type: 'ortho', axis: 'z', up: [0,1,0], pos: [0,0,100] },
        { id: 'cv_side',  type: 'ortho', axis: 'y', up: [0,0,1], pos: [0,-100,0] },
        { id: 'cv_front', type: 'ortho', axis: 'x', up: [0,0,1], pos: [100,0,0] },
        { id: 'cv_iso',   type: 'persp', pos: [viewRadius*1.5, -viewRadius*1.5, viewRadius] }
    ];

    const renderMap = {};

    views.forEach(v => {
        const cv = document.getElementById(v.id);
        const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true });
        renderer.setPixelRatio(window.devicePixelRatio);

        let camera;
        if (v.type === 'ortho') {
            camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10000);
            camera.zoom = 1;
        } else {
            camera = new THREE.PerspectiveCamera(45, 1, 0.1, 10000);
        }

        camera.up.set(...(v.up || [0,0,1]));
        camera.position.set(...v.pos);
        camera.lookAt(0,0,0);

        // Controls
        const controls = new OrbitControls(camera, cv);
        if (v.type === 'ortho') {
            controls.enableRotate = false;
            controls.mouseButtons = {
                LEFT: THREE.MOUSE.PAN,
                MIDDLE: THREE.MOUSE.DOLLY,
                RIGHT: THREE.MOUSE.PAN
            };
        } else {
            controls.enableDamping = true;
        }

        renderMap[v.id] = { renderer, camera, controls, scene: v.type==='persp'?scenes.iso:scenes.ortho };
    });

    // Resize Handling
    function handleResize() {
        views.forEach(v => {
            const item = renderMap[v.id];
            const cv = item.renderer.domElement;
            const width = cv.parentElement.clientWidth;
            const height = cv.parentElement.clientHeight;

            item.renderer.setSize(width, height, false);

            if (item.camera.isOrthographicCamera) {
                const aspect = width / height;
                const frustumSize = viewRadius * 2.5; // Initial zoom fit

                // Adjust frustum based on aspect ratio to keep object visible
                item.camera.left = -frustumSize * aspect / 2;
                item.camera.right = frustumSize * aspect / 2;
                item.camera.top = frustumSize / 2;
                item.camera.bottom = -frustumSize / 2;
            } else {
                item.camera.aspect = width / height;
            }
            item.camera.updateProjectionMatrix();
        });
    }

    window.addEventListener('resize', handleResize);
    // Initial size
    setTimeout(handleResize, 50);

    // Loop
    function animate() {
        requestAnimationFrame(animate);
        Object.values(renderMap).forEach(item => {
            item.controls.update();
            item.renderer.render(item.scene, item.camera);
        });
    }
    animate();

    // UI Logic
    document.getElementById('loader').style.opacity = 0;
    setTimeout(() => document.getElementById('loader').remove(), 500);

    // Wireframe Toggle
    function toggleWireframe() {
        state.wireframe = !state.wireframe;
        materials.forEach(m => m.wireframe = state.wireframe);
        document.getElementById('btn-wireframe').classList.toggle('active', state.wireframe);
    }
    document.getElementById('btn-wireframe').onclick = toggleWireframe;

    // Grid Toggle
    function toggleGrid() {
        state.showGrid = !state.showGrid;
        helpers.visible = state.showGrid;
        document.getElementById('btn-grid').classList.toggle('active', !state.showGrid); // Invert logic visually if needed, but here active means ON
    }
    document.getElementById('btn-grid').onclick = toggleGrid;

    // Reset
    document.getElementById('btn-reset').onclick = () => {
        views.forEach(v => {
            const item = renderMap[v.id];
            item.controls.reset();
            item.camera.position.set(...v.pos);
            item.camera.lookAt(0,0,0);
            if(item.camera.isOrthographicCamera) item.camera.zoom = 1;
            item.camera.updateProjectionMatrix();
        });
        handleResize(); // re-fit
    };

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
        if (e.key.toLowerCase() === 'w') toggleWireframe();
        if (e.key.toLowerCase() === 'g') toggleGrid();
        if (e.key.toLowerCase() === 'r') document.getElementById('btn-reset').click();
    });

  </script>
</body>
</html>"""

    html = html_template.replace("PARAMS_PLACEHOLDER", parts_json)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
'''

# New file content
new_content = lines[:start_idx]
new_content.append(new_code + "\n\n\n")
new_content.extend(lines[end_idx:])

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_content)

print("Successfully updated visualization_3d.py")
