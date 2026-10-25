"use strict";
// Static map client. All decryption happens here, in the browser; the passphrase never leaves it.
// It matches the Python crypto format: file = "FNC1" + nonce(12) + AES-256-GCM(ct||tag);
// plaintext = 4-byte big-endian length + data + zero padding. The data key is itself wrapped
// by the passphrase: "FNK1" + salt(16) + nonce(12) + GCM(32-byte key), PBKDF2-SHA256 600k.

const REPO = "brwnw6692-sys/notes-sync";
const BASE_DEG = 0.5, FACTOR = 5;           // must match collector config
const PBKDF2_ROUNDS = 600000;
// The area we listen to (must match collector grid bounds): the whole Middle East, incl. all Turkey.
const AOI = [[12.0, 25.0], [42.5, 64.0]];   // [[latMin,lonMin],[latMax,lonMax]]

const map = L.map("map", { zoomControl: true });
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; OpenStreetMap', maxZoom: 19, className: "basemap-dark",
}).addTo(map);
map.fitBounds(AOI, { padding: [10, 10] });
// The perimeter: a clear line showing exactly how far the system listens.
L.rectangle(AOI, { color: "#39b0b8", weight: 1.5, fill: false, dashArray: "2 4", interactive: false }).addTo(map);

const events = L.layerGroup().addTo(map);   // where something is happening (foreground)
const gaps = L.layerGroup();                 // unwatched hot cells (behind a toggle)
let lastSnap = null;
const $ = (id) => document.getElementById(id);

function heatColor(t) {              // 0..1 -> blue(calm) .. red(hot)
  const stops = [[42,111,176],[216,177,47],[216,90,48],[194,46,46]];
  const x = Math.max(0, Math.min(1, t)) * (stops.length - 1);
  const i = Math.floor(x), f = x - i, a = stops[i], b = stops[Math.min(i + 1, stops.length - 1)];
  const c = a.map((v, k) => Math.round(v + (b[k] - v) * f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

function drawEvents(snap) {
  events.clearLayers();
  // Foreground: where something is happening. Each report cluster glows — bigger and brighter
  // with more independent sources — so the eye goes straight to the action.
  const maxCount = Math.max(1, ...snap.active.map((c) => c.count));
  for (const c of snap.active) {
    const r = 5 + 9 * Math.sqrt(c.count / maxCount);
    const col = heatColor(0.45 + 0.55 * (c.count / maxCount));
    L.circleMarker([c.lat, c.lon], {                       // soft halo = the glow
      radius: r + 7, stroke: false, fillColor: col, fillOpacity: 0.18,
    }).addTo(events);
    L.circleMarker([c.lat, c.lon], {                       // bright core
      radius: r, color: "#fff", weight: 1, fillColor: col, fillOpacity: 0.9,
    }).bindTooltip(`${c.count} independent source${c.count > 1 ? "s" : ""} reporting here`).addTo(events);
  }
}

function drawGaps(snap) {
  gaps.clearLayers();
  // Quiet background: hot, populated cells we have no eyes on yet. Only when the viewer asks.
  const s = BASE_DEG / 2;
  for (const c of snap.blind) {
    L.rectangle([[c.lat - s, c.lon - s], [c.lat + s, c.lon + s]], {
      stroke: false, fillColor: "#c22e2e", fillOpacity: 0.12,
    }).addTo(gaps);
  }
}

function draw(snap) {
  lastSnap = snap;
  drawEvents(snap);
  if (map.hasLayer(gaps)) drawGaps(snap);
  const age = Math.max(0, Math.round((Date.now() - new Date(snap.generated_at)) / 60000));
  const headline = snap.active.length
    ? `<b>${snap.active.length}</b> place${snap.active.length > 1 ? "s" : ""} active now`
    : `No activity located yet`;
  $("status").innerHTML =
    `${headline}. Watching <b>${snap.covered_hot_cells}</b> of ${snap.hot_cells} populated cells ` +
    `(${snap.blind.length} still unwatched). ` +
    (age > 60 ? `<span style="color:#d85a30">updated ${age} min ago</span>` : `updated ${age} min ago`);
}

function b64ToBytes(b64) {
  const bin = atob(b64.replace(/\s+/g, ""));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function fetchDataFile(name) {
  // GitHub contents API is CORS-enabled for public repos (no token, rate-limited but fine).
  const url = `https://api.github.com/repos/${REPO}/contents/${name}?ref=data`;
  const r = await fetch(url, { headers: { Accept: "application/vnd.github.raw" } });
  if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`);
  return new Uint8Array(await r.arrayBuffer());
}

function unpad(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  const n = dv.getUint32(0, false);
  return buf.slice(4, 4 + n);
}

async function unwrapKey(wrapped, passphrase) {
  if (String.fromCharCode(...wrapped.slice(0, 4)) !== "FNK1") throw new Error("bad key file");
  const salt = wrapped.slice(4, 20), nonce = wrapped.slice(20, 32), ct = wrapped.slice(32);
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(passphrase),
    "PBKDF2", false, ["deriveKey"]);
  const kek = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ROUNDS, hash: "SHA-256" },
    base, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
  const raw = await crypto.subtle.decrypt({ name: "AES-GCM", iv: nonce }, kek, ct);
  return crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["decrypt"]);
}

async function decryptFile(blob, dataKey) {
  if (String.fromCharCode(...blob.slice(0, 4)) !== "FNC1") throw new Error("bad data file");
  const nonce = blob.slice(4, 16), ct = blob.slice(16);
  const plain = new Uint8Array(await crypto.subtle.decrypt({ name: "AES-GCM", iv: nonce }, dataKey, ct));
  return JSON.parse(new TextDecoder().decode(unpad(plain)));
}

async function loadLive(passphrase) {
  $("status").textContent = "Decrypting…";
  try {
    const [wrapped, mapBlob] = await Promise.all([fetchDataFile("wrapped_key.bin"), fetchDataFile("map.bin")]);
    const dataKey = await unwrapKey(wrapped, passphrase);
    draw(await decryptFile(mapBlob, dataKey));
  } catch (e) {
    $("status").innerHTML = `<span style="color:#d85a30">${e.message}. Wrong passphrase, or no data yet.</span>`;
  }
}

function demo() {
  const cells = [];
  for (const [lat, lon, lvl, n] of [[31.5,34.47,3,40],[33.89,35.5,2,18],[35.69,51.39,1,9],[33.31,44.36,2,22]])
    cells.push({ lat, lon, level: lvl, count: n, heat: 6 + Math.random() * 4 });
  draw({ generated_at: new Date().toISOString(), coverage_pct: 37, hot_cells: 295,
         covered_hot_cells: 109, active: cells,
         blind: [{ lat: 36.2, lon: 37.16, heat: 7 }, { lat: 15.37, lon: 44.19, heat: 7 }] });
  $("status").innerHTML += "<br><i>(demo data)</i>";
}

$("go").onclick = () => loadLive($("pass").value);
$("pass").addEventListener("keydown", (e) => { if (e.key === "Enter") loadLive($("pass").value); });
$("demo").onclick = demo;
$("toggleBlind").addEventListener("change", (e) => {
  if (e.target.checked) { map.addLayer(gaps); if (lastSnap) drawGaps(lastSnap); }
  else { map.removeLayer(gaps); }
});
