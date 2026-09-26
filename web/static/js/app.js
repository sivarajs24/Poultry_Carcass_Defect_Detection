/**
 * PoultryGuard — frontend for defect detection
 */

const API = "";

const CLASS_COLORS = [
  "#e74c3c", "#9b59b6", "#3498db", "#1abc9c", "#f39c12",
  "#e67e22", "#2ecc71", "#16a085", "#c0392b", "#7f8c8d", "#8e44ad",
];

const CLASS_NAMES = [
  "bile", "bruise", "dislocation", "feather", "fracture", "hematoma",
  "scratch", "skin-rash", "abnormal-carcass", "technical-failure", "fecal-contamination",
];

const state = {
  activeTab: "camera",
  conf: 0.35,
  iou: 0.45,
  cameraStream: null,
  cameraDetecting: false,
  cameraLoopId: null,
  lastFrameTime: 0,
  fps: 0,
  selectedImageFile: null,
  selectedVideoFile: null,
  modelReady: false,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function toast(message, type = "info") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  $("#toastContainer").appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

function getSettings() {
  return { conf: state.conf, iou: state.iou };
}

function initSliders() {
  const confSlider = $("#confSlider");
  const iouSlider = $("#iouSlider");

  confSlider.addEventListener("input", () => {
    state.conf = parseFloat(confSlider.value);
    $("#confValue").textContent = confSlider.value;
  });

  iouSlider.addEventListener("input", () => {
    state.iou = parseFloat(iouSlider.value);
    $("#iouValue").textContent = iouSlider.value;
  });
}

function initLegend() {
  const ul = $("#classLegend");
  CLASS_NAMES.forEach((name, i) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="class-swatch" style="background:${CLASS_COLORS[i]}"></span>${name}`;
    ul.appendChild(li);
  });
}

function initTabs() {
  const titles = {
    camera: ["Live Camera Detection", "Real-time inspection via webcam"],
    image: ["Image Upload", "Analyze still frames from the processing line"],
    video: ["Video Analysis", "Batch-process recorded inspection footage"],
    analytics: ["Analytics Dashboard", "Historical trends of detected defects"],
  };

  $$(".nav-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const id = tab.dataset.tab;
      state.activeTab = id;

      $$(".nav-tab").forEach((t) => {
        t.classList.toggle("active", t === tab);
        t.setAttribute("aria-selected", t === tab ? "true" : "false");
      });

      $$(".tab-panel").forEach((p) => p.classList.toggle("active", p.dataset.panel === id));

      const [title, sub] = titles[id];
      $("#panelTitle").textContent = title;
      $("#panelSubtitle").textContent = sub;
      
      if (id === "analytics") {
        loadAnalytics();
      }
    });
  });
}

async function checkHealth() {
  const dot = $("#statusDot");
  const text = $("#statusText");
  const pathEl = $("#modelPath");

  try {
    const res = await fetch(`${API}/api/health`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Backend unavailable");

    state.modelReady = data.status === "ready";
    dot.className = `status-dot ${data.status === "ready" ? "ready" : "error"}`;
    text.textContent = data.status === "ready" ? "Model loaded" : "Model error";
    pathEl.textContent = data.model?.path?.split(/[/\\]/).slice(-3).join("/") || "—";

    if (data.status === "ready") toast("Detection engine ready", "success");
  } catch (err) {
    dot.className = "status-dot error";
    text.textContent = "Offline";
    pathEl.textContent = err.message;
    toast("Cannot reach backend. Start run_server.py", "error");
  }
}

function updateMetrics(inferenceMs, defectCount) {
  $("#metricInference").textContent = inferenceMs != null ? `${Math.round(inferenceMs)} ms` : "—";
  $("#metricDefects").textContent = defectCount ?? 0;
  $("#metricFps").textContent = state.fps > 0 ? state.fps.toFixed(1) : "—";
}

function renderResults(detections, summary) {
  const summaryEl = $("#resultsSummary");
  const listEl = $("#detectionList");
  listEl.innerHTML = "";

  if (!detections?.length) {
    summaryEl.innerHTML = '<p class="muted">No defects detected in this frame.</p>';
    return;
  }

  const parts = Object.entries(summary?.by_class || {})
    .map(([k, v]) => `<strong>${k}</strong>: ${v}`)
    .join(" · ");

  summaryEl.innerHTML = `<p><strong>${summary.total}</strong> defect(s) — ${parts}</p>`;

  detections.forEach((d) => {
    const li = document.createElement("li");
    li.style.borderLeftColor = d.color || "#c9a227";
    li.innerHTML = `<span>${d.label}</span><span class="conf">${(d.confidence * 100).toFixed(1)}%</span>`;
    listEl.appendChild(li);
  });
}

/* ——— Camera ——— */

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    state.cameraStream = stream;
    const video = $("#cameraVideo");
    video.srcObject = stream;
    $("#cameraEmpty").classList.add("hidden");
    $("#stopCameraBtn").disabled = false;
    toast("Camera enabled", "success");
  } catch (err) {
    toast("Camera access denied: " + err.message, "error");
  }
}

function stopCamera() {
  stopCameraDetection();
  if (state.cameraStream) {
    state.cameraStream.getTracks().forEach((t) => t.stop());
    state.cameraStream = null;
  }
  $("#cameraVideo").srcObject = null;
  $("#cameraOutput").src = "";
  $("#cameraOutput").classList.add("hidden");
  $("#cameraOutputEmpty").classList.remove("hidden");
  $("#cameraEmpty").classList.remove("hidden");
  $("#stopCameraBtn").disabled = true;
  $("#toggleCameraDetect").textContent = "Start Live Detection";
}

function captureFrame() {
  const video = $("#cameraVideo");
  const canvas = $("#cameraCanvas");
  if (!video.videoWidth) return null;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0);
  return canvas.toDataURL("image/jpeg", 0.85);
}

async function sendFrame(imageDataUrl) {
  const res = await fetch(`${API}/api/detect/frame`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: imageDataUrl, ...getSettings() }),
  });
  return res.json();
}

async function cameraDetectionLoop() {
  if (!state.cameraDetecting) return;

  const frame = captureFrame();
  if (!frame) {
    state.cameraLoopId = requestAnimationFrame(cameraDetectionLoop);
    return;
  }

  const now = performance.now();
  if (state.lastFrameTime) {
    const delta = (now - state.lastFrameTime) / 1000;
    state.fps = 0.85 * state.fps + 0.15 * (1 / delta);
  }
  state.lastFrameTime = now;

  try {
    const data = await sendFrame(frame);
    if (data.success && data.image) {
      const out = $("#cameraOutput");
      out.src = data.image;
      out.classList.remove("hidden");
      $("#cameraOutputEmpty").classList.add("hidden");
      updateMetrics(data.inference_ms, data.summary?.total ?? 0);
      renderResults(data.detections, data.summary);
    }
  } catch {
    /* skip frame on network error */
  }

  if (state.cameraDetecting) {
    setTimeout(() => {
      state.cameraLoopId = requestAnimationFrame(cameraDetectionLoop);
    }, 80);
  }
}

function toggleCameraDetection() {
  if (!state.cameraStream) {
    toast("Enable the camera first", "error");
    return;
  }
  if (!state.modelReady) {
    toast("Model not ready yet", "error");
    return;
  }

  state.cameraDetecting = !state.cameraDetecting;
  const btn = $("#toggleCameraDetect");
  btn.textContent = state.cameraDetecting ? "Stop Live Detection" : "Start Live Detection";

  if (state.cameraDetecting) {
    state.lastFrameTime = 0;
    cameraDetectionLoop();
  }
}

function stopCameraDetection() {
  state.cameraDetecting = false;
  if (state.cameraLoopId) cancelAnimationFrame(state.cameraLoopId);
  $("#toggleCameraDetect").textContent = "Start Live Detection";
}

/* ——— Image ——— */

function setupDropZone(zoneId, inputId, browseId, onFile) {
  const zone = $(zoneId);
  const input = $(inputId);

  $(browseId).addEventListener("click", (e) => {
    e.stopPropagation();
    input.click();
  });

  zone.addEventListener("click", () => input.click());

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("dragover");
  });

  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));

  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  });

  input.addEventListener("change", () => {
    if (input.files[0]) onFile(input.files[0]);
  });
}

function loadImagePreview(file) {
  state.selectedImageFile = file;
  const url = URL.createObjectURL(file);
  $("#imageOriginal").src = url;
  $("#imageOutput").src = "";
  $("#imageResults").classList.remove("hidden");
  $("#runImageDetect").disabled = false;
  $("#clearImage").disabled = false;
  toast(`Loaded: ${file.name}`, "success");
}

async function runImageDetection() {
  if (!state.selectedImageFile) return;

  const btn = $("#runImageDetect");
  btn.disabled = true;
  btn.textContent = "Analyzing…";

  const form = new FormData();
  form.append("file", state.selectedImageFile);
  form.append("conf", state.conf);
  form.append("iou", state.iou);

  try {
    const res = await fetch(`${API}/api/detect/image`, { method: "POST", body: form });
    const data = await res.json();

    if (!data.success) throw new Error(data.error || "Detection failed");

    $("#imageOutput").src = data.image;
    updateMetrics(data.inference_ms, data.summary?.total ?? 0);
    renderResults(data.detections, data.summary);
    toast(`Found ${data.summary?.total ?? 0} defect(s)`, "success");
  } catch (err) {
    toast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyze Image";
  }
}

function clearImage() {
  state.selectedImageFile = null;
  $("#imageInput").value = "";
  $("#imageResults").classList.add("hidden");
  $("#runImageDetect").disabled = true;
  $("#clearImage").disabled = true;
}

/* ——— Video ——— */

function loadVideoPreview(file) {
  state.selectedVideoFile = file;
  $("#runVideoDetect").disabled = false;
  $("#clearVideo").disabled = false;
  $("#videoResults").classList.add("hidden");
  toast(`Video selected: ${file.name}`, "success");
}

async function runVideoDetection() {
  if (!state.selectedVideoFile) return;

  const btn = $("#runVideoDetect");
  btn.disabled = true;
  btn.textContent = "Processing…";

  const wrap = $("#videoProgressWrap");
  const bar = $("#videoProgressBar");
  wrap.classList.remove("hidden");
  bar.style.width = "0%";
  $("#videoProgressText").textContent = "Uploading and starting video processing…";

  const form = new FormData();
  form.append("file", state.selectedVideoFile);
  form.append("conf", state.conf);
  form.append("iou", state.iou);

  try {
    const res = await fetch(`${API}/api/detect/video`, { method: "POST", body: form });
    const data = await res.json();

    if (!data.success) throw new Error(data.error || "Video upload failed");

    const jobId = data.job_id;

    const pollInterval = setInterval(async () => {
      try {
        const statusRes = await fetch(`${API}/api/detect/video/status/${jobId}`);
        const statusData = await statusRes.json();

        if (statusData.status === "processing") {
            bar.style.width = `${Math.max(10, statusData.progress)}%`;
            $("#videoProgressText").textContent = `Processing: ${statusData.progress}%`;
        } else if (statusData.status === "done") {
            clearInterval(pollInterval);
            bar.style.width = "100%";
            $("#videoProgressText").textContent =
              `Done — ${statusData.stats.frames_processed} frames in ${statusData.stats.processing_sec}s`;
        
            const video = $("#videoOutput");
            video.src = statusData.video_url;
            $("#videoResults").classList.remove("hidden");
        
            updateMetrics(null, statusData.stats.total_detections);
            renderResults(
              Object.entries(statusData.stats.by_class || {}).map(([label, count]) => ({
                label,
                confidence: 1,
                color: "#c9a227",
              })),
              { total: statusData.stats.total_detections, by_class: statusData.stats.by_class }
            );
        
            toast("Video processing complete", "success");
            btn.disabled = false;
            btn.textContent = "Process Video";
        } else if (statusData.status === "error") {
            throw new Error(statusData.error || "Video processing failed");
        }
      } catch (err) {
        clearInterval(pollInterval);
        toast(err.message, "error");
        wrap.classList.add("hidden");
        btn.disabled = false;
        btn.textContent = "Process Video";
      }
    }, 1000);

  } catch (err) {
    toast(err.message, "error");
    wrap.classList.add("hidden");
    btn.disabled = false;
    btn.textContent = "Process Video";
  }
}

function clearVideo() {
  state.selectedVideoFile = null;
  $("#videoInput").value = "";
  $("#videoResults").classList.add("hidden");
  $("#videoProgressWrap").classList.add("hidden");
  $("#runVideoDetect").disabled = true;
  $("#clearVideo").disabled = true;
}

/* ——— Analytics ——— */

let chartInstance = null;

async function loadAnalytics() {
  try {
    const res = await fetch(`${API}/api/analytics`);
    const data = await res.json();
    
    if (data.error) throw new Error(data.error);

    const counts = data.class_counts || {};
    const labels = Object.keys(counts);
    const values = Object.values(counts);

    const ctx = document.getElementById('analyticsChart').getContext('2d');
    
    if (chartInstance) {
      chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Total Defects Detected',
          data: values,
          backgroundColor: CLASS_COLORS.slice(0, labels.length),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });

  } catch (err) {
    toast("Failed to load analytics: " + err.message, "error");
  }
}

/* ——— Init ——— */

function init() {
  initSliders();
  initLegend();
  initTabs();
  checkHealth();

  $("#startCameraBtn").addEventListener("click", startCamera);
  $("#stopCameraBtn").addEventListener("click", stopCamera);
  $("#toggleCameraDetect").addEventListener("click", toggleCameraDetection);

  $("#captureSnapshot").addEventListener("click", async () => {
    const frame = captureFrame();
    if (!frame) {
      toast("No camera frame available", "error");
      return;
    }
    try {
      const data = await sendFrame(frame);
      if (data.success) {
        $("#cameraOutput").src = data.image;
        $("#cameraOutput").classList.remove("hidden");
        $("#cameraOutputEmpty").classList.add("hidden");
        renderResults(data.detections, data.summary);
        toast("Snapshot analyzed", "success");
      }
    } catch (err) {
      toast(err.message, "error");
    }
  });

  setupDropZone("#imageDropZone", "#imageInput", "#imageBrowseBtn", loadImagePreview);
  setupDropZone("#videoDropZone", "#videoInput", "#videoBrowseBtn", loadVideoPreview);

  $("#runImageDetect").addEventListener("click", runImageDetection);
  $("#clearImage").addEventListener("click", clearImage);
  $("#runVideoDetect").addEventListener("click", runVideoDetection);
  $("#clearVideo").addEventListener("click", clearVideo);
  
  $("#refreshAnalyticsBtn").addEventListener("click", loadAnalytics);
}

document.addEventListener("DOMContentLoaded", init);
