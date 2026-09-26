# Three.js snippets

Use these as project-local starting points, not as a replacement for the
project's rendering architecture. The relevant official references are the
[responsive canvas guide](https://threejs.org/manual/pages/responsive.html),
[WebGLRenderer API](https://threejs.org/docs/pages/WebGLRenderer.html), and
[GLTFLoader API](https://threejs.org/docs/pages/GLTFLoader.html).

## Responsive animated scene

```ts
import * as THREE from 'three';

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
container.append(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
camera.position.set(0, 0.4, 4);

function resize() {
  const { clientWidth: width, clientHeight: height } = container;
  const dpr = Math.min(window.devicePixelRatio, 2);
  const bufferWidth = Math.floor(width * dpr);
  const bufferHeight = Math.floor(height * dpr);
  if (renderer.domElement.width === bufferWidth && renderer.domElement.height === bufferHeight) return;
  renderer.setSize(bufferWidth, bufferHeight, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

renderer.setAnimationLoop(() => {
  resize();
  renderer.render(scene, camera);
});

// Cleanup when the component/page is disposed.
renderer.setAnimationLoop(null);
renderer.dispose();
renderer.domElement.remove();
```

Use CSS to size `container`/canvas. Do not set both CSS dimensions and
renderer CSS dimensions in competing places. For static product viewers,
render on demand instead of continuously.

## Load a GLTF/GLB asset

```ts
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const gltf = await loader.loadAsync('/models/product.glb');
gltf.scene.traverse((object) => {
  if ('castShadow' in object) object.castShadow = true;
  if ('receiveShadow' in object) object.receiveShadow = true;
});
scene.add(gltf.scene);
```

Add Draco, KTX2, or Meshopt decoders only when the supplied asset uses the
matching compression. Dispose loaded textures/materials when replacing the
model or unmounting the scene.

## Reduced-motion contract

```ts
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
if (reducedMotion.matches) {
  renderer.setAnimationLoop(null);
  renderer.render(scene, camera);
} else {
  renderer.setAnimationLoop(render);
}
```

Keep the page's primary content and CTA available in semantic HTML; the canvas
is enhancement, not the only route to information or interaction.
