import json
import logging
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from typing import Optional
from jpyweb import (
    WsControlCode,
    static_route,
    route,
    stop,
    ws,
    HttpRequestData,
    HttpResponseData,
    HttpMethod,
    WsData,
    start,
)

from ..audio.track import AudioTrack
from ..utils.data_uri import make_data_uri
from ..utils.ffmpeg import ffmpeg_call
from .. import logger
from ..lighting.lightmap import Lightmap
from ..singleton import singleton
from ..audio.audio_route import AudioRouter
from ..lighting.keyframes import Keyframes
from ..project.baking import BakedProject
from ..launchpad.base import Launchpad, LaunchpadIn, LaunchpadOut
from ..launchpad.route import LaunchpadReceiver
from ..ptypes import int2, int3
from ..utils.color import col
from ..lighting.lightmanager import KfData, LightManager, LightReceiver
from ..project.project import ProjButton, ProjLight, Project
from ..utils.filedialog import select_file, select_save
from ..utils.animations import load_animation
from ..project.project import Project
from .. import constants

static_route("/static", constants.STATIC_UI)


@route(HttpMethod.GET, "/")
def root(req: HttpRequestData) -> HttpResponseData:
    return HttpResponseData.move("/static/index.html")


@route(HttpMethod.GET, "/lp")
def launchpad(req: HttpRequestData) -> HttpResponseData:
    return HttpResponseData.move("/static/launchpad.html")


api = ws("/api/v1/full")
lp = ws("/api/v1/lp")


def _proj() -> "Project":
    return Project.CURRENT_PROJECT.v


def page_get() -> dict:
    return {"page": Launchpad.PAGE.v}


def proj_get() -> dict:
    p = _proj()
    return {"project": {"title": p.title, "load_path": p.load_path}}


def tracks_get() -> dict:
    return {
        "tracks": [
            {
                "name": t.name,
                "length": t.length,
                "volume": t.volume,
                "waveform": t.waveform,
                "raw": make_data_uri(t.path),
            }
            for t in _proj().tracks.v
        ]
    }


def lighting_get() -> dict:
    return {
        "lighting": [
            {
                "time": l.time,
                "duration": abs(l.duration),
                "static": l.duration < 0,
                "light": l.light,
                "offx": l.offset[0],
                "offy": l.offset[1],
            }
            for l in _proj().lighting.v
        ],
    }


def timestamps_get() -> dict:
    return {
        "timestamps": [
            {
                "time": t.time,
                "page": t.page,
                "posx": t.pos[0],
                "posy": t.pos[1],
            }
            for t in _proj().timestamps.v
        ]
    }


def kfpreview(name: str, kf: Keyframes) -> dict:
    return {
        "kfpreview": {name: kf.preview},
    }


def keyframes_get() -> dict:
    return {
        "keyframes": {
            name: {
                "static": value.static_after,
                "duration": abs(value.anim_time),
                "preview": value.preview,
            }
            for name, value in Keyframes.FRAME_CACHE.items()
            if not name.startswith("__")
        }
    }


def lightmap_get() -> dict:
    if len(Launchpad.OUTPUTS) == 0:
        m = Lightmap.MAPS["Mk2+Realism"]
    else:
        m = Lightmap.MAPS[Launchpad.OUTPUTS[0].lightmap()]

    return {"lightmap": {k: v.rgb for k, v in m.items()}}


def route_get() -> dict:
    global _ROUTE

    return {"route": _ROUTE.frontend_applet()}


def timestamp_get() -> dict:
    return {"timestamp": CreateRoute().timestamp}


def lastframe_get() -> dict:
    return {"lightrecv": WebUiLightReceiver().lightmap}


def launchpad_get() -> dict:
    return {
        "launchpad": {
            "type": [
                s.__name__
                for s in Launchpad.__subclasses__()
                if s != LaunchpadIn and s != LaunchpadOut
            ],
            "list": [
                {
                    "midiname": l.midiname,
                    "id": i,
                    "offx": l.offx,
                    "offy": l.offy,
                    "type": type(l).__bases__[0].__name__,
                }
                for i, l in enumerate(Launchpad.INPUTS)
            ],
        }
    }


def api_open_project() -> None:
    path = select_file(
        title="Open CC/v2 Project",
        filetype=("CCv2 Cover files", "*.lpz"),
    )
    if path is None:
        return

    load_finish = load_animation()
    Project.load(path)
    _proj().bake()

    load_finish.set()


def api_save_project(file: Optional[str] = None) -> None:
    p = _proj()
    if file is not None:
        return p.save(file)

    if p.load_path is None:
        return api_save_project_as()

    p.save(p.load_path)
    logger.info("Project saved")


def api_save_project_as() -> None:
    path = select_save(
        title="Save CC/v2 Project",
        filetype=("CCv2 Cover files", "*.lpz"),
    )
    if path is None:
        return

    return api_save_project(path)


def api_import_sound() -> None:
    path = select_file(
        title="Import Soundtrack",
        filetype=("Audio files", "*.mp3"),
    )
    if path is None:
        return

    filename = os.path.basename(path)
    file_out = os.path.splitext(filename)[0] + ".wav"
    out_path = os.path.join(constants.CACHE_AUDIO, file_out)

    logger.info("Converting sound")
    assert (
        ffmpeg_call(
            "-i", '"' + path + '"', "-ar", "44100", "-ac", "2", '"' + out_path + '"'
        )
        == 0
    )

    logger.info("Loading audio track")
    proj = _proj()
    proj.tracks.v.append(AudioTrack(out_path))
    proj.tracks.change()


def api_response(req: WsData[str], data: dict) -> WsData:
    return req.respond(WsControlCode.OP_TEXT, json.dumps({"type": "update"} | data))


def api_update(data: dict) -> None:
    d = json.dumps({"type": "update"} | data)
    api.broadcast(WsControlCode.OP_TEXT, d, None)


def api_retransmit() -> dict:
    gen = GenerateRoute()

    return (
        {"type": "update"}
        | page_get()
        | proj_get()
        | tracks_get()
        | lighting_get()
        | timestamps_get()
        | lightmap_get()
        | keyframes_get()
        | route_get()
        | timestamp_get()
        | gen.gencol_get()
        | lastframe_get()
        | gen.frames_get()
        | gen.lighttype_get()
        | gen.gradient_get()
        | launchpad_get()
    )


def newproj_in_api(_data):

    Project.CURRENT_PROJECT.v = Project()


def lightadd_in_api(data):
    name = data["name"]
    duration = data["duration"]
    offset = data["offx"], data["offy"]
    static = data["static"]

    lighting = _proj().lighting
    lighting.v.append(
        ProjLight(
            name,
            CreateRoute().timestamp,
            duration if not static else -duration,
            offset,
        )
    )

    lighting.change()


def lightchange_in_api(data):
    id = data["id"]
    name = data["name"]
    timestamp = data["time"]
    duration = data["duration"]
    static = data["static"]
    offset = data["offx"], data["offy"]

    lighting = _proj().lighting
    vid = lighting.v[id]
    vid.light = name
    vid.duration = duration if not static else -duration
    vid.time = timestamp
    vid.offset = offset

    lighting.change()


def bttnchange_in_api(data):
    id = data["id"]
    timestamp = data["time"]
    page = data["page"]
    position = data["posx"], data["posy"]

    buttons = _proj().timestamps
    vid = buttons.v[id]
    vid.time = timestamp
    vid.page = page
    vid.pos = position

    buttons.change()


def timestamp_in_api(data):
    CreateRoute().timestamp = data["time"]
    api_update(timestamp_get())


def projtitle_in_api(data):
    _proj().title = data["value"]
    api_update(proj_get())


def route_in_api(data):
    sel_route = data["route"]

    for r in WEB_ROUTES:
        if r.frontend_applet() == sel_route:
            r.request()

            api_update(route_get())
            return

    logger.error("No frontend route found %s!", sel_route)


def gencol_in_api(data):
    (g := GenerateRoute()).velocity = data["vel"]
    api_update(g.gencol_get() | g.gradient_get())


def lighttype_in_api(data):
    (g := GenerateRoute()).light_type(data["light"])
    api_update(g.lighttype_get() | g.gencol_get())


def gradientremove_in_api(data):
    (g := GenerateRoute()).gradient_remove(data["idx"])
    api_update(g.gradient_get())


def lpoffset_in_api(data):
    lid = data["id"]
    offx = data["offx"]
    offy = data["offy"]

    i = Launchpad.INPUTS[lid]
    i.offx = offx
    i.offy = offy
    o = Launchpad.OUTPUTS[lid]
    o.offx = offx
    o.offy = offy

    print(lid, offx, offy)

    api_update(launchpad_get())


def bttnremove_in_api(data):
    t = _proj().timestamps
    t.v.pop(data["id"])
    t.change()


def lightremove_in_api(data):
    l = _proj().lighting
    l.v.pop(data["id"])
    l.change()


@api.text
def wsapi(req: WsData[str]) -> WsData | None:
    try:
        data = json.loads(req.data)
        if (t := data.get("type", None)) == None:
            return

        return {
            "retransmit": lambda _: api_response(req, api_retransmit()),
            "openproj": lambda _: threading.Thread(target=api_open_project).start(),
            "newproj": newproj_in_api,
            "saveproj": lambda _: threading.Thread(target=api_save_project).start(),
            "saveasproj": lambda _: threading.Thread(
                target=api_save_project_as
            ).start(),
            "getproj": lambda _: api_response(req, proj_get()),
            "gettracks": lambda _: api_response(req, tracks_get()),
            "getlighting": lambda _: api_response(req, lighting_get()),
            "gettimestamps": lambda _: api_response(req, timestamps_get()),
            "getkeyframes": lambda _: api_response(req, keyframes_get()),
            "bake": lambda _: _proj().bake(),
            "lpclick": lambda _: LaunchpadReceiver.route_click(data["x"], data["y"]),
            "lightadd": lightadd_in_api,
            "lightchange": lightchange_in_api,
            "bttnchange": bttnchange_in_api,
            "timestamp": timestamp_in_api,
            "projtitle": projtitle_in_api,
            "route": route_in_api,
            "gencol": gencol_in_api,
            "genaction": lambda _: GenerateRoute().action(data["action"]),
            "genpreview": lambda _: GenerateRoute().preview(data["duration"]),
            "gensave": lambda _: GenerateRoute().save(data["name"], data["duration"]),
            "lighttype": lighttype_in_api,
            "gradientremove": gradientremove_in_api,
            "lpoffset": lpoffset_in_api,
            "importsound": lambda _: api_import_sound(),
            "bttnremove": bttnremove_in_api,
            "lightremove": lightremove_in_api,
        }.get(t, print)(data)

    except:
        logger.error("Failed handling full api endpoint", stack_info=True)


@lp.binary
def lpapi(req: WsData[bytes]) -> WsData | None:
    assert len(req.data) == 1
    packed_pos = int.from_bytes(req.data)

    LaunchpadReceiver.route_click((packed_pos >> 4) - 1, (packed_pos & 0xF) - 1)


def vpad_send_frame(frame: dict[str, int3]) -> None:
    data: list[int] = []
    for pos, col in frame.items():
        x, y = map(int, pos.split(";", 1))
        if x < -1 or x > 8 or y < -1 or y > 9:
            continue

        packed = ((x + 1) << 4) | (y + 1)
        data.append(packed)
        data.append(col[0])
        data.append(col[1])
        data.append(col[2])

    lp.broadcast(WsControlCode.OP_BINARY, bytes(data), None)


@singleton
class WebUiLightReceiver(LightReceiver):
    def __init__(self) -> None:
        self._lpmap: dict[str, int3] = {}

    @property
    def lightmap(self) -> dict[str, int3]:
        return self._lpmap

    def __setitem__(self, pos: tuple[int, int], c: col) -> None:
        self._lpmap[f"{pos[0]};{pos[1]}"] = c.rgb

    def finish(self) -> None:
        try:
            api_update({"lightrecv": self._lpmap})
        except:
            pass

        try:
            vpad_send_frame(self._lpmap)
        except:
            pass

        self._lpmap = {}


@singleton
class PlayRoute(LaunchpadReceiver):
    @staticmethod
    def request() -> None:
        global _ROUTE
        LaunchpadReceiver.request_input(_ROUTE := PlayRoute())

    @staticmethod
    def frontend_applet() -> str:
        return "tl"

    def note_on(self, x: int, y: int) -> None:
        if x == -1 and y == -1:
            r = AudioRouter()
            r.stop_all()

            LightManager().stop()
            Launchpad.broadcast_clear()
        elif x == 8 and y >= 0:
            Launchpad.PAGE.v = y

        proj = _proj().baked
        if not proj:
            return

        self._play_note(proj, x, y)
        self._play_light(proj, x, y)

    def _play_note(self, proj: BakedProject, x: int, y: int) -> None:
        aud = proj.get_audio(Launchpad.PAGE.v, (x, y))

        if aud is None:
            return

        AudioRouter().play(aud)

    def _play_light(self, proj: BakedProject, x: int, y: int) -> None:
        light = proj.get_light(Launchpad.PAGE.v, (x, y))

        if light is None:
            return

        for l in light:
            LightManager().play_after(*l)

    def note_off(self, x: int, y: int) -> None:
        return super().note_off(x, y)


@singleton
class CreateRoute(LaunchpadReceiver):
    @staticmethod
    def request() -> None:
        global _ROUTE

        LaunchpadReceiver.request_input(_ROUTE := CreateRoute())

    @staticmethod
    def frontend_applet() -> str:
        return "tr"

    def __init__(self) -> None:
        super().__init__()

        self._timestamp: float = 0

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, num: float) -> None:
        self._timestamp = num

    def note_on(self, x: int, y: int) -> None:
        timestamps = _proj().timestamps
        timestamps.v.append(
            ProjButton(
                self._timestamp,
                (x, y),
                Launchpad.PAGE.v,
            )
        )
        timestamps.change()

    def note_off(self, x: int, y: int) -> None:
        return super().note_off(x, y)


@singleton
class GenerateRoute(LaunchpadReceiver):
    @staticmethod
    def request() -> None:
        global _ROUTE

        LaunchpadReceiver.request_input(_ROUTE := GenerateRoute())

    @staticmethod
    def frontend_applet() -> str:
        return "br"

    def __init__(self) -> None:
        self._created_frames: list[dict[int2, col]] = [{}]
        self._display_frame: int = 0
        self._frame_event: Optional[threading.Event] = None
        self._current_vel: int = 0
        self._current_gradient: list[int] = []
        self._current_type = "static"
        self._active_gradients: dict[int2, list[int]] = {}

    @property
    def velocity(self) -> Optional[int]:
        if self._current_type == "static":
            return self._current_vel
        return None

    @velocity.setter
    def velocity(self, value: int) -> None:
        if self._current_type == "static":
            self._current_vel = value
        else:
            if len(self._current_gradient) >= 16:
                self._current_gradient.pop()
            self._current_gradient.append(value)

    def light_type(self, t: str) -> None:
        self._current_type = t

    def lighttype_get(self) -> dict:
        return {"lighttype": self._current_type}

    def gradient_get(self) -> dict:
        return {"gradient": [self._cvt_color(c).rgb for c in self._current_gradient]}

    def gradient_remove(self, idx: int) -> None:
        if idx >= len(self._current_gradient):
            return
        self._current_gradient.pop(idx)

    def gencol_get(self) -> dict:
        return {"gencol": self.velocity}

    def action(self, action: str) -> None:
        if action == "clear":
            self.clear()
            api_update(self.frames_get())
        elif action == "back":
            self._display_frame = max(self._display_frame - 1, 0)
            self._display_current()
            api_update(self.frames_get())
        elif action == "next":
            self._display_frame += 1

            if len(self._created_frames) == self._display_frame:
                new: dict[int2, col] = {}
                self._created_frames.append(new)

                for xy, g in self._active_gradients.copy().items():
                    vel = g.pop(0)
                    new[xy] = self._cvt_color(vel)

                    if len(g) == 0:
                        del self._active_gradients[xy]

            self._display_current()
            api_update(self.frames_get())

    def _keyframes(self) -> Keyframes:
        kf = Keyframes()
        for f in self._created_frames:
            kf.append(f.copy())

        return kf

    def preview(self, time: float) -> None:
        if self._frame_event is not None:
            self._frame_event.set()
            self._frame_event = None

        kf = self._keyframes()

        evt = LightManager().play_raw(KfData(kf, time))

        def evtwait():
            evt.wait()
            self._display_current()

        threading.Thread(target=evtwait, daemon=True, name="GenPreviewEvent").start()

    def save(self, name: str, duration: float) -> None:
        kf = self._keyframes()
        kf.anim_time = duration

        Keyframes.FRAME_CACHE[name] = kf
        Keyframes.preview_request(name, kf)
        api_update(keyframes_get())

        self.clear()
        api_update(self.frames_get())
        _proj().bake()

    def frames_get(self) -> dict:
        return {
            "genframes": {"cur": self._display_frame, "max": len(self._created_frames)}
        }

    def _cvt_color(self, vel: int) -> col:
        if len(Launchpad.OUTPUTS) == 0:
            m = Lightmap.MAPS["Mk2+Realism"]
        else:
            m = Lightmap.MAPS[Launchpad.OUTPUTS[0].lightmap()]

        return m[vel]

    def clear(self) -> None:
        if self._frame_event is not None:
            self._frame_event.set()
            self._frame_event = None

        self._created_frames = [{}]
        self._display_frame = 0

    def _display_current(self) -> None:
        if self._frame_event is not None:
            self._frame_event.set()

        kf = Keyframes()
        kf.frame_buffer.append(self._created_frames[self._display_frame].copy())
        self._frame_event = threading.Event()
        persistent = kf.persistent(self._frame_event)
        LightManager().play_raw(KfData(persistent, duration=0.1))

    def note_on(self, x: int, y: int) -> None:
        frame = self._created_frames[self._display_frame]
        current = frame.get((x, y), None)

        if current is not None:
            del frame[x, y]
            if self._active_gradients.get((x, y), None) is not None:
                del self._active_gradients[x, y]

            self._display_current()
            return

        if self._current_type == "static":
            frame[x, y] = self._cvt_color(self._current_vel)
        else:
            if len(self._current_gradient) == 0:
                return

            grad = self._current_gradient.copy()
            frame[x, y] = self._cvt_color(grad.pop(0))

            if len(grad) > 0:
                self._active_gradients[x, y] = grad

        self._display_current()

    def note_off(self, x: int, y: int) -> None:
        return super().note_off(x, y)


type _WebRoute = PlayRoute | CreateRoute | GenerateRoute
WEB_ROUTES: list[_WebRoute] = [PlayRoute(), CreateRoute(), GenerateRoute()]
_ROUTE: _WebRoute = PlayRoute()


def _proj_change_listeners(p: "Project") -> None:
    p.tracks.add_listener(lambda _: api_update(tracks_get()))
    p.lighting.add_listener(lambda _: api_update(lighting_get()))
    p.timestamps.add_listener(lambda _: api_update(timestamps_get()))


def _proj_change(p: "Project"):
    _proj_change_listeners(p)

    api_update(proj_get() | tracks_get() | lighting_get() | timestamps_get())


def add_update_listeners() -> None:
    Launchpad.PAGE.add_listener(lambda _: api_update(page_get()))
    Project.CURRENT_PROJECT.add_listener(_proj_change)
    _proj_change_listeners(_proj())


WEBUI_URL = f"http://127.0.0.1:{constants.WEBUI_PORT}/"


def browser_chromium(tmpdir: str, size: tuple[int, int], verbose: bool) -> None:
    kwargs = {}
    if not verbose:
        kwargs["stdin"] = subprocess.PIPE
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    subprocess.Popen(
        [
            "chromium",
            "--app=" + WEBUI_URL,
            f"--user-data-dir={tmpdir}",
            "--window-size=" + ",".join(map(str, size)),
            "--disable-extensions",
            "--disable-features=Translate",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-crash-reporter",
            "--disable-component-updates",
            "--disable-background-networking",
            "--safebrowsing-disable-auto-update",
            "--metrics-recording-only",
        ],
        **kwargs,
    ).wait()


def browser_google_chrome(tmpdir: str, size: tuple[int, int], verbose: bool) -> None:
    kwargs = {}
    if not verbose:
        kwargs["stdin"] = subprocess.PIPE
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    subprocess.Popen(
        [
            "google-chrome",
            "--app=" + WEBUI_URL,
            f"--user-data-dir={tmpdir}",
            "--window-size=" + ",".join(map(str, size)),
            "--disable-extensions",
            "--disable-features=Translate",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-crash-reporter",
            "--disable-component-updates",
            "--disable-background-networking",
            "--disable-gcm",
            "--safebrowsing-disable-auto-update",
            "--metrics-recording-only",
        ],
        **kwargs,
    ).wait()


def browser_fallback_firefox(_: str, __: tuple[int, int], verbose: bool) -> None:
    logger.warning(
        "Consider installing chromium/google chrome for best app-experience!\nPress Ctrl+C to quit this application."
    )

    kwargs = {}
    if not verbose:
        kwargs["stdin"] = subprocess.PIPE
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    subprocess.Popen(["firefox", "-url", WEBUI_URL], **kwargs)

    threading.Event().wait()


def browser_none(_: str, __: tuple[int, int], ___: bool) -> None:
    logger.error(
        "No browser found! Please install chromium/google chrome or access %s manually!\nPress Ctrl+C to quit this application.",
        WEBUI_URL,
    )
    threading.Event().wait()


def open_and_run(splash_finish: threading.Event, args) -> None:
    add_update_listeners()
    LightManager().add_light_receiver(WebUiLightReceiver())
    Keyframes.PREVIEW_COMPLETED = lambda n, v: api_update(kfpreview(n, v))
    Keyframes.LOAD_COMPLETED = lambda _: api_update(keyframes_get())
    _ROUTE.request()

    if args.vpad:
        hostaddr = socket.gethostbyname(socket.gethostname())
        logger.info("Starting VPad on http://%s:%d/lp", hostaddr, constants.WEBUI_PORT)

    def browser() -> None:
        time.sleep(0.1)
        splash_finish.set()

        with tempfile.TemporaryDirectory() as tmpdir:
            for br in [
                browser_chromium,
                browser_google_chrome,
                browser_fallback_firefox,
                browser_none,
            ]:
                try:
                    br(tmpdir, (1500, 1000), args.verbose)
                except FileNotFoundError:
                    continue

                break

        stop()

    threading.Thread(target=browser, daemon=True, name="BrowserView").start()

    try:
        start(
            port=constants.WEBUI_PORT,
            hostname="0.0.0.0" if args.vpad else "127.0.0.1",
            log_level=logging.DEBUG,
        )
    except KeyboardInterrupt:
        pass
