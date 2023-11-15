import { Viewer, WebIFCLoaderPlugin, AxisGizmoPlugin, TreeViewPlugin } from
  "https://cdn.jsdelivr.net/npm/@xeokit/xeokit-sdk@2.3.9/dist/xeokit-sdk.es.min.js";

import * as WebIFC from
  "https://cdn.jsdelivr.net/npm/web-ifc@0.0.34/web-ifc-api.js";


const viewer = new Viewer({
  canvasId: "xeokitCanvas",
  transparent: true
});
window.viewer = viewer;

const axisGizmo = new AxisGizmoPlugin(viewer, {
  canvasId: "gizmoCanvas"
});
window.axisGizmo = axisGizmo;

const treeView = new TreeViewPlugin(viewer, {
  containerElement: document.getElementById("treeContainer"),
  hierarchy: "containment",
  autoExpandDepth: 3
});
window.treeView = treeView;

const cameraControl = viewer.cameraControl;
cameraControl.navMode = "orbit";
cameraControl.followPointer = true;
cameraControl.on("picked", (e) => treeView.showNode(e.entity.id));
cameraControl.pivotElement = document.getElementById("pivotMarker");


async function reloadIfc () {
  const response = await google.colab.kernel.invokeFunction(
    'notebook._request_ifc',
    [],
    {}
  );
  const result = response.data['application/json'];
  if (!result.success) {
    console.log("IFC request failed");
  }
}
window.reloadIfc = reloadIfc;


function treeToggleClick() {
  const treeContainer = document.getElementById("treeContainer");
  if (treeContainer.style.display === "inline") {
    treeContainer.style.display = "none";
  } else {
    treeContainer.style.display = "inline";
  }
}
window.treeToggleClick = treeToggleClick;


function gizmoToggleClick() {
  const gizmoCanvas = document.getElementById("gizmoCanvas");
  gizmoCanvas.hidden = !gizmoCanvas.hidden;
}
window.gizmoToggleClick = gizmoToggleClick;


class StringIfcSource {
    getIFC(ifcStr, ok, err) {
      const enc = new TextEncoder();
      const arr = enc.encode(ifcStr);
      try {
        ok(arr);
      } catch (error) {
        err(error);
      }
    }
}


function setContainerSize(width="900px", height="500px") {
  const xeokitCanvas = document.getElementById("xeokitCanvas");
  xeokitCanvas.style.width = width;
  xeokitCanvas.style.height = height;
}


function setupModel(ifcStr) {
  if (window.model === undefined) {
    const ifcLoader = new WebIFCLoaderPlugin(window.viewer, {
      wasmPath: "https://cdn.jsdelivr.net/npm/@xeokit/xeokit-sdk@2.3.9/dist/",
      dataSource: new StringIfcSource(),
      objectDefaults: {
        IfcSpace: {
          pickable: false,
          opacity: 0.2
        }
      }
    });
    window.ifcLoader = ifcLoader;
    window.ifcAPI = ifcLoader._ifcAPI;
  } else {
    window.model.destroy();
    window.model = null;
  }

  const model = window.ifcLoader.load({
    id: 0,
    src: ifcStr,
    edges: true
  });
  window.model = model;
}


async function setupCamera() {
  const camera = window.viewer.camera;
  const metaScene = window.viewer.metaScene;
  // const metaModel = metaScene.metaModels[0];
  // console.log(metaScene.metaObjects);
  // console.log(metaScene.getObjectIDsInSubtree("2YC7gQ6vP1t9SHUrCHXvlj", ["My Site"]));

  const ifcAPI = window.ifcAPI;
  const siteIDs = ifcAPI.GetLineIDsWithType(0, WebIFC.IFCSITE);

  if (siteIDs.length === 0) {
    console.log("No IfcSite were found, camera not positioned.");
    return
  } else if (siteIDs.length > 1) {
    console.log("More than one IfcSite, camera positioned to the first one.");
  }
  const siteID = siteIDs.get(0);
  const site = await ifcAPI.GetLine(0, siteID);

  // const metaSite = metaScene.metaObjects[site.GlobalId.value];
  // console.log("metaSite", metaSite);

  camera.worldAxis = [
      1, 0, 0, // Right
      0, 0, 1, // Up
      0,-1, 0  // Forward
  ];
  camera.gimbalLock = false;

  const objectIDs = metaScene.getObjectIDsInSubtree(site.GlobalId.value);
  // const objectIDs = window.viewer.scene.visibleObjectIds;
  const aabb = await window.viewer.scene.getAABB(objectIDs);
  const eyeX = aabb[0] + 0.6 * (aabb[3] - aabb[0]);
  const eyeY = aabb[1] + 1 * (aabb[4] - aabb[1]);
  const eyeZ = aabb[2] + 2.5 * (aabb[5] - aabb[2]);
  camera.eye = [eyeX, eyeY, eyeZ];
  camera.look = [0., 1., 0.];
  camera.up = [0., 0., 1.];
  viewer.cameraFlight.flyTo(aabb);
}


document.body.addEventListener(
  "wheel",
  (event) => event.preventDefault(),
  {passive: false}
);


google.colab.kernel.comms.registerTarget("xeokitViz", async (comm, message) => {
  let ifcStr = message["data"]["ifcStr"];
  setContainerSize();
  setupModel(ifcStr);
  window.model.on("loaded", async () => await setupCamera());
});


reloadIfc();
