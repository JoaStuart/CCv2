// Copyright (C) 2026 JoaStuart
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

const $debugLog = (...args) => {
  // Cause JS be doin JS things
  for (const a of args) {
    console.log(typeof a, a);
  }
};

const menuLineCallback = (keyscombo, element, callback) => {
  keyCallbacks.push(() => {
    if (heldKeys.join("+") !== keyscombo) return;
    callback();
  });
  element.onclick = () => callback();
};
const menuCallback = (id) => {
  const list = document.getElementById(id);
  const parent = list.parentElement;
  if (parent.classList.contains("active")) {
    parent.classList.remove("active");
    list.style.display = "none";
  } else {
    parent.classList.add("active");
    list.style.display = "block";
  }
};

const round2 = (num) => Math.round(num * 100) / 100;

const keyCallbacks = [];
const heldKeys = [];
document.onkeydown = (e) => {
  heldKeys.push(e.key);
  keyCallbacks.forEach((el) => el());
};
document.onkeyup = (e) => {
  heldKeys.splice(heldKeys.indexOf(e.key), 1);
};

const $ = (id) => document.getElementById(id);

const elSetRGB = (el, r, g, b) => {
  if (el == null) return;

  el.style.setProperty("--r", r);
  el.style.setProperty("--g", g);
  el.style.setProperty("--b", b);
};
const apiSend = (d) => ws.send(JSON.stringify(d));

const setPage = (i) => {
  for (let y = 0; y < 8; y++) $(`8;${y}`).classList.remove("page");

  $(`8;${i}`).classList.add("page");
};

const setProject = (p) => {
  $("projtitle").value = p.title;
  $("projloadpath").value = p.load_path;
};

const setLightmap = (l) => {
  for (let i = 0; i < 128; i++) {
    const lm_element = l[i];
    if (lm_element === undefined) continue;

    elSetRGB(
      $(`vel${i}`),
      lm_element[0] * 4,
      lm_element[1] * 4,
      lm_element[2] * 4,
    );
  }
};

const setLightRecv = (r) => {
  Object.entries(r).forEach(([key, value]) => {
    const el = $(key);
    if (value[0] == 0 && value[1] == 0 && value[2] == 0) {
      elSetRGB(el, null, null, null);
    } else {
      elSetRGB(
        el,
        Math.min(255, value[0] * 4),
        Math.min(255, value[1] * 4),
        Math.min(255, value[2] * 4),
      );
    }
  });
};

const emptyElement = (el) => {
  while ((c = el.firstChild) !== null) el.removeChild(c);
};

const setTrack = (t) => {
  $("projduration").value = round2(t.length);

  $("track").querySelector("img").src = t.waveform;
  $("trackbounds").style.setProperty("--sec-duration", t.length);
  $("trackaudio").src = t.raw;
};

const addLighting = (l) => {
  const el = document.createElement("div");
  el.id = `light${l.id}`;
  el.classList.add("light");
  el.style.setProperty("--time", l.time);
  el.style.setProperty("--duration", l.duration);
  el.style.setProperty("--rank", l.rank);
  el.innerText = l.light;

  el.onclick = () => selectLight(el);

  el.dataset["id"] = l.id;
  el.dataset["time"] = round2(l.time);
  el.dataset["duration"] = round2(l.duration);
  el.dataset["name"] = l.light;
  el.dataset["offx"] = l.offx;
  el.dataset["offy"] = l.offy;
  el.dataset["static"] = l.static;

  $("lighttrack").appendChild(el);

  if (+l.id === (+$("curlight").dataset.id || 0)) {
    selectLight(el);
  }
};

const setLighting = (lighting) => {
  emptyElement($("lighttrack"));

  offsetLights(lighting);

  for (let i in lighting) {
    const l = lighting[i];
    l.id = i;
    addLighting(l);
  }
};

const setButtons = (buttons) => {
  emptyElement($("bttntrack"));

  for (let i in buttons) {
    const b = buttons[i];
    const el = document.createElement("div");
    el.id = `bttn${i}`;
    el.classList.add("bttn");
    el.style.setProperty("--time", b.time);
    el.onclick = () => selectButton(el);

    el.dataset["id"] = i;
    el.dataset["time"] = b.time;
    el.dataset["page"] = b.page;
    el.dataset["posx"] = b.posx;
    el.dataset["posy"] = b.posy;

    $("bttntrack").appendChild(el);

    if (+i === (+$("curbttn").dataset.id || 0)) {
      selectButton(el);
    }
  }
};

const vidEmpty =
  "data:video/mp4;base64,AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAl1tZGF0AAACQwYF//8/3EXpvebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE2NSAtIEguMjY0L01QRUctNCBBVkMgY29kZWMgLSBDb3B5bGVmdCAyMDAzLTIwMjUgLSBodHRwOi8vd3d3LnZpZGVvbGFuLm9yZy94MjY0Lmh0bWwgLSBvcHRpb25zOiBjYWJhYz0wIHJlZj0xIGRlYmxvY2s9MDowOjAgYW5hbHlzZT0wOjAgbWU9ZGlhIHN1Ym1lPTAgcHN5PTEgcHN5X3JkPTEuMDA6MC4wMCBtaXhlZF9yZWY9MCBtZV9yYW5nZT0xNiBjaHJvbWFfbWU9MSB0cmVsbGlzPTAgOHg4ZGN0PTAgY3FtPTAgZGVhZHpvbmU9MjEsMTEgZmFzdF9wc2tpcD0xIGNocm9tYV9xcF9vZmZzZXQ9MCB0aHJlYWRzPTEgbG9va2FoZWFkX3RocmVhZHM9MSBzbGljZWRfdGhyZWFkcz0wIG5yPTAgZGVjaW1hdGU9MSBpbnRlcmxhY2VkPTAgYmx1cmF5X2NvbXBhdD0wIGNvbnN0cmFpbmVkX2ludHJhPTAgYmZyYW1lcz0wIHdlaWdodHA9MCBrZXlpbnQ9MSBrZXlpbnRfbWluPTEgc2NlbmVjdXQ9MCBpbnRyYV9yZWZyZXNoPTAgcmM9Y3JmIG1idHJlZT0wIGNyZj0yMy4wIHFjb21wPTAuNjAgcXBtaW49MCBxcG1heD02OSBxcHN0ZXA9NCBpcF9yYXRpbz0xLjQwIGFxPTAAgAAAAApliIQ6JigACQLgAAAC/G1vb3YAAABsbXZoZAAAAAAAAAAAAAAAAAAAA+gAAAPoAAEAAAEAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAIndHJhawAAAFx0a2hkAAAAAwAAAAAAAAAAAAAAAQAAAAAAAAPoAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAKAAAACgAAAAAAJGVkdHMAAAAcZWxzdAAAAAAAAAABAAAD6AAAAAAAAQAAAAABn21kaWEAAAAgbWRoZAAAAAAAAAAAAAAAAAAAQAAAAEAAVcQAAAAAAC1oZGxyAAAAAAAAAAB2aWRlAAAAAAAAAAAAAAAAVmlkZW9IYW5kbGVyAAAAAUptaW5mAAAAFHZtaGQAAAABAAAAAAAAAAAAAAAkZGluZgAAABxkcmVmAAAAAAAAAAEAAAAMdXJsIAAAAAEAAAEKc3RibAAAAKZzdHNkAAAAAAAAAAEAAACWYXZjMQAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAKAAoASAAAAEgAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABj//wAAACxhdmNDAULACv/hABVnQsAK3fkkhAAAAwAEAAADAAo8SJ4BAARozg/IAAAAFGJ0cnQAAAAAAAASqAAAAAAAAAAYc3R0cwAAAAAAAAABAAAAAQAAQAAAAAAcc3RzYwAAAAAAAAABAAAAAQAAAAEAAAABAAAAFHN0c3oAAAAAAAACVQAAAAEAAAAUc3RjbwAAAAAAAAABAAAAMAAAAGF1ZHRhAAAAWW1ldGEAAAAAAAAAIWhkbHIAAAAAAAAAAG1kaXJhcHBsAAAAAAAAAAAAAAAALGlsc3QAAAAkqXRvbwAAABxkYXRhAAAAAQAAAABMYXZmNjIuMy4xMDA=";
const setKeyframes = (keyframes) => {
  emptyElement($("kflist"));

  Object.entries(keyframes).forEach(([name, v]) => {
    const el = document.createElement("div");
    el.classList.add("out", "kfentry");
    el.id = `kf${name}`;
    el.dataset["static"] = v.static;
    el.dataset["duration"] = v.duration;

    const vid = document.createElement("video");
    if (v.preview !== null) {
      vid.src = v.preview;
    } else {
      vid.src = vidEmpty;
    }
    vid.preload = "auto";
    vid.muted = true;
    vid.playsInline = true;
    vid.loop = true;

    const n = document.createElement("span");
    n.title = n.innerText = name;

    el.onmouseenter = () =>
      vid
        .play()
        .then(() => {})
        .catch(() => {});
    el.onmouseleave = () => {
      vid.pause();
      vid.currentTime = 0;
    };
    el.onclick = () => {
      apiSend({
        type: "lightadd",
        name: name,
        duration: v.duration,
        offx: 0,
        offy: 0,
        static: v.static,
      });
    };

    el.appendChild(vid);
    el.appendChild(n);
    $("kflist").appendChild(el);
  });
};

const setKeyframePreview = (p) => {
  Object.entries(p).forEach(([name, preview]) => {
    const kf = $(`kf${name}`);
    if (kf === null) return;

    kf.querySelector("video").src = preview;
  });
};

const trackTimestamp = (t) => {
  const track = $("track");
  const bounds = $("trackbounds");

  track.style.setProperty("--timestamp", `${t}`);
  const pxPerSec =
    track.clientWidth / +bounds.style.getPropertyValue("--sec-duration");
  const markerLeft = pxPerSec * t;

  if (markerLeft > bounds.scrollLeft + bounds.clientWidth) {
    bounds.scrollLeft = markerLeft;
  }
};

const setTimestamp = (t) => {
  trackTimestamp(t);
  $("trackaudio").currentTime = t;
};

const setRoute = (r) => {
  for (const a of document.getElementsByClassName("applet")) {
    a.classList.remove("active");
  }

  $(r).classList.add("active");
};

const setGenCol = (c) => {
  for (let i = 0; i < 128; i++) {
    $(`vel${i}`).classList.remove("active");
  }

  if (c !== null) $(`vel${c}`).classList.add("active");
};

const setGenFrames = (c) => {
  $("genframes").innerText = `${c.cur + 1} / ${c.max}`;
};

const setLightType = (l) => {
  for (let i of document.getElementsByClassName("ltypebtn"))
    i.classList.remove("out");

  $(`ltype${l}`).classList.add("out");
};

const setGradient = (glist) => {
  for (let i = 0; i < 16; i++) {
    let g = glist[i];
    if (g === undefined) g = [0, 0, 0];

    elSetRGB($(`velograd${i}`), g[0] * 4, g[1] * 4, g[2] * 4);
  }
};

const makeSettingLaunchpad = (lpType, l) => {
  const tr = document.createElement("tr");
  tr.classList.add("connlp");

  const tdName = document.createElement("td");
  tdName.innerText = l.midiname;
  tr.appendChild(tdName);

  const tdType = document.createElement("td");
  const selectType = document.createElement("select");
  selectType.id = `lp${l.id}`;

  for (const t of lpType) {
    const lpOption = document.createElement("option");
    lpOption.value = t;
    lpOption.selected = l.type === t;
    lpOption.innerText = t;
    selectType.appendChild(lpOption);
  }
  tdType.appendChild(selectType);
  tr.appendChild(tdType);

  const tdX = document.createElement("td");
  const inputX = document.createElement("input");
  inputX.type = "number";
  inputX.id = `lp${l.id}x`;
  inputX.value = l.offx;
  tdX.appendChild(inputX);
  tr.appendChild(tdX);

  const tdY = document.createElement("td");
  const inputY = document.createElement("input");
  inputY.type = "number";
  inputY.id = `lp${l.id}y`;
  inputY.value = l.offy;
  tdY.appendChild(inputY);
  tr.appendChild(tdY);

  const setOffset = () =>
    apiSend({
      type: "lpoffset",
      id: l.id,
      offx: +inputX.value,
      offy: +inputY.value,
    });

  inputX.addEventListener("focusout", setOffset);
  inputY.addEventListener("focusout", setOffset);

  return tr;
};

const setLaunchpad = (launchpadInfo) => {
  const table = $("connlaunchpads").querySelector("tbody");
  table.innerHTML = "<tr><th>Name</th><th>Type</th><th>X</th><th>Y</th></tr>";

  const lpType = launchpadInfo.type;
  const lpList = launchpadInfo.list;

  for (const l of lpList) table.appendChild(makeSettingLaunchpad(lpType, l));
};

const debugTransmit = () => {
  apiSend({ type: $("debugtransmit").value });
};

const debugBake = () => apiSend({ type: "bake" });

const ws = new WebSocket("/api/v1/full");
ws.onclose = () => null; //window.location.reload();
ws.onopen = () => apiSend({ type: "retransmit" });
ws.onmessage = (ev) => {
  const data = JSON.parse(ev.data);

  if (data.type == "update")
    Object.entries({
      page: setPage,
      project: setProject,
      lightmap: setLightmap,
      lightrecv: setLightRecv,
      track: setTrack,
      lighting: setLighting,
      timestamps: setButtons,
      keyframes: setKeyframes,
      kfpreview: setKeyframePreview,
      timestamp: setTimestamp,
      route: setRoute,
      gencol: setGenCol,
      genframes: setGenFrames,
      lighttype: setLightType,
      gradient: setGradient,
      launchpad: setLaunchpad,
    }).forEach(([key, handler]) => {
      if (data[key] !== undefined) {
        handler(data[key]);
      }
    });
};

const colorClick = (r, g, b) => {
  console.log(JSON.stringify({ r: +r, g: +g, b: +b }));
};

const trackZoom = (zoom) => {
  const style = $("trackbounds").style;
  style.setProperty(
    "--sec-per-screen",
    +style.getPropertyValue("--sec-per-screen") + zoom,
  );
};

const deselectAll = () => {
  for (const c of document.getElementsByClassName("light")) {
    c.classList.remove("select");
  }

  for (const c of document.getElementsByClassName("bttn")) {
    c.classList.remove("select");
  }
};

const selectLight = (el) => {
  $("curbttn").classList.remove("active");
  $("curbttn").dataset["id"] = undefined;
  $("curlight").classList.add("active");
  $("curlight").dataset["id"] = el.dataset["id"];

  deselectAll();
  el.classList.add("select");

  $("lighttime").value = +el.dataset["time"];
  $("lightname").value = el.dataset["name"];
  $("lightduration").value = +el.dataset["duration"];
  $("lightoffx").value = +el.dataset["offx"];
  $("lightoffy").value = +el.dataset["offy"];
  $("lightpersist").checked = el.dataset["static"] === "true";
};

const selectButton = (el) => {
  $("curlight").classList.remove("active");
  $("curlight").dataset["id"] = undefined;
  $("curbttn").classList.add("active");
  $("curbttn").dataset["id"] = el.dataset["id"];

  deselectAll();
  el.classList.add("select");

  $("bttntime").value = +el.dataset["time"];
  $("bttnx").value = +el.dataset["posx"];
  $("bttny").value = +el.dataset["posy"];
  $("bttnpage").value = +el.dataset["page"];
};

const lpClick = (x, y) => {
  apiSend({ type: "lpclick", x: x, y: y });
};

const lpSwitch = (r) => {
  apiSend({ type: "route", route: r });
};

const lmClick = (i) =>
  apiSend({
    type: "gencol",
    vel: i,
  });

const genSend = (n) =>
  apiSend({
    type: "genaction",
    action: n,
  });

const genPreview = () => {
  apiSend({
    type: "genpreview",
    duration: +$("gentime").value,
  });
};

const lightType = (t) => {
  apiSend({
    type: "lighttype",
    light: t,
  });
};

const offsetLights = (lights) => {
  lights.sort((a, b) => a.time - b.time);

  const getLastLowerLight = (idx, rank) => {
    for (let i = idx - 1; i >= 0; i--) {
      if (lights[i].rank < rank) return lights[i];
    }
  };

  for (let i in lights) {
    i = +i;
    if (i === 0) {
      lights[i].rank = 0;
      continue;
    }

    const currentLight = lights[i];
    let rank = lights[i - 1].rank + 1;

    while (rank > 0) {
      const lastLowerLight = getLastLowerLight(i, rank);
      if (currentLight.time > lastLowerLight.time + lastLowerLight.duration)
        rank = lastLowerLight.rank;
      else break;
    }
    currentLight.rank = rank;
  }
};

const remove = (t) => {
  if ($("cur" + t).dataset["id"] === undefined) return;
  apiSend({ type: t + "remove", id: +$("cur" + t).dataset["id"] });
};
