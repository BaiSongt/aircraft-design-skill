import multiprocessing as mp
import os
import queue
import sys
import threading
import time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


def _get_qvtk_class():
    try:
        from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    except Exception:
        return None
    return QVTKRenderWindowInteractor


def _add_light(vtk, renderer):
    light = vtk.vtkLight()
    light.SetLightTypeToSceneLight()
    light.SetPosition(1.0, 1.0, 1.0)
    light.SetFocalPoint(0.0, 0.0, 0.0)
    light.SetIntensity(1.0)
    renderer.AddLight(light)


def _resolve_color(named_colors, color):
    if isinstance(color, (list, tuple)) and len(color) == 3:
        return color
    if isinstance(color, str):
        try:
            return named_colors.GetColor3d(color)
        except Exception:
            return named_colors.GetColor3d("LightGray")
    return named_colors.GetColor3d("LightGray")


def _clear_actors(renderer, actors):
    for actor in actors:
        renderer.RemoveActor(actor)
    actors.clear()


def _add_polydata(vtk, renderer, actors, named_colors, polydata, color="LightGray", show_edges=True, clip_plane=None):
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(polydata)
    normals.AutoOrientNormalsOn()
    normals.ConsistencyOn()
    normals.SplittingOff()
    normals.Update()
    mapper = vtk.vtkPolyDataMapper()
    clipper = None
    if clip_plane is not None:
        clipper = vtk.vtkClipPolyData()
        clipper.SetInputConnection(normals.GetOutputPort())
        clipper.SetClipFunction(clip_plane)
        clipper.InsideOutOn()
        clipper.Update()
        mapper.SetInputConnection(clipper.GetOutputPort())
    else:
        mapper.SetInputConnection(normals.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(_resolve_color(named_colors, color))
    actor.GetProperty().SetAmbient(0.3)
    actor.GetProperty().SetDiffuse(0.7)
    actor.GetProperty().SetSpecular(0.1)
    actor.GetProperty().SetSpecularPower(10.0)
    if show_edges:
        actor.GetProperty().SetEdgeVisibility(1)
        actor.GetProperty().SetEdgeColor(0.0, 0.0, 0.0)
        actor.GetProperty().SetLineWidth(1.0)
    renderer.AddActor(actor)
    actors.append(actor)
    return actor, clipper


def _apply_view_mode(renderer, view_mode):
    bounds = renderer.ComputeVisiblePropBounds()
    if not bounds or bounds[1] < bounds[0]:
        center = (0.0, 0.0, 0.0)
        size = 10.0
    else:
        center = (
            (bounds[0] + bounds[1]) * 0.5,
            (bounds[2] + bounds[3]) * 0.5,
            (bounds[4] + bounds[5]) * 0.5,
        )
        size = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4], 1.0)
    dist = size * 2.0
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(center[0], center[1], center[2])
    if view_mode == "top":
        camera.SetPosition(center[0], center[1], center[2] + dist)
        camera.SetViewUp(0.0, 1.0, 0.0)
    elif view_mode == "side":
        camera.SetPosition(center[0], center[1] + dist, center[2])
        camera.SetViewUp(0.0, 0.0, 1.0)
    else:
        camera.SetPosition(center[0] + dist, center[1] + dist, center[2] + dist)
        camera.SetViewUp(0.0, 0.0, 1.0)
    renderer.ResetCameraClippingRange()


def _build_mesh_from_geom(vtk, renderer, actors, named_colors, geom_dict, clip_plane=None):
    components = ["fuselage", "wing", "htail", "vtail", "horizontal_tail", "vertical_tail"]
    has_mesh_data = False
    clippers = []
    for name in components:
        comp = geom_dict.get(name)
        if not comp:
            if name == "htail":
                comp = geom_dict.get("horizontal_tail")
            if name == "vtail":
                comp = geom_dict.get("vertical_tail")
        if not comp:
            continue
        if "vertices" in comp and "faces" in comp:
            has_mesh_data = True
            verts = comp["vertices"]
            faces = comp["faces"]
            points = vtk.vtkPoints()
            for v in verts:
                points.InsertNextPoint(v[0], v[1], v[2])
            polys = vtk.vtkCellArray()
            for f in faces:
                polygon = vtk.vtkPolygon()
                polygon.GetPointIds().SetNumberOfIds(len(f))
                for i, idx in enumerate(f):
                    polygon.GetPointIds().SetId(i, idx)
                polys.InsertNextCell(polygon)
            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(polys)
            color = comp.get("color", "LightGray")
            _, clipper = _add_polydata(
                vtk,
                renderer,
                actors,
                named_colors,
                polydata,
                color=color,
                show_edges=True,
                clip_plane=clip_plane,
            )
            if clipper is not None:
                clippers.append(clipper)
    return has_mesh_data, clippers


def _build_parametric(vtk, renderer, actors, named_colors, geom_dict, clip_plane=None):
    clippers = []
    fus = geom_dict.get("fuselage", {})
    length = fus.get("length_m") or geom_dict.get("fuselage_length_m", 10.0)
    diameter = fus.get("diameter_m") or geom_dict.get("fuselage_diameter_m", 1.0)

    cylinder = vtk.vtkCylinderSource()
    cylinder.SetRadius(diameter / 2)
    cylinder.SetHeight(length)
    cylinder.SetResolution(32)
    cylinder.Update()

    transform = vtk.vtkTransform()
    transform.RotateY(90)
    transform.Translate(length / 2, 0, 0)
    transform_filter = vtk.vtkTransformPolyDataFilter()
    transform_filter.SetInputData(cylinder.GetOutput())
    transform_filter.SetTransform(transform)
    transform_filter.Update()
    _, clipper = _add_polydata(
        vtk,
        renderer,
        actors,
        named_colors,
        transform_filter.GetOutput(),
        color="LightGray",
        show_edges=False,
        clip_plane=clip_plane,
    )
    if clipper is not None:
        clippers.append(clipper)

    wing = geom_dict.get("wing", {})
    area = wing.get("s_ref_m2") or geom_dict.get("s_wing", 20.0)
    aspect = wing.get("aspect_ratio") or geom_dict.get("aspect_ratio", 3.0)
    sweep = wing.get("sweep_deg") or geom_dict.get("sweep_deg", 0)
    taper = wing.get("taper_ratio") or geom_dict.get("taper_ratio", 1.0)

    if area > 0:
        span = (area * aspect) ** 0.5
        c_root = 2 * area / (span * (1 + taper))
        c_tip = c_root * taper

        x_le_root = length * 0.4
        y_root = 0
        z_root = 0

        tip_y = span / 2
        tip_x = x_le_root + (span / 2) * vtk.vtkMath.Tan(vtk.vtkMath.RadiansFromDegrees(sweep))

        pts = [
            (x_le_root, y_root, z_root),
            (tip_x, tip_y, z_root),
            (tip_x + c_tip, tip_y, z_root),
            (x_le_root + c_root, y_root, z_root),
        ]
        pts_l = [
            (x_le_root, -y_root, z_root),
            (tip_x, -tip_y, z_root),
            (tip_x + c_tip, -tip_y, z_root),
            (x_le_root + c_root, -y_root, z_root),
        ]

        points = vtk.vtkPoints()
        for v in pts + pts_l:
            points.InsertNextPoint(v[0], v[1], v[2])

        polys = vtk.vtkCellArray()
        poly1 = vtk.vtkPolygon()
        poly1.GetPointIds().SetNumberOfIds(4)
        for i in range(4):
            poly1.GetPointIds().SetId(i, i)
        polys.InsertNextCell(poly1)

        poly2 = vtk.vtkPolygon()
        poly2.GetPointIds().SetNumberOfIds(4)
        for i in range(4):
            poly2.GetPointIds().SetId(i, i + 4)
        polys.InsertNextCell(poly2)

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(polys)
        _, clipper = _add_polydata(
            vtk,
            renderer,
            actors,
            named_colors,
            polydata,
            color="LightBlue",
            show_edges=True,
            clip_plane=clip_plane,
        )
        if clipper is not None:
            clippers.append(clipper)
    return clippers


def _load_file(vtk, renderer, actors, named_colors, path, clip_plane=None):
    ext = path.lower().split(".")[-1]
    reader = None
    if ext == "obj":
        reader = vtk.vtkOBJReader()
    elif ext == "stl":
        reader = vtk.vtkSTLReader()
    elif ext == "ply":
        reader = vtk.vtkPLYReader()
    if not reader:
        return False, []
    reader.SetFileName(path)
    reader.Update()
    polydata = reader.GetOutput()
    _, clipper = _add_polydata(
        vtk, renderer, actors, named_colors, polydata, color="White", show_edges=True, clip_plane=clip_plane
    )
    clippers = [clipper] if clipper is not None else []
    return True, clippers


def _vtk_worker(command_queue, result_queue):
    try:
        import vtk
    except Exception:
        result_queue.put(("error", -1, "vtk_import"))
        return

    views = {}

    def create_view(view_id, view_mode):
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(1.0, 1.0, 1.0)
        use_offscreen = sys.platform != "darwin"
        if use_offscreen and hasattr(vtk, "vtkOSOpenGLRenderWindow"):
            render_window = vtk.vtkOSOpenGLRenderWindow()
        else:
            render_window = vtk.vtkRenderWindow()
        if hasattr(render_window, "SetOffScreenRendering"):
            render_window.SetOffScreenRendering(1 if use_offscreen else 0)
        if hasattr(render_window, "SetShowWindow"):
            render_window.SetShowWindow(False)
        _add_light(vtk, renderer)
        render_window.SetSize(800, 600)
        render_window.AddRenderer(renderer)
        views[view_id] = {
            "renderer": renderer,
            "render_window": render_window,
            "named_colors": vtk.vtkNamedColors(),
            "actors": [],
            "view_mode": view_mode or "iso",
            "offscreen": use_offscreen,
        }

    def render_frame(view, view_id, width, height):
        render_window = view["render_window"]
        if width and height:
            render_window.SetSize(max(2, int(width)), max(2, int(height)))
        else:
            size = render_window.GetSize()
            if not size or size[0] < 2 or size[1] < 2:
                render_window.SetSize(800, 600)
        view["renderer"].ResetCamera()
        _apply_view_mode(view["renderer"], view["view_mode"])
        render_window.Render()
        w2if = vtk.vtkWindowToImageFilter()
        w2if.SetInput(render_window)
        if view.get("offscreen", True):
            w2if.ReadFrontBufferOff()
        else:
            w2if.ReadFrontBufferOn()
        w2if.SetInputBufferTypeToRGBA()
        w2if.Update()
        writer = vtk.vtkPNGWriter()
        writer.SetWriteToMemory(True)
        writer.SetInputConnection(w2if.GetOutputPort())
        writer.Write()
        result = writer.GetResult()
        if result:
            result_queue.put(("frame", view_id, bytes(result)))
        else:
            result_queue.put(("error", view_id, "empty_frame"))

    while True:
        cmd = command_queue.get()
        if not isinstance(cmd, dict):
            continue
        cmd_type = cmd.get("type")
        if cmd_type == "stop":
            break
        view_id = cmd.get("view_id")
        try:
            if cmd_type == "init":
                create_view(view_id, cmd.get("view_mode"))
            elif cmd_type == "close":
                if view_id in views:
                    views.pop(view_id, None)
            else:
                if view_id not in views:
                    create_view(view_id, cmd.get("view_mode"))
                view = views[view_id]
                if cmd_type == "clear":
                    _clear_actors(view["renderer"], view["actors"])
                    render_frame(view, view_id, cmd.get("width"), cmd.get("height"))
                elif cmd_type == "reset":
                    render_frame(view, view_id, cmd.get("width"), cmd.get("height"))
                elif cmd_type == "load_file":
                    _clear_actors(view["renderer"], view["actors"])
                    ok, _ = _load_file(vtk, view["renderer"], view["actors"], view["named_colors"], cmd.get("path", ""))
                    if ok:
                        render_frame(view, view_id, cmd.get("width"), cmd.get("height"))
                elif cmd_type == "update":
                    _clear_actors(view["renderer"], view["actors"])
                    geom = cmd.get("geometry") or {}
                    has_mesh, _ = _build_mesh_from_geom(
                        vtk, view["renderer"], view["actors"], view["named_colors"], geom
                    )
                    if not has_mesh:
                        _build_parametric(vtk, view["renderer"], view["actors"], view["named_colors"], geom)
                    render_frame(view, view_id, cmd.get("width"), cmd.get("height"))
        except Exception as e:
            result_queue.put(("error", view_id if view_id is not None else -1, str(e)))


class VTKRenderManager:
    def __init__(self):
        self._ctx = mp.get_context("spawn")
        self._command_queue = self._ctx.Queue()
        self._result_queue = self._ctx.Queue()
        self._process = self._ctx.Process(
            target=_vtk_worker,
            args=(self._command_queue, self._result_queue),
            daemon=True,
        )
        self._process.start()
        self._lock = threading.Lock()
        self._latest = {}
        self._errors = {}
        self._global_error = None
        self._refcount = 0
        self._next_view_id = 1
        self._stopping = False
        self._idle_timer = None
        self._last_frame = None
        self._reader_thread = threading.Thread(target=self._read_results, daemon=True)
        self._reader_thread.start()

    def _read_results(self):
        while True:
            try:
                item = self._result_queue.get()
            except (EOFError, OSError):
                break
            if not isinstance(item, tuple) or len(item) < 3:
                continue
            kind, view_id, payload = item[0], item[1], item[2]
            with self._lock:
                if kind == "frame":
                    self._latest[view_id] = payload
                    self._last_frame = payload
                elif kind == "error":
                    if view_id == -1:
                        self._global_error = payload
                    else:
                        self._errors[view_id] = payload

    def acquire(self):
        with self._lock:
            self._refcount += 1
            if self._idle_timer:
                self._idle_timer.cancel()
                self._idle_timer = None

    def release(self):
        with self._lock:
            self._refcount -= 1
            if self._refcount <= 0:
                self._refcount = 0
                self._schedule_stop()

    def _schedule_stop(self, delay_s: float = 10.0):
        if self._idle_timer:
            self._idle_timer.cancel()
        self._idle_timer = threading.Timer(delay_s, self.stop)
        self._idle_timer.daemon = True
        self._idle_timer.start()

    def stop(self):
        if self._stopping:
            return
        self._stopping = True
        if self._idle_timer:
            self._idle_timer.cancel()
            self._idle_timer = None
        try:
            self._command_queue.put_nowait({"type": "stop"})
        except queue.Full:
            pass
        if self._process.is_alive():
            self._process.join(timeout=1.0)
        if self._process.is_alive():
            self._process.terminate()
        try:
            self._command_queue.close()
            self._command_queue.cancel_join_thread()
        except Exception:
            pass
        try:
            self._result_queue.close()
            self._result_queue.cancel_join_thread()
        except Exception:
            pass

    def create_view(self, view_mode):
        with self._lock:
            view_id = self._next_view_id
            self._next_view_id += 1
        self.send({"type": "init", "view_id": view_id, "view_mode": view_mode})
        return view_id

    def destroy_view(self, view_id):
        self.send({"type": "close", "view_id": view_id})
        with self._lock:
            self._latest.pop(view_id, None)
            self._errors.pop(view_id, None)

    def send(self, cmd):
        if self._stopping:
            return
        try:
            self._command_queue.put_nowait(cmd)
        except queue.Full:
            return

    def get_latest(self, view_id):
        with self._lock:
            frame = self._latest.pop(view_id, None)
            error = self._errors.pop(view_id, None)
            global_error = self._global_error
        return frame, error, global_error

    def get_cached_frame(self):
        with self._lock:
            return self._last_frame


_VTK_MANAGER = None


def _get_vtk_manager():
    global _VTK_MANAGER
    if _VTK_MANAGER is None:
        _VTK_MANAGER = VTKRenderManager()
    return _VTK_MANAGER


class PyVistaWidget(QWidget):
    def __init__(self, parent=None, view_mode="iso"):
        super().__init__(parent)
        self.view_mode = view_mode
        layout = QVBoxLayout(self)
        disable_qvtk = os.environ.get("AD_DISABLE_QVTK") == "1"
        force_qvtk = os.environ.get("AD_FORCE_QVTK") == "1"
        self._qvtk_class = None if disable_qvtk else _get_qvtk_class()
        self._use_qvtk = bool(self._qvtk_class) and (force_qvtk or sys.platform == "darwin")
        self._manager = None
        self._view_id = None
        self._pending_commands = []
        self._manager_ready = False
        self._vtk_ready = False
        self._renderer = None
        self._named_colors = None
        self._actors = []
        self._render_window = None
        self._pending_geometry = None
        self._last_source = None
        self._grid_actor = None
        self._grid_source = None
        self._grid_enabled = True
        self._axes_widget = None
        self._axes_enabled = True
        self._distance_widget = None
        self._measure_enabled = False
        self._plane_widget = None
        self._slice_plane = None
        self._slice_enabled = False
        self._clip_filters = []
        self._highlight_actor = None
        self._highlight_style = None
        self._picker = None

        if self._use_qvtk:
            self._qvtk = self._qvtk_class(self)
            self._qvtk.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addWidget(self._qvtk)
            QTimer.singleShot(0, self._init_qvtk)
        else:
            self.label = QLabel("VTK 初始化中...", self)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label.setScaledContents(True)
            self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.label.setMinimumSize(0, 0)
            layout.addWidget(self.label)

            self._last_sent = 0.0
            self._min_interval = 0.2
            self._poll_timer = QTimer(self)
            self._poll_timer.timeout.connect(self._drain_results)
            self._poll_timer.start(50)
            self._throttle_timer = QTimer(self)
            self._throttle_timer.setSingleShot(True)
            self._throttle_timer.timeout.connect(self._flush_pending)
            QTimer.singleShot(0, self._init_manager)

    def _init_qvtk(self):
        if self._vtk_ready:
            return
        try:
            import vtk
        except Exception:
            self._use_qvtk = False
            self.label = QLabel("VTK 初始化失败", self)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label.setScaledContents(True)
            self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.label.setMinimumSize(0, 0)
            self.layout().addWidget(self.label)
            return
        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(1.0, 1.0, 1.0)
        _add_light(vtk, self._renderer)
        self._named_colors = vtk.vtkNamedColors()
        self._render_window = self._qvtk.GetRenderWindow()
        self._render_window.AddRenderer(self._renderer)
        self._qvtk.Initialize()
        self._qvtk.Start()
        self._setup_interaction(vtk)
        self._vtk_ready = True
        if self._pending_geometry is not None:
            geom = self._pending_geometry
            self._pending_geometry = None
            self.update_mesh(geom)

    def _setup_interaction(self, vtk):
        interactor = self._render_window.GetInteractor()
        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)

        self._picker = vtk.vtkCellPicker()
        self._picker.SetTolerance(0.0005)

        axes_actor = vtk.vtkAxesActor()
        self._axes_widget = vtk.vtkOrientationMarkerWidget()
        self._axes_widget.SetOrientationMarker(axes_actor)
        self._axes_widget.SetInteractor(interactor)
        self._axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self._axes_widget.SetEnabled(1 if self._axes_enabled else 0)
        self._axes_widget.SetInteractive(0)

        self._distance_widget = vtk.vtkDistanceWidget()
        self._distance_widget.SetInteractor(interactor)
        self._distance_widget.CreateDefaultRepresentation()
        self._distance_widget.SetEnabled(1 if self._measure_enabled else 0)

        self._slice_plane = vtk.vtkPlane()
        plane_rep = vtk.vtkImplicitPlaneRepresentation()
        plane_rep.SetPlaceFactor(1.2)
        plane_rep.SetNormal(0.0, 0.0, 1.0)
        plane_rep.SetOrigin(0.0, 0.0, 0.0)
        plane_rep.PlaceWidget([-1, 1, -1, 1, -1, 1])
        self._plane_widget = vtk.vtkImplicitPlaneWidget2()
        self._plane_widget.SetInteractor(interactor)
        self._plane_widget.SetRepresentation(plane_rep)
        self._plane_widget.SetEnabled(1 if self._slice_enabled else 0)

        def on_plane(_obj, _evt):
            plane_rep.GetPlane(self._slice_plane)
            for clip in self._clip_filters:
                clip.Update()
            self._render_window.Render()

        self._plane_widget.AddObserver("InteractionEvent", on_plane)

        def on_left_press(_obj, _evt):
            if interactor.GetShiftKey():
                x, y = interactor.GetEventPosition()
                self._picker.Pick(x, y, 0, self._renderer)
                actor = self._picker.GetActor()
                self._apply_highlight(actor)
                self._render_window.Render()
            else:
                style.OnLeftButtonDown()

        interactor.AddObserver("LeftButtonPressEvent", on_left_press)

        def on_key_press(_obj, _evt):
            key = interactor.GetKeySym().lower()
            if key == "g":
                self._grid_enabled = not self._grid_enabled
                self._update_grid_visibility()
            elif key == "a":
                self._axes_enabled = not self._axes_enabled
                self._update_axes_visibility()
            elif key == "s":
                self._slice_enabled = not self._slice_enabled
                self._rebuild_scene()
            elif key == "m":
                self._measure_enabled = not self._measure_enabled
                self._update_measure_visibility()
            elif key == "r":
                self.reset_camera()
            self._render_window.Render()

        interactor.AddObserver("KeyPressEvent", on_key_press)

    def _update_axes_visibility(self):
        if self._axes_widget is None:
            return
        self._axes_widget.SetEnabled(1 if self._axes_enabled else 0)

    def _update_measure_visibility(self):
        if self._distance_widget is None:
            return
        self._distance_widget.SetEnabled(1 if self._measure_enabled else 0)

    def _update_grid_visibility(self):
        if self._grid_actor is not None:
            self._grid_actor.SetVisibility(1 if self._grid_enabled else 0)

    def _apply_highlight(self, actor):
        if actor is self._highlight_actor:
            return
        if self._highlight_actor is not None and self._highlight_style is not None:
            prop = self._highlight_actor.GetProperty()
            prop.SetColor(*self._highlight_style["color"])
            prop.SetEdgeColor(*self._highlight_style["edge_color"])
            prop.SetEdgeVisibility(self._highlight_style["edge_vis"])
            prop.SetLineWidth(self._highlight_style["line_width"])
        self._highlight_actor = None
        self._highlight_style = None
        if actor is None or actor not in self._actors:
            return
        prop = actor.GetProperty()
        self._highlight_style = {
            "color": prop.GetColor(),
            "edge_color": prop.GetEdgeColor(),
            "edge_vis": prop.GetEdgeVisibility(),
            "line_width": prop.GetLineWidth(),
        }
        prop.SetColor(1.0, 0.4, 0.0)
        prop.SetEdgeVisibility(1)
        prop.SetEdgeColor(1.0, 0.2, 0.0)
        prop.SetLineWidth(2.0)
        self._highlight_actor = actor

    def _ensure_grid(self, vtk, bounds):
        if bounds is None or bounds[1] < bounds[0]:
            bounds = (-5.0, 5.0, -5.0, 5.0, -1.0, 1.0)
        x_min, x_max, y_min, y_max, z_min, z_max = bounds
        size = max(x_max - x_min, y_max - y_min, 1.0) * 1.2
        cx = (x_min + x_max) * 0.5
        cy = (y_min + y_max) * 0.5
        z = z_min
        if self._grid_source is None:
            self._grid_source = vtk.vtkPlaneSource()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(self._grid_source.GetOutputPort())
            self._grid_actor = vtk.vtkActor()
            self._grid_actor.SetMapper(mapper)
            self._grid_actor.GetProperty().SetColor(0.8, 0.8, 0.8)
            self._grid_actor.GetProperty().SetLineWidth(1.0)
            self._grid_actor.GetProperty().SetRepresentationToWireframe()
            self._grid_actor.GetProperty().SetOpacity(0.6)
            self._renderer.AddActor(self._grid_actor)
        self._grid_source.SetXResolution(20)
        self._grid_source.SetYResolution(20)
        self._grid_source.SetOrigin(cx - size * 0.5, cy - size * 0.5, z)
        self._grid_source.SetPoint1(cx + size * 0.5, cy - size * 0.5, z)
        self._grid_source.SetPoint2(cx - size * 0.5, cy + size * 0.5, z)
        self._grid_source.Update()
        self._update_grid_visibility()

    def _rebuild_scene(self):
        if not self._vtk_ready or not self._last_source:
            return
        if self._plane_widget is not None:
            self._plane_widget.SetEnabled(1 if self._slice_enabled else 0)
        source_type, value = self._last_source
        if source_type == "geometry":
            self._update_scene(value)
        elif source_type == "file":
            self._update_scene(value, is_file=True)

    def _init_manager(self):
        if self._manager_ready:
            return
        self._manager = _get_vtk_manager()
        self._manager.acquire()
        cached = self._manager.get_cached_frame()
        if cached:
            image = QImage.fromData(cached)
            if not image.isNull():
                self.label.setPixmap(QPixmap.fromImage(image))
        self._view_id = self._manager.create_view(self.view_mode)
        self._manager_ready = True
        if self._pending_commands:
            for cmd in self._pending_commands:
                self._send_command(cmd)
            self._pending_commands.clear()
        if self._pending_geometry is not None:
            self._schedule_send()

    def _send_command(self, cmd):
        if not self._manager_ready:
            self._pending_commands.append(cmd)
            return
        payload = dict(cmd)
        payload["view_id"] = self._view_id
        payload["view_mode"] = self.view_mode
        self._manager.send(payload)

    def _drain_results(self):
        if not self._manager_ready:
            return
        frame, error, global_error = self._manager.get_latest(self._view_id)
        if global_error:
            self.label.setText(f"VTK 渲染异常: {global_error}")
            return
        if error:
            self.label.setText(f"VTK 渲染异常: {error}")
            return
        if frame:
            image = QImage.fromData(frame)
            if image.isNull():
                self.label.setText("VTK 渲染失败")
            else:
                pixmap = QPixmap.fromImage(image)
                if not self.label.size().isEmpty():
                    pixmap = pixmap.scaled(
                        self.label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                self.label.setPixmap(pixmap)

    def _schedule_send(self):
        if self._use_qvtk:
            return
        now = time.monotonic()
        elapsed = now - self._last_sent
        if elapsed >= self._min_interval:
            self._flush_pending()
        elif not self._throttle_timer.isActive():
            delay = max(1, int((self._min_interval - elapsed) * 1000))
            self._throttle_timer.start(delay)

    def _flush_pending(self):
        if not self._manager_ready:
            return
        geom = self._pending_geometry
        if geom is None:
            return
        self._pending_geometry = None
        self._last_sent = time.monotonic()
        self._send_command(
            {
                "type": "update",
                "geometry": geom,
                "width": self.width(),
                "height": self.height(),
            }
        )

    def update_mesh(self, geom_dict):
        self._last_source = ("geometry", geom_dict)
        if self._use_qvtk:
            if not self._vtk_ready:
                self._pending_geometry = geom_dict
                return
            self._update_scene(geom_dict)
            return
        self._pending_geometry = geom_dict
        self._schedule_send()

    def load_file(self, file_path):
        self._last_source = ("file", file_path)
        if self._use_qvtk:
            if not self._vtk_ready:
                return
            self._update_scene(file_path, is_file=True)
            return
        self._send_command(
            {
                "type": "load_file",
                "path": file_path,
                "width": self.width(),
                "height": self.height(),
            }
        )

    def clear(self):
        self._last_source = None
        if self._use_qvtk:
            if not self._vtk_ready:
                return
            _clear_actors(self._renderer, self._actors)
            self._render_window.Render()
            return
        self._send_command({"type": "clear", "width": self.width(), "height": self.height()})

    def reset_camera(self):
        if not self._last_source:
            return
        source_type, value = self._last_source
        if source_type == "geometry":
            if self._use_qvtk:
                if not self._vtk_ready:
                    self._pending_geometry = value
                    return
                self._update_scene(value)
                return
            self._pending_geometry = value
            self._schedule_send()
        elif source_type == "file":
            self.load_file(value)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._last_source:
            return
        if self._use_qvtk:
            return
        source_type, value = self._last_source
        if source_type == "geometry":
            self._pending_geometry = value
            self._schedule_send()
        elif source_type == "file":
            self.load_file(value)

    def closeEvent(self, event):
        try:
            if self._manager_ready:
                self._manager.destroy_view(self._view_id)
        except Exception:
            pass
        if self._manager_ready:
            self._manager.release()
        super().closeEvent(event)

    def _update_scene(self, payload, is_file=False):
        try:
            import vtk
        except Exception:
            return
        _clear_actors(self._renderer, self._actors)
        self._clip_filters = []
        self._apply_highlight(None)
        clip_plane = self._slice_plane if self._slice_enabled else None
        if is_file:
            _, clippers = _load_file(
                vtk, self._renderer, self._actors, self._named_colors, payload, clip_plane=clip_plane
            )
            self._clip_filters = clippers
        else:
            has_mesh, clippers = _build_mesh_from_geom(
                vtk, self._renderer, self._actors, self._named_colors, payload or {}, clip_plane=clip_plane
            )
            if not has_mesh:
                clippers = _build_parametric(
                    vtk, self._renderer, self._actors, self._named_colors, payload or {}, clip_plane=clip_plane
                )
            self._clip_filters = clippers
        bounds = self._renderer.ComputeVisiblePropBounds()
        self._ensure_grid(vtk, bounds)
        self._update_axes_visibility()
        self._update_measure_visibility()
        if self._plane_widget is not None and self._slice_enabled:
            plane_rep = self._plane_widget.GetRepresentation()
            if plane_rep is not None and bounds and bounds[1] >= bounds[0]:
                plane_rep.PlaceWidget(bounds)
                cx = (bounds[0] + bounds[1]) * 0.5
                cy = (bounds[2] + bounds[3]) * 0.5
                cz = (bounds[4] + bounds[5]) * 0.5
                plane_rep.SetOrigin(cx, cy, cz)
                plane_rep.SetNormal(0.0, 0.0, 1.0)
                plane_rep.GetPlane(self._slice_plane)
                for clip in self._clip_filters:
                    clip.Update()
        self._renderer.ResetCamera()
        _apply_view_mode(self._renderer, self.view_mode)
        self._render_window.Render()
