import * as THREE from "three";

let satelliteState = null;

const socket = new WebSocket("ws://127.0.0.1:8000/ws");

const Y_AXIS = new THREE.Vector3(0, 1, 0);
const targetEarthRotation = new THREE.Quaternion();
const currentEarthRotation = new THREE.Quaternion();

socket.onopen = (event) => {
  console.log("WebSocket connection established!");
};

socket.onmessage = (event) => {
  satelliteState = JSON.parse(event.data);
  // console.log(satelliteState);

  if (satelliteState.earth_rotation_angle) {
    targetEarthRotation.setFromAxisAngle(
      Y_AXIS,
      satelliteState.earth_rotation_angle
    );
  }
};

socket.onerror = (error) => {
  console.error("❌ WebSocket Error:", error);
};

socket.onclose = (event) => {
  console.log("WebSocket connection closed.");
};

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
  50,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);

const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const earthGeometry = new THREE.SphereGeometry(6, 64, 64);
const earthMaterial = new THREE.MeshBasicMaterial({
  color: 0x0000ff,
  wireframe: true,
});
const earth = new THREE.Mesh(earthGeometry, earthMaterial);
scene.add(earth);

const cubeGeometry = new THREE.BoxGeometry(0.07, 0.07, 0.2);
const cubeMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
scene.add(cube);

camera.position.z = 20;

function animate() {
  if (satelliteState) {
    const scale = 1 / 1000;

    const targetPosition = new THREE.Vector3(
      satelliteState.orbit.position[0] * scale,
      satelliteState.orbit.position[2] * scale,
      satelliteState.orbit.position[1] * scale
    );
    cube.position.lerp(targetPosition, 0.1);

    currentEarthRotation.slerp(targetEarthRotation, 0.1);
    earth.setRotationFromQuaternion(currentEarthRotation);
  }
  renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);
