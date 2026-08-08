import * as THREE from 'three';

const NODE_RADIUS = 1.2;
const API_URL = '/api/graph/';
const POSITIONS_URL = '/api/graph/positions/';

const welcomeScreen = document.getElementById('welcome-screen');
const welcomeClose = document.getElementById('welcome-close');
const graphContainer = document.getElementById('graph-container');
const canvas = document.getElementById('graph-canvas');
const tooltip = document.getElementById('tooltip');
const popup = document.getElementById('person-popup');
const popupOverlay = popup.querySelector('.person-popup__overlay');
const popupClose = popup.querySelector('.person-popup__close');
const popupPhoto = popup.querySelector('.person-popup__photo');
const popupInitials = popup.querySelector('.person-popup__initials');
const popupName = popup.querySelector('.person-popup__name');
const popupBio = popup.querySelector('.person-popup__bio');
const popupLink = popup.querySelector('.person-popup__link');
const layoutToast = document.getElementById('layout-toast');

const canSaveLayout = graphContainer?.dataset?.canSaveLayout === '1';

let scene, camera, renderer, raycaster, mouse;
let nodeMeshes = [];
let edgeLines = [];
let graphData = null;
let hoveredNode = null;
let draggedNode = null;
let isPanning = false;
let panStart = { x: 0, y: 0 };
let cameraStart = { x: 0, y: 0 };
let toastTimer = null;

function getCookie(name) {
    const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
    return match ? decodeURIComponent(match[1]) : '';
}

function showLayoutToast(message) {
    if (!layoutToast) return;
    layoutToast.textContent = message;
    layoutToast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        layoutToast.hidden = true;
    }, 1800);
}

async function saveNodePosition(mesh) {
    if (!canSaveLayout || !mesh) return;
    const csrf = getCookie('csrftoken');
    try {
        const response = await fetch(POSITIONS_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf,
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                positions: [{
                    id: mesh.userData.id,
                    x: Number(mesh.position.x.toFixed(3)),
                    y: Number(mesh.position.y.toFixed(3)),
                }],
            }),
        });
        if (!response.ok) {
            showLayoutToast('Не удалось сохранить');
            return;
        }
        mesh.userData.x = mesh.position.x;
        mesh.userData.y = mesh.position.y;
        showLayoutToast('Позиция сохранена');
    } catch {
        showLayoutToast('Ошибка сети');
    }
}

welcomeClose.addEventListener('click', () => {
    welcomeScreen.classList.add('welcome-screen--hidden');
    graphContainer.classList.remove('graph-container--hidden');
    initGraph();
});

popupClose.addEventListener('click', closePopup);
popupOverlay.addEventListener('click', closePopup);

function closePopup() {
    popup.hidden = true;
}

function showPopup(nodeData) {
    popupName.textContent = nodeData.full_name;
    popupBio.textContent = nodeData.short_bio || 'Информация пока не добавлена.';
    popupLink.href = nodeData.detail_url;

    if (nodeData.photo_url) {
        popupPhoto.src = nodeData.photo_url;
        popupPhoto.alt = nodeData.full_name;
        popupPhoto.hidden = false;
        popupInitials.hidden = true;
    } else {
        popupPhoto.hidden = true;
        popupInitials.hidden = false;
        popupInitials.textContent = nodeData.node_label || nodeData.initials;
    }

    popup.hidden = false;
}

function createLabelTexture(label) {
    const size = 256;
    const canvasEl = document.createElement('canvas');
    canvasEl.width = size;
    canvasEl.height = size;
    const ctx = canvasEl.getContext('2d');

    ctx.fillStyle = '#2a2622';
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#c4a882';
    ctx.lineWidth = 6;
    ctx.stroke();

    const text = (label || '').trim() || '?';
    const parts = text.split(/\s+/);
    const line1 = parts[0] || text;
    const line2 = parts.slice(1).join(' ');

    ctx.fillStyle = '#c4a882';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const maxWidth = size * 0.78;
    const fitFont = (content, maxPx, minPx) => {
        let px = maxPx;
        while (px > minPx) {
            ctx.font = `600 ${px}px Cormorant Garamond, Georgia, serif`;
            if (ctx.measureText(content).width <= maxWidth) break;
            px -= 2;
        }
        return px;
    };

    if (line2) {
        const size1 = fitFont(line1, 42, 18);
        const size2 = fitFont(line2, 36, 16);
        ctx.font = `600 ${size1}px Cormorant Garamond, Georgia, serif`;
        ctx.fillText(line1, size / 2, size / 2 - 22);
        ctx.font = `600 ${size2}px Cormorant Garamond, Georgia, serif`;
        ctx.fillText(line2, size / 2, size / 2 + 26);
    } else {
        const size1 = fitFont(line1, 48, 18);
        ctx.font = `600 ${size1}px Cormorant Garamond, Georgia, serif`;
        ctx.fillText(line1, size / 2, size / 2 + 2);
    }

    const texture = new THREE.CanvasTexture(canvasEl);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
}

function loadPhotoTexture(url) {
    return new Promise((resolve, reject) => {
        const loader = new THREE.TextureLoader();
        loader.load(
            url,
            (texture) => {
                texture.colorSpace = THREE.SRGBColorSpace;
                resolve(texture);
            },
            undefined,
            reject,
        );
    });
}

async function createNodeMesh(nodeData, position) {
    const label = nodeData.node_label || nodeData.initials;
    let texture;
    if (nodeData.photo_url) {
        try {
            texture = await loadPhotoTexture(nodeData.photo_url);
        } catch {
            texture = createLabelTexture(label);
        }
    } else {
        texture = createLabelTexture(label);
    }

    const geometry = new THREE.CircleGeometry(NODE_RADIUS, 64);
    const material = new THREE.MeshBasicMaterial({
        map: texture,
        transparent: true,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(position.x, position.y, 0);
    mesh.userData = { ...nodeData, isNode: true };

    const borderGeometry = new THREE.RingGeometry(NODE_RADIUS, NODE_RADIUS + 0.08, 64);
    const borderMaterial = new THREE.MeshBasicMaterial({
        color: 0xc4a882,
        transparent: true,
        opacity: 0.6,
    });
    const border = new THREE.Mesh(borderGeometry, borderMaterial);
    mesh.add(border);

    return mesh;
}

function autoLayout(nodes) {
    const allZero = nodes.every((n) => n.x === 0 && n.y === 0);
    if (!allZero) {
        return nodes.map((n) => ({ id: n.id, x: n.x, y: n.y }));
    }

    const count = nodes.length;
    const radius = Math.max(4, count * 0.8);
    return nodes.map((n, i) => {
        const angle = (i / count) * Math.PI * 2;
        return {
            id: n.id,
            x: Math.cos(angle) * radius,
            y: Math.sin(angle) * radius,
        };
    });
}

function createEdgeLine(from, to, type) {
    const colors = {
        'parent-child': 0x6b8f71,
        sibling: 0x8f6b7a,
        spouse: 0xc4a882,
    };
    const color = colors[type] || 0x888888;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array([
        from.x, from.y, -0.1,
        to.x, to.y, -0.1,
    ]);
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: 0.7,
        linewidth: 2,
    });

    const line = new THREE.Line(geometry, material);
    line.userData = { fromId: from.id, toId: to.id, type };
    return line;
}

function updateEdgePositions() {
    const posMap = {};
    nodeMeshes.forEach((mesh) => {
        posMap[mesh.userData.id] = mesh.position;
    });

    edgeLines.forEach((line) => {
        const from = posMap[line.userData.fromId];
        const to = posMap[line.userData.toId];
        if (from && to) {
            const positions = line.geometry.attributes.position.array;
            positions[0] = from.x;
            positions[1] = from.y;
            positions[3] = to.x;
            positions[4] = to.y;
            line.geometry.attributes.position.needsUpdate = true;
        }
    });
}

function getWorldMouse(event) {
    const rect = canvas.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

function getIntersectedNode() {
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(nodeMeshes);
    return intersects.length > 0 ? intersects[0].object : null;
}

function onMouseMove(event) {
    getWorldMouse(event);

    if (draggedNode) {
        const vector = new THREE.Vector3(mouse.x, mouse.y, 0.5);
        vector.unproject(camera);
        draggedNode.position.x = vector.x;
        draggedNode.position.y = vector.y;
        updateEdgePositions();
        return;
    }

    if (isPanning) {
        const dx = event.clientX - panStart.x;
        const dy = event.clientY - panStart.y;
        camera.position.x = cameraStart.x - dx * 0.02;
        camera.position.y = cameraStart.y + dy * 0.02;
        return;
    }

    const node = getIntersectedNode();
    if (node !== hoveredNode) {
        if (hoveredNode) {
            hoveredNode.scale.set(1, 1, 1);
        }
        hoveredNode = node;
        if (node) {
            node.scale.set(1.1, 1.1, 1.1);
            tooltip.textContent = node.userData.full_name;
            tooltip.hidden = false;
            canvas.style.cursor = 'pointer';
        } else {
            tooltip.hidden = true;
            canvas.style.cursor = isPanning ? 'grabbing' : 'grab';
        }
    }

    if (hoveredNode) {
        tooltip.style.left = `${event.clientX}px`;
        tooltip.style.top = `${event.clientY}px`;
    }
}

function onMouseDown(event) {
    if (event.button !== 0) return;
    getWorldMouse(event);

    const node = getIntersectedNode();
    if (node) {
        draggedNode = node;
        canvas.style.cursor = 'grabbing';
    } else {
        isPanning = true;
        panStart = { x: event.clientX, y: event.clientY };
        cameraStart = { x: camera.position.x, y: camera.position.y };
        canvas.style.cursor = 'grabbing';
    }
}

function onMouseUp(event) {
    if (event.button !== 0) return;

    if (draggedNode && !isPanning) {
        const moved =
            Math.abs(draggedNode.position.x - draggedNode.userData._startX) > 0.05 ||
            Math.abs(draggedNode.position.y - draggedNode.userData._startY) > 0.05;

        if (!moved) {
            showPopup(draggedNode.userData);
        } else if (canSaveLayout) {
            saveNodePosition(draggedNode);
        }
    }

    draggedNode = null;
    isPanning = false;
    canvas.style.cursor = hoveredNode ? 'pointer' : 'grab';
}

function onMouseDownTrackStart(event) {
    if (event.button !== 0) return;
    getWorldMouse(event);
    const node = getIntersectedNode();
    if (node) {
        node.userData._startX = node.position.x;
        node.userData._startY = node.position.y;
    }
}

function onWheel(event) {
    event.preventDefault();
    const zoomFactor = event.deltaY > 0 ? 1.1 : 0.9;
    camera.zoom = THREE.MathUtils.clamp(camera.zoom * (1 / zoomFactor), 0.3, 5);
    camera.updateProjectionMatrix();
}

async function initGraph() {
    const response = await fetch(API_URL);
    graphData = await response.json();

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f0e0d);

    const aspect = window.innerWidth / window.innerHeight;
    const viewSize = 12;
    camera = new THREE.OrthographicCamera(
        -viewSize * aspect,
        viewSize * aspect,
        viewSize,
        -viewSize,
        0.1,
        100,
    );
    camera.position.z = 10;

    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    raycaster = new THREE.Raycaster();
    mouse = new THREE.Vector2();

    const positions = autoLayout(graphData.nodes);
    const posMap = {};
    positions.forEach((p) => {
        posMap[p.id] = p;
    });

    for (const nodeData of graphData.nodes) {
        const pos = posMap[nodeData.id] || { x: 0, y: 0 };
        const mesh = await createNodeMesh(nodeData, pos);
        scene.add(mesh);
        nodeMeshes.push(mesh);
    }

    for (const edge of graphData.edges) {
        const fromPos = posMap[edge.source];
        const toPos = posMap[edge.target];
        if (fromPos && toPos) {
            const line = createEdgeLine(
                { ...fromPos, id: edge.source },
                { ...toPos, id: edge.target },
                edge.type,
            );
            scene.add(line);
            edgeLines.push(line);
        }
    }

    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mousedown', onMouseDownTrackStart);
    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('mouseleave', onMouseUp);
    canvas.addEventListener('wheel', onWheel, { passive: false });

    window.addEventListener('resize', onResize);
    animate();
}

function onResize() {
    if (!camera || !renderer) return;
    const aspect = window.innerWidth / window.innerHeight;
    const viewSize = 12;
    camera.left = -viewSize * aspect;
    camera.right = viewSize * aspect;
    camera.top = viewSize;
    camera.bottom = -viewSize;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
