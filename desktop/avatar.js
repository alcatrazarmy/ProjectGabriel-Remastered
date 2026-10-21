import * as THREE from './vendor/three/three.module.js';
import { GLTFLoader } from './vendor/three/GLTFLoader.js';
import { OrbitControls } from './vendor/three/OrbitControls.js';

export async function createAvatar(canvas, speechState) {
  const renderer = new THREE.WebGLRenderer({canvas, antialias: true, alpha: true});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xeaf6ff, 0x647480, 2.2));
  const light = new THREE.DirectionalLight(0xfff1df, 2.5);
  light.position.set(2, 4, 3); scene.add(light);
  const camera = new THREE.PerspectiveCamera(32, 1, .01, 100);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.enablePan = true;
  controls.maxPolarAngle = Math.PI * .65;
  const gltf = await new GLTFLoader().loadAsync('/api/avatar');
  const avatar = gltf.scene;
  const vrm = gltf.parser.json.extensions?.VRM;
  if (!vrm) throw Error('The configured model needs a VRM humanoid rig.');
  avatar.rotation.y = Math.PI; // VRM 0 models face -Z.
  scene.add(avatar);
  const bones = {}, base = {};
  for (const item of vrm.humanoid.humanBones) {
    bones[item.bone] = await gltf.parser.getDependency('node', item.node);
    base[item.bone] = bones[item.bone].quaternion.clone();
  }
  if (!bones.head || !bones.leftUpperArm || !bones.rightUpperArm) throw Error('Required avatar bones are missing.');
  const morphs = {};
  for (const group of vrm.blendShapeMaster.blendShapeGroups) {
    const entries = [];
    for (const binding of group.binds) {
      const object = await gltf.parser.getDependency('mesh', binding.mesh);
      object.traverse(child => {
        if (child.morphTargetInfluences) entries.push([child, binding.index, binding.weight / 100]);
      });
    }
    morphs[group.presetName] = entries;
  }
  const bounds = new THREE.Box3().setFromObject(avatar);
  const height = bounds.max.y - bounds.min.y;
  controls.target.set(0, bounds.min.y + height * .55, 0);
  camera.position.set(0, bounds.min.y + height * .65, height * 2.05);
  controls.minDistance = height * .6; controls.maxDistance = height * 3;
  const floor = new THREE.Mesh(new THREE.CircleGeometry(height * .7, 64),
    new THREE.MeshBasicMaterial({color: 0x254854, transparent: true, opacity: .25, depthWrite: false}));
  floor.rotation.x = -Math.PI / 2; floor.position.y = bounds.min.y + .001; scene.add(floor);
  const offset = new THREE.Quaternion(), euler = new THREE.Euler();
  function pose(name, x = 0, y = 0, z = 0) {
    if (!bones[name]) return;
    offset.setFromEuler(euler.set(x, y, z));
    bones[name].quaternion.copy(base[name]).multiply(offset);
  }
  function morph(name, value) {
    for (const [mesh, index, weight] of morphs[name] || []) mesh.morphTargetInfluences[index] = value * weight;
  }
  const leftSign = Math.sign(bones.leftLowerArm.position.x) || 1;
  const rightSign = Math.sign(bones.rightLowerArm.position.x) || -1;
  let pointerX = 0, pointerY = 0, waveUntil = 0, speech = 0, nextBlink = 2, blinkStart = -1;
  canvas.addEventListener('pointermove', event => {
    const box = canvas.getBoundingClientRect();
    pointerX = ((event.clientX - box.left) / box.width - .5) * 2;
    pointerY = ((event.clientY - box.top) / box.height - .5) * 2;
  });
  canvas.addEventListener('pointerleave', () => { pointerX = 0; pointerY = 0; });
  const start = performance.now();
  function wave() { waveUntil = (performance.now() - start) / 1000 + 3.5; }
  let last = 0, waveAmount = 0;
  renderer.setAnimationLoop(now => {
    const t = (now - start) / 1000, dt = Math.min(.05, Math.max(0, t - last)); last = t;
    const state = speechState();
    speech += (Math.min(1, state.mouth * 2) - speech) * (1 - Math.exp(-dt * 5));
    waveAmount += ((t < waveUntil ? 1 : 0) - waveAmount) * (1 - Math.exp(-dt * 6));
    const breath = Math.sin(t * 1.6), sway = Math.sin(t * .65);
    pose('spine', breath * .014, sway * .025, sway * .018);
    pose('chest', breath * .018, Math.sin(t * .8) * .012, 0);
    pose('neck', pointerY * .05, pointerX * .12, 0);
    pose('head', pointerY * .06 + Math.sin(t * 2.7) * .035 * speech,
      pointerX * .12 + Math.sin(t * .5) * .045, state.thinking ? .09 : Math.sin(t * .9) * .02);
    pose('leftUpperArm', .04 + speech * .08, 0, -leftSign * (1.18 - speech * (.12 + .08 * Math.sin(t * 2))));
    pose('leftLowerArm', 0, leftSign * (.12 + speech * .25), 0);
    pose('rightUpperArm', .04, 0, -rightSign * (1.18 - speech * .13 - waveAmount * 1.55));
    pose('rightLowerArm', 0, rightSign * (.12 + waveAmount * .35), rightSign * waveAmount * .85);
    pose('rightHand', 0, waveAmount * Math.sin(t * 10) * .25, waveAmount * Math.sin(t * 10) * .22);
    pose('leftHand', 0, 0, Math.sin(t * 1.1) * .035);
    if (t >= nextBlink) { blinkStart = t; nextBlink = t + 2.8 + Math.random() * 2.5; }
    const elapsed = t - blinkStart;
    const blink = blinkStart >= 0 && elapsed < .18 ? Math.sin(elapsed / .18 * Math.PI) : 0;
    morph('blink', blink); morph('a', state.mouth * .8);
    canvas.dataset.blink = blink.toFixed(3);
    canvas.dataset.head = bones.head.quaternion.toArray().join(',');
    canvas.dataset.arm = bones.rightUpperArm.quaternion.toArray().join(',');
    canvas.dataset.speech = speech.toFixed(3);
    const width = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== Math.round(width * renderer.getPixelRatio()) || canvas.height !== Math.round(h * renderer.getPixelRatio())) {
      renderer.setSize(width, h, false); camera.aspect = width / h; camera.updateProjectionMatrix();
    }
    controls.update(); renderer.render(scene, camera);
    canvas.dataset.ready = 'true';
  });
  return {wave};
}
