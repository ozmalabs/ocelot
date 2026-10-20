// Three.js 3D Physics Graph Visualizer for OCELOT (G, Γ, C) Substrate
// Features: 3D Force-Directed Layout, Energy Pulses, Node Birth Glow, 3D Labels, Raycasting, OrbitControls.

import * as THREE from './vendor/three.module.js';
import { OrbitControls } from './vendor/OrbitControls.js';
import { NODE_FAMILIES, getNodeFamily } from './graph_view.js';

export class GraphVisualizer3D {
  constructor(containerElement, options = {}) {
    this.container = containerElement;
    this.options = Object.assign({
      charge: -600,
      linkDistance: 70,
      linkStrength: 0.06,
      damping: 0.88,
      nodeRadius: 4.5,
      autoRotate: false,
      particleSpeed: 0.015,
    }, options);

    this.nodes = new Map(); // id -> { id, type, attrs, x, y, z, vx, vy, vz, mesh, sprite, family, activeGlow }
    this.links = [];        // [{ src, tgt, type, lineMesh, particles }]
    this.selectedNode = null;
    this.hoveredNode = null;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2(-999, -999);
    this.plane = new THREE.Plane();
    this.planeIntersect = new THREE.Vector3();

    this.draggedNode = null;
    this.isDragging = false;
    this.animId = null;
    this.onSelectCallback = null;

    // Node geometries & material caches
    this.nodeGeometry = new THREE.SphereGeometry(this.options.nodeRadius, 24, 24);
    this.haloGeometry = new THREE.RingGeometry(this.options.nodeRadius * 1.2, this.options.nodeRadius * 1.6, 32);
    this.particleGeometry = new THREE.SphereGeometry(1.2, 8, 8);
    this.particleMaterial = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });

    this.materialsByColor = new Map();

    this._initThree();
    this._bindEvents();
    this.start();
  }

  onSelect(callback) {
    this.onSelectCallback = callback;
  }

  _getMaterial(colorHex, emissiveIntensity = 0.3) {
    const key = `${colorHex}_${emissiveIntensity}`;
    if (!this.materialsByColor.has(key)) {
      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(colorHex),
        roughness: 0.25,
        metalness: 0.65,
        emissive: new THREE.Color(colorHex),
        emissiveIntensity: emissiveIntensity,
      });
      this.materialsByColor.set(key, mat);
    }
    return this.materialsByColor.get(key);
  }

  _initThree() {
    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 600;

    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x070b14);
    this.scene.fog = new THREE.FogExp2(0x070b14, 0.0018);

    // Camera
    this.camera = new THREE.PerspectiveCamera(55, width / height, 0.5, 2000);
    this.camera.position.set(0, 80, 220);

    // Renderer
    this.renderer = this.options.renderer || new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(width, height);
    if (this.renderer.setPixelRatio && typeof window !== 'undefined') {
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    }
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.1;
    this.container.appendChild(this.renderer.domElement);

    // Controls
    this.controls = this.options.controls || new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxDistance = 800;
    this.controls.minDistance = 15;
    this.controls.autoRotate = this.options.autoRotate;
    this.controls.autoRotateSpeed = 1.0;

    // Lighting
    const ambient = new THREE.AmbientLight(0xffffff, 0.85);
    this.scene.add(ambient);

    const keyLight = new THREE.DirectionalLight(0x38bdf8, 1.6);
    keyLight.position.set(100, 150, 100);
    this.scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x818cf8, 1.2);
    fillLight.position.set(-100, -80, -100);
    this.scene.add(fillLight);

    // Spatial grid floor
    const grid = new THREE.GridHelper(400, 40, 0x1e293b, 0x0f172a);
    grid.position.y = -60;
    this.scene.add(grid);

    // Starfield particles in background
    const starGeo = new THREE.BufferGeometry();
    const starCount = 350;
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {
      starPos[i] = (Math.random() - 0.5) * 800;
      starPos[i + 1] = (Math.random() - 0.5) * 600;
      starPos[i + 2] = (Math.random() - 0.5) * 800;
    }
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({ color: 0x475569, size: 1.5, transparent: true, opacity: 0.6 });
    this.scene.add(new THREE.Points(starGeo, starMat));
  }

  resize() {
    if (!this.container || !this.renderer) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  _createLabelSprite(text) {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
    ctx.roundRect(4, 8, 248, 48, 10);
    ctx.fill();

    ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
    ctx.lineWidth = 2;
    ctx.roundRect(4, 8, 248, 48, 10);
    ctx.stroke();

    ctx.font = 'bold 20px system-ui, sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 128, 32);

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(16, 4, 1);
    return sprite;
  }

  setSnapshot(snapshot) {
    if (!snapshot || !Array.isArray(snapshot.nodes)) return;

    const newNodes = new Map();
    const existingNodes = this.nodes;

    // Process Nodes
    for (const n of snapshot.nodes) {
      const id = String(n.id);
      const existing = existingNodes.get(id);
      const fam = getNodeFamily(n.type);
      const label = n.attrs?.name || n.attrs?.tag || n.attrs?.label || n.type;

      let x, y, z;
      if (existing) {
        x = existing.x;
        y = existing.y;
        z = existing.z;
      } else {
        // Initial 3D placement by family
        let yOffset = (Math.random() - 0.5) * 40;
        if (fam.key === 'theory') yOffset += 30; // Elevated hypotheses canopy
        if (fam.key === 'signal') yOffset -= 30; // Perceptual floor
        x = (Math.random() - 0.5) * 120;
        y = yOffset;
        z = (Math.random() - 0.5) * 120;
      }

      let mesh, sprite;
      if (existing) {
        mesh = existing.mesh;
        sprite = existing.sprite;
      } else {
        // Create 3D sphere mesh
        const mat = this._getMaterial(fam.color, 0.35);
        mesh = new THREE.Mesh(this.nodeGeometry, mat);
        mesh.userData = { nodeId: id };
        this.scene.add(mesh);

        // Create 3D billboard text label
        sprite = this._createLabelSprite(`${label} #${n.id}`);
        this.scene.add(sprite);

        // Birth animation flag
        mesh.scale.set(0.1, 0.1, 0.1);
      }

      newNodes.set(id, {
        id,
        rawId: n.id,
        type: n.type,
        label,
        attrs: n.attrs || {},
        family: fam,
        x, y, z,
        vx: existing ? existing.vx : 0,
        vy: existing ? existing.vy : 0,
        vz: existing ? existing.vz : 0,
        mesh,
        sprite,
        scale: existing ? existing.scale : 0.1,
        activeGlow: existing ? existing.activeGlow : 1.0,
      });
    }

    // Clean up removed nodes
    for (const [id, node] of existingNodes) {
      if (!newNodes.has(id)) {
        this.scene.remove(node.mesh);
        this.scene.remove(node.sprite);
      }
    }

    // Clean up old links
    for (const link of this.links) {
      this.scene.remove(link.lineMesh);
      if (link.particle) this.scene.remove(link.particle);
    }

    // Process Edges & Link Beams
    const newLinks = [];
    if (Array.isArray(snapshot.edges)) {
      for (const e of snapshot.edges) {
        const srcId = String(e.src);
        const tgtId = String(e.tgt);
        if (newNodes.has(srcId) && newNodes.has(tgtId)) {
          const src = newNodes.get(srcId);
          const tgt = newNodes.get(tgtId);

          // Line geometry
          const lineGeo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(src.x, src.y, src.z),
            new THREE.Vector3(tgt.x, tgt.y, tgt.z),
          ]);
          const lineMat = new THREE.LineBasicMaterial({
            color: 0x334155,
            transparent: true,
            opacity: 0.55,
            linewidth: 1,
          });
          const lineMesh = new THREE.Line(lineGeo, lineMat);
          this.scene.add(lineMesh);

          // Energy Packet Particle (travels along edge)
          const particle = new THREE.Mesh(this.particleGeometry, this.particleMaterial);
          this.scene.add(particle);

          newLinks.push({
            src,
            tgt,
            type: e.type,
            attrs: e.attrs || {},
            lineMesh,
            particle,
            particleProgress: Math.random(),
          });
        }
      }
    }

    this.nodes = newNodes;
    this.links = newLinks;

    if (this.selectedNode && this.nodes.has(this.selectedNode.id)) {
      this.selectedNode = this.nodes.get(this.selectedNode.id);
    } else {
      this.selectedNode = null;
    }
  }

  _bindEvents() {
    window.addEventListener('resize', () => this.resize());

    const dom = this.renderer.domElement;

    dom.addEventListener('mousemove', (e) => {
      const rect = dom.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      if (this.isDragging && this.draggedNode) {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        if (this.raycaster.ray.intersectPlane(this.plane, this.planeIntersect)) {
          this.draggedNode.x = this.planeIntersect.x;
          this.draggedNode.y = this.planeIntersect.y;
          this.draggedNode.z = this.planeIntersect.z;
          this.draggedNode.vx = 0;
          this.draggedNode.vy = 0;
          this.draggedNode.vz = 0;
        }
      }
    });

    dom.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return; // Left click only
      this.raycaster.setFromCamera(this.mouse, this.camera);
      const meshes = Array.from(this.nodes.values()).map(n => n.mesh);
      const intersects = this.raycaster.intersectObjects(meshes);

      if (intersects.length > 0) {
        const hitMesh = intersects[0].object;
        const nodeId = hitMesh.userData.nodeId;
        const node = this.nodes.get(nodeId);

        this.selectedNode = node;
        this.draggedNode = node;
        this.isDragging = true;
        this.controls.enabled = false; // Disable orbit while dragging node

        // Setup dragging plane perpendicular to camera
        const normal = this.camera.getWorldDirection(new THREE.Vector3()).negate();
        this.plane.setFromNormalAndCoplanarPoint(normal, new THREE.Vector3(node.x, node.y, node.z));

        if (this.onSelectCallback) this.onSelectCallback(node);
      } else {
        this.selectedNode = null;
        if (this.onSelectCallback) this.onSelectCallback(null);
      }
    });

    window.addEventListener('mouseup', () => {
      if (this.isDragging) {
        this.isDragging = false;
        this.draggedNode = null;
        this.controls.enabled = true;
      }
    });
  }

  stepPhysics() {
    const nodes = Array.from(this.nodes.values());
    const count = nodes.length;
    if (count === 0) return;

    // 1. 3D Coulomb Repulsion
    for (let i = 0; i < count; i++) {
      const n1 = nodes[i];
      for (let j = i + 1; j < count; j++) {
        const n2 = nodes[j];
        let dx = n2.x - n1.x;
        let dy = n2.y - n1.y;
        let dz = n2.z - n1.z;
        let distSq = dx * dx + dy * dy + dz * dz;
        if (distSq < 1) distSq = 1;
        const dist = Math.sqrt(distSq);

        if (dist < 300) {
          const force = this.options.charge / distSq;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          const fz = (dz / dist) * force;

          if (n1 !== this.draggedNode) {
            n1.vx += fx;
            n1.vy += fy;
            n1.vz += fz;
          }
          if (n2 !== this.draggedNode) {
            n2.vx -= fx;
            n2.vy -= fy;
            n2.vz -= fz;
          }
        }
      }
    }

    // 2. 3D Hooke Spring Attraction
    for (const link of this.links) {
      const src = link.src;
      const tgt = link.tgt;
      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dz = tgt.z - src.z;
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
      const displacement = dist - this.options.linkDistance;
      const force = displacement * this.options.linkStrength;

      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      const fz = (dz / dist) * force;

      if (src !== this.draggedNode) {
        src.vx += fx;
        src.vy += fy;
        src.vz += fz;
      }
      if (tgt !== this.draggedNode) {
        tgt.vx -= fx;
        tgt.vy -= fy;
        tgt.vz -= fz;
      }
    }

    // 3. Centering force & update coordinates
    for (const n of nodes) {
      if (n !== this.draggedNode) {
        n.vx -= n.x * 0.003;
        n.vy -= n.y * 0.003;
        n.vz -= n.z * 0.003;

        n.vx *= this.options.damping;
        n.vy *= this.options.damping;
        n.vz *= this.options.damping;

        n.x += n.vx;
        n.y += n.vy;
        n.z += n.vz;
      }

      // Smooth birth scale-up animation
      if (n.scale < 1.0) {
        n.scale += 0.08;
        if (n.scale > 1.0) n.scale = 1.0;
        n.mesh.scale.set(n.scale, n.scale, n.scale);
      }

      // Sync 3D Mesh & Sprite positions
      n.mesh.position.set(n.x, n.y, n.z);
      n.sprite.position.set(n.x, n.y + this.options.nodeRadius + 6, n.z);

      // Highlight selected node
      const isSelected = this.selectedNode && n.id === this.selectedNode.id;
      if (isSelected) {
        n.mesh.material.emissiveIntensity = 0.85;
      } else {
        n.mesh.material.emissiveIntensity = 0.35;
      }
    }

    // 4. Update Link Lines & Moving Energy Packets (Shows what the graph is doing!)
    for (const link of this.links) {
      const src = link.src;
      const tgt = link.tgt;

      // Update line geometry points
      const positions = link.lineMesh.geometry.attributes.position.array;
      positions[0] = src.x; positions[1] = src.y; positions[2] = src.z;
      positions[3] = tgt.x; positions[4] = tgt.y; positions[5] = tgt.z;
      link.lineMesh.geometry.attributes.position.needsUpdate = true;

      // Highlight connected lines
      const isConnected = this.selectedNode && (src.id === this.selectedNode.id || tgt.id === this.selectedNode.id);
      link.lineMesh.material.color.setHex(isConnected ? 0x38bdf8 : 0x334155);
      link.lineMesh.material.opacity = isConnected ? 0.9 : 0.45;

      // Advance energy pulse along edge
      link.particleProgress += this.options.particleSpeed;
      if (link.particleProgress > 1.0) link.particleProgress = 0;

      const px = src.x + (tgt.x - src.x) * link.particleProgress;
      const py = src.y + (tgt.y - src.y) * link.particleProgress;
      const pz = src.z + (tgt.z - src.z) * link.particleProgress;
      link.particle.position.set(px, py, pz);
    }
  }

  resetView() {
    this.camera.position.set(0, 80, 220);
    this.camera.lookAt(0, 0, 0);
    this.controls.target.set(0, 0, 0);
  }

  toggleAutoRotate() {
    this.controls.autoRotate = !this.controls.autoRotate;
    return this.controls.autoRotate;
  }

  start() {
    const rAF = (typeof requestAnimationFrame !== 'undefined') ? requestAnimationFrame : (cb) => setTimeout(cb, 16);
    const loop = () => {
      this.stepPhysics();
      if (this.controls) this.controls.update();
      if (this.renderer && this.scene && this.camera) {
        this.renderer.render(this.scene, this.camera);
      }
      this.animId = rAF(loop);
    };
    this.animId = rAF(loop);
  }

  stop() {
    if (this.animId) {
      const cAF = (typeof cancelAnimationFrame !== 'undefined') ? cancelAnimationFrame : clearTimeout;
      cAF(this.animId);
      this.animId = null;
    }
  }
}
