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

menuLineCallback("Alt+n", $("newproject"), () => apiSend({ type: "newproj" }));
menuLineCallback("Alt+o", $("openproject"), () =>
  apiSend({ type: "openproj" }),
);
menuLineCallback("Alt+s", $("saveproject"), () =>
  apiSend({ type: "saveproj" }),
);
menuLineCallback("Alt+Shift+s", $("saveasproject"), () =>
  apiSend({ type: "saveasproj" }),
);
menuLineCallback(
  "Alt+p",
  $("settings"),
  () => ($("settingsui").style.display = "flex"),
);
menuLineCallback("Alt+i", $("importsound"), () =>
  apiSend({ type: "importsound" }),
);

$("projtitle").addEventListener("focusout", () =>
  apiSend({
    type: "projtitle",
    value: $("projtitle").value,
  }),
);

$("track").onclick = (e) => {
  const usrOffX = e.offsetX;
  const pxPerSecond =
    track.clientWidth /
    +$("trackbounds").style.getPropertyValue("--sec-duration");
  const sec = usrOffX / pxPerSecond;
  const rounded = Math.round(sec * 100) / 100;
  apiSend({ type: "timestamp", time: rounded });
};

const lightsend = () => {
  if ($("curlight").dataset["id"] === undefined) return;

  apiSend({
    type: "lightchange",
    id: +$("curlight").dataset["id"],
    name: $("lightname").value,
    time: +$("lighttime").value,
    duration: +$("lightduration").value,
    static: $("lightpersist").checked,
    offx: +$("lightoffx").value,
    offy: +$("lightoffy").value,
  });
};

for (const c of $("curlight").querySelector(".options").children) {
  if (c.nodeName === "INPUT") c.addEventListener("focusout", lightsend);
}
$("lightpersist").onchange = lightsend;

const bttnsend = () => {
  if ($("curbttn").dataset["id"] === undefined) return;

  apiSend({
    type: "bttnchange",
    id: +$("curbttn").dataset["id"],
    time: +$("bttntime").value,
    page: +$("bttnpage").value,
    posx: +$("bttnx").value,
    posy: +$("bttny").value,
  });
};

for (const c of $("curbttn").querySelector(".options").children) {
  if (c.nodeName === "INPUT") c.addEventListener("focusout", bttnsend);
}

const aud = $("trackaudio");
const play = $("trackplay");
menuLineCallback(" ", play, () => {
  if (aud.paused) aud.play();
  else aud.pause();
});
aud.onplay = () => {
  play.querySelector("img").src = "feathericons/icons/pause.svg";
  audUpdate();
};
aud.onpause = aud.onended = () => {
  play.querySelector("img").src = "feathericons/icons/play.svg";
  apiSend({ type: "timestamp", time: aud.currentTime });
};
menuLineCallback("Backspace", $("trackback"), () => {
  aud.pause();
  aud.currentTime = 0;
  apiSend({ type: "timestamp", time: 0 });
});

$("kfsave").onclick = () =>
  apiSend({
    type: "gensave",
    name: $("kfname").value,
    duration: +$("gentime").value,
  });

let rafid = null;
const audUpdate = () => {
  trackTimestamp(aud.currentTime);

  if (!aud.paused) requestAnimationFrame(audUpdate);
};
