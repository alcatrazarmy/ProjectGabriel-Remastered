import { createAvatar } from './avatar.js';
const $ = id => document.getElementById(id);
const voice = $('voice');
let context, analyser, waveform, generation = 0, aborter, finishPlayback;
let mouth = 0, companionMouth = 0, companionSeen = 0, companionThinking = false;
const canvas = $('avatar');

function notice(text) { $('notice').textContent = text; }
function message(role, text) {
  const p = document.createElement('p'); p.className = `message ${role}`;
  p.textContent = `${role === 'user' ? 'You' : 'Yelena'}: ${text}`;
  $('messages').append(p); p.scrollIntoView({block: 'nearest'});
}
async function response(url, options = {}) {
  const r = await fetch(url, options);
  if (!r.ok) {
    let detail; try { detail = (await r.json()).detail; } catch { /* no server detail */ }
    throw Error(typeof detail === 'string' ? detail : `Request failed (${r.status}).`);
  }
  return r;
}
function post(url, body, signal) {
  return response(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body), signal});
}
async function enableAudio() {
  if (!context) {
    context = new AudioContext(); analyser = context.createAnalyser(); analyser.fftSize = 512;
    waveform = new Float32Array(analyser.fftSize);
    context.createMediaElementSource(voice).connect(analyser); analyser.connect(context.destination);
  }
  await context.resume();
}
async function refreshOutputs() {
  const selected = $('output').value;
  $('output').replaceChildren(new Option('Windows default audio', ''));
  const devices = await navigator.mediaDevices.enumerateDevices();
  for (const d of devices.filter(d => d.kind === 'audiooutput' && d.deviceId !== 'default')) {
    $('output').add(new Option(d.label || 'Audio output (name unavailable)', d.deviceId));
  }
  if ([...$('output').options].some(o => o.value === selected)) $('output').value = selected;
}
$('refresh-output').onclick = () => refreshOutputs().then(() => notice('Audio list refreshed. If Quest audio is hidden, select it in Windows Sound settings.')).catch(e => notice(e.message));
$('output').onchange = async () => {
  try {
    await enableAudio();
    if (!context.setSinkId) throw Error('Choose the headset output in Windows Sound settings; this browser cannot switch it here.');
    await context.setSinkId($('output').value); notice('Audio output selected.');
  } catch (e) { notice(e.message); }
};
function stop() {
  generation++; aborter?.abort(); voice.pause(); voice.removeAttribute('src'); voice.load();
  finishPlayback?.(); mouth = 0;
}
$('stop').onclick = () => { stop(); notice('Voice stopped.'); };
function play(blob, token) {
  return new Promise((resolve, reject) => {
    if (token !== generation) return resolve();
    const url = URL.createObjectURL(blob);
    const cleanup = () => {
      voice.onended = null; voice.onerror = null; finishPlayback = null;
      URL.revokeObjectURL(url); mouth = 0;
    };
    finishPlayback = () => { cleanup(); resolve(); };
    voice.onended = () => { cleanup(); resolve(); };
    voice.onerror = () => { cleanup(); reject(Error('Audio playback failed. Check the selected output.')); };
    voice.src = url;
    voice.play().catch(e => { cleanup(); reject(e); });
  });
}
function speechChunks(text) {
  const chunks = []; let rest = text.trim();
  while (rest) {
    let end = Math.min(500, rest.length);
    if (rest.length > 500) { const space = rest.lastIndexOf(' ', 500); if (space > 0) end = space; }
    chunks.push(rest.slice(0, end)); rest = rest.slice(end).trimStart();
  }
  return chunks;
}
async function speak(text, token, signal) {
  for (const chunk of speechChunks(text)) {
    if (token !== generation) break;
    notice('Preparing Lisa’s voice…');
    const wav = await post('/api/speak', {text: chunk}, signal);
    if (token !== generation) break;
    notice('Yelena is speaking.'); await play(await wav.blob(), token);
  }
}
let busy = false;
async function run(action) {
  if (busy) return;
  stop(); busy = true;
  const token = generation; aborter = new AbortController();
  for (const id of ['sample', 'send', 'speak']) $(id).disabled = true;
  try {
    await enableAudio(); await action(token, aborter.signal);
    if (token === generation) notice('Ready.');
  } catch (e) { if (e.name !== 'AbortError' && token === generation) notice(e.message); }
  finally { busy = false; for (const id of ['sample', 'send', 'speak']) $(id).disabled = false; }
}
$('sample').onclick = () => run(async (token, signal) => {
  const sample = await response('/api/sample', {signal});
  await play(await sample.blob(), token);
});
$('speak').onclick = () => {
  const text = $('text').value.trim();
  if (!text) return notice('Enter some text for Lisa to read.');
  run((token, signal) => speak(text, token, signal));
};
$('chat').onsubmit = async event => {
  event.preventDefault(); const text = $('text').value.trim(); if (!text) return;
  $('send').disabled = true;
  try {
    await post('/api/companion/chat', {text});
    $('text').value = ''; notice('Sent to the original app. Its selected speaker plays the reply.');
  } catch (e) { notice(e.message); }
  finally { $('send').disabled = false; }
};

let cursor = '', lastRole = '', lastBubble;
async function pollCompanion() {
  try {
    const state = await (await response('/api/companion?after=' + encodeURIComponent(cursor))).json();
    companionMouth = state.mouth; companionSeen = performance.now(); companionThinking = state.thinking;
    $('connection').textContent = state.connected
      ? 'Original app connected - ' + (state.microphone ? 'microphone ready' : 'type to talk; microphone unavailable')
      : 'Original app is reconnecting...';
    for (const entry of state.events) {
      cursor = entry.timestamp;
      if (entry.type === 'error') { notice(entry.content); continue; }
      const role = entry.type === 'transcription' ? 'user' : 'assistant';
      if (role === 'user' || role !== lastRole || !lastBubble) {
        const p = document.createElement('p'); p.className = `message ${role}`;
        p.textContent = (role === 'user' ? 'You: ' : 'Yelena: ') + entry.content;
        $('messages').append(p); lastBubble = p;
      } else lastBubble.textContent += entry.content;
      lastRole = role; $('messages').scrollTop = $('messages').scrollHeight;
    }
  } catch (e) {
    companionMouth = 0; companionThinking = false; $('connection').textContent = e.message;
  } finally { setTimeout(pollCompanion, 160); }
}

function animationState() {
  let target = performance.now() - companionSeen < 600 ? companionMouth : 0;
  if (analyser && !voice.paused && !voice.ended) {
    analyser.getFloatTimeDomainData(waveform);
    let sum = 0; for (const value of waveform) sum += value * value;
    target = Math.max(target, Math.min(1, Math.sqrt(sum / waveform.length) * 7));
  }
  mouth += (target - mouth) * .35;
  canvas.dataset.mouth = mouth.toFixed(3);
  return {mouth, thinking: companionThinking};
}
createAvatar(canvas, animationState).then(avatar => {
  $('avatar-status').textContent = 'Breathing, blinking, and live speech movement';
  $('wave').onclick = () => avatar.wave();
}).catch(e => { $('avatar-status').textContent = `Avatar: ${e.message}`; });
pollCompanion();
refreshOutputs().catch(() => {});
