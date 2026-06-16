const preview = document.getElementById("preview");
const startButton = document.getElementById("startButton");
const retryButton = document.getElementById("retryButton");
const statusText = document.getElementById("statusText");
const cornerStatus = document.getElementById("cornerStatus");
const hintText = document.getElementById("hintText");
const errorText = document.getElementById("errorText");
const countdownText = document.getElementById("countdownText");
const meaningText = document.getElementById("meaningText");
const confidenceText = document.getElementById("confidenceText");
const spokenText = document.getElementById("spokenText");
const currentModeText = document.getElementById("currentModeText");
const stateDot = document.getElementById("stateDot");
const cameraBadge = document.getElementById("cameraBadge");
const modeBadge = document.getElementById("modeBadge");
const modeDescription = document.getElementById("modeDescription");
const analyzeStepText = document.getElementById("analyzeStepText");
const progressBar = document.getElementById("progressBar");
const flowSteps = Array.from(document.querySelectorAll("[data-step]"));
const modeButtons = Array.from(document.querySelectorAll("[data-mode]"));
const volumeSlider = document.getElementById("volumeSlider");
const rateSlider = document.getElementById("rateSlider");
const pitchSlider = document.getElementById("pitchSlider");
const volumeValue = document.getElementById("volumeValue");
const rateValue = document.getElementById("rateValue");
const pitchValue = document.getElementById("pitchValue");
const voiceTypeButtons = Array.from(document.querySelectorAll("[data-voice-type]"));
const voiceSelect = document.getElementById("voiceSelect");
const voiceNotice = document.getElementById("voiceNotice");
const presetButtons = Array.from(document.querySelectorAll("[data-voice-preset]"));
const testVoiceButton = document.getElementById("testVoiceButton");

let currentMode = "program";
let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let busy = false;
let systemVoices = [];
let filteredVoices = [];

const modes = {
  program: {
    label: "程序模式",
    badge: "AI Video Analysis",
    endpoint: "/api/analyze-sign",
    analyzeStep: "AI 分析",
    description: "程序模式：AI 视频分析。录制手语视频并进入真实多模态 AI 分析流程，适合后续接入和调试真实识别 API。",
    status: {
      preparing: "摄像头准备中",
      idle: "待机中",
      countdown: "倒计时",
      recording: "录制中",
      analyzing: "AI 分析中",
      speaking: "播报中",
      done: "识别完成",
      error: "出错提示",
    },
    analyzingHint: "AI 分析中，请稍候...",
    doneHint: "识别完成，可点击重新识别再次采集。",
  },
  demo: {
    label: "演示模式",
    badge: "Demo Meeting",
    endpoint: "/api/demo-meeting",
    analyzeStep: "演示语句",
    description: "演示模式：用于现场展示，系统会从会议场景语句中随机播报一条，保证演示稳定流畅。",
    status: {
      preparing: "摄像头准备中",
      idle: "待机中",
      countdown: "倒计时",
      recording: "录制中",
      analyzing: "生成演示语句中",
      speaking: "播报中",
      done: "演示完成",
      error: "出错提示",
    },
    analyzingHint: "生成演示语句中，请稍候...",
    doneHint: "演示完成，可点击重新识别再次展示。",
  },
};

const activeSteps = {
  preparing: ["capture"],
  idle: ["capture"],
  countdown: ["capture"],
  recording: ["capture", "record"],
  analyzing: ["capture", "record", "analyze"],
  speaking: ["capture", "record", "analyze", "speak"],
  done: ["capture", "record", "analyze", "speak"],
  error: [],
};

const voiceSettings = {
  volume: readNumberSetting("voiceVolume", 1, 0, 1),
  rate: readNumberSetting("voiceRate", 1, 0.6, 1.6),
  pitch: readNumberSetting("voicePitch", 1, 0.5, 2),
  voiceType: readStringSetting("voiceType", "all"),
  selectedVoiceName: readStringSetting("selectedVoiceName", ""),
};

const femaleKeywords = [
  "female",
  "woman",
  "xiaoxiao",
  "xiaoyi",
  "huihui",
  "yaoyao",
  "tingting",
  "hanhan",
  "meijia",
  "microsoft xiaoxiao",
];

const maleKeywords = [
  "male",
  "man",
  "yunxi",
  "yunyang",
  "kangkang",
  "zhiwei",
  "microsoft yunxi",
  "microsoft kangkang",
];

function readNumberSetting(key, fallback, min, max) {
  const value = Number(window.localStorage.getItem(key));
  if (!Number.isFinite(value)) {
    return fallback;
  }
  return Math.min(Math.max(value, min), max);
}

function readStringSetting(key, fallback) {
  return window.localStorage.getItem(key) || fallback;
}

function saveVoiceSettings() {
  window.localStorage.setItem("voiceVolume", String(voiceSettings.volume));
  window.localStorage.setItem("voiceRate", String(voiceSettings.rate));
  window.localStorage.setItem("voicePitch", String(voiceSettings.pitch));
  window.localStorage.setItem("voiceType", voiceSettings.voiceType);
  window.localStorage.setItem("selectedVoiceName", voiceSettings.selectedVoiceName);
}

function getMode() {
  return modes[currentMode];
}

function friendlyError(message) {
  if (message.includes("DASHSCOPE_API_KEY is missing")) {
    return "API Key 未配置，请在 .env 中填写 DASHSCOPE_API_KEY，或切换 AI_PROVIDER=mock。";
  }
  if (message.includes("dashscope package is not installed")) {
    return "DashScope 依赖未安装，请先运行 setup.bat。";
  }
  return message;
}

function setStatus(state, detail = "", displayText = "") {
  const mode = getMode();
  const label = displayText || mode.status[state] || state;
  statusText.textContent = label;
  cornerStatus.textContent = label;
  hintText.textContent = detail || label;
  stateDot.classList.toggle("active", ["recording", "analyzing", "speaking"].includes(state));
  stateDot.classList.toggle("error", state === "error");
  document.body.classList.toggle("is-recording", state === "recording");
  updateFlow(state);
}

function updateFlow(state) {
  const enabledSteps = activeSteps[state] || [];
  flowSteps.forEach((step) => {
    step.classList.toggle("active", enabledSteps.includes(step.dataset.step));
  });
}

function setMode(modeName, shouldReset = true) {
  if (busy || !modes[modeName]) {
    return;
  }

  currentMode = modeName;
  const mode = getMode();

  modeButtons.forEach((button) => {
    const active = button.dataset.mode === currentMode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  currentModeText.textContent = mode.label;
  modeBadge.textContent = mode.badge;
  modeDescription.textContent = mode.description;
  analyzeStepText.textContent = mode.analyzeStep;

  if (shouldReset) {
    resetResult(false);
  }

  if (mediaStream) {
    setStatus("idle", `${mode.label}已就绪，可以开始识别。`);
  }
}

function setControlsDisabled(disabled) {
  startButton.disabled = disabled || !mediaStream;
  retryButton.disabled = disabled || !mediaStream;
  modeButtons.forEach((button) => {
    button.disabled = disabled;
  });
}

function setError(message) {
  const displayMessage = friendlyError(message);
  errorText.textContent = displayMessage;
  errorText.hidden = false;
  setStatus("error", displayMessage);
}

function clearError() {
  errorText.textContent = "";
  errorText.hidden = true;
}

function resetResult(clearMode = false) {
  if (clearMode) {
    currentModeText.textContent = getMode().label;
  }
  meaningText.textContent = "--";
  confidenceText.textContent = "--";
  spokenText.textContent = "--";
  progressBar.style.width = "0%";
  countdownText.hidden = true;
  clearError();
}

function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function getSupportedMimeType() {
  const types = [
    "video/webm;codecs=vp9",
    "video/webm;codecs=vp8",
    "video/webm",
  ];

  return types.find((type) => window.MediaRecorder && MediaRecorder.isTypeSupported(type)) || "";
}

async function initCamera() {
  setStatus("preparing", "正在请求摄像头权限...");

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setError("当前浏览器不支持摄像头访问，请换用新版 Chrome、Edge 或 Firefox。");
    cameraBadge.textContent = "Camera Error";
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: "user",
      },
      audio: false,
    });
    preview.srcObject = mediaStream;
    document.body.classList.add("camera-ready");
    cameraBadge.textContent = "Camera Ready";
    setControlsDisabled(false);
    setStatus("idle", "摄像头已就绪，可以开始识别。");
  } catch (error) {
    console.error(error);
    cameraBadge.textContent = "Camera Error";
    setError("无法访问摄像头，请检查浏览器权限或确认摄像头未被其他程序占用。");
  }
}

async function runCountdown() {
  countdownText.hidden = false;
  progressBar.style.width = "0%";

  for (let count = 3; count > 0; count -= 1) {
    countdownText.textContent = String(count);
    setStatus("countdown", "请把手势放在摄像头中央。", `倒计时 ${count}`);
    await wait(1000);
  }

  countdownText.hidden = true;
}

function recordVideo() {
  return new Promise((resolve, reject) => {
    recordedChunks = [];
    const mimeType = getSupportedMimeType();
    const options = mimeType ? { mimeType } : undefined;

    try {
      mediaRecorder = new MediaRecorder(mediaStream, options);
    } catch (error) {
      reject(error);
      return;
    }

    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    };

    mediaRecorder.onerror = () => reject(mediaRecorder.error || new Error("录制失败"));
    mediaRecorder.onstop = () => {
      progressBar.style.width = "100%";
      resolve(new Blob(recordedChunks, { type: mimeType || "video/webm" }));
    };

    let remaining = 5;
    setStatus("recording", "录制中，请保持手势清晰。剩余 5 秒。");
    progressBar.style.width = "0%";
    mediaRecorder.start();

    const intervalId = window.setInterval(() => {
      remaining -= 1;
      const elapsed = 5 - remaining;
      progressBar.style.width = `${Math.min((elapsed / 5) * 100, 100)}%`;
      if (remaining > 0) {
        setStatus("recording", `录制中，请保持手势清晰。剩余 ${remaining} 秒。`);
      }
    }, 1000);

    window.setTimeout(() => {
      window.clearInterval(intervalId);
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
      }
    }, 5000);
  });
}

async function uploadVideo(videoBlob) {
  const mode = getMode();
  setStatus("analyzing", mode.analyzingHint);

  const formData = new FormData();
  formData.append("file", videoBlob, "signx-recording.webm");

  const response = await fetch(mode.endpoint, {
    method: "POST",
    body: formData,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `${mode.endpoint} 返回异常`);
  }

  if (data.error) {
    throw new Error(data.error);
  }

  return data;
}

function renderResult(result) {
  currentModeText.textContent = getMode().label;
  meaningText.textContent = result.meaning || "--";
  confidenceText.textContent = typeof result.confidence === "number"
    ? `${Math.round(result.confidence * 100)}%`
    : "--";
  spokenText.textContent = result.spoken_text || "--";
}

function isChineseVoice(voice) {
  const lang = (voice.lang || "").toLowerCase();
  const name = (voice.name || "").toLowerCase();
  return lang.includes("zh") || name.includes("chinese") || name.includes("mandarin");
}

function nameMatches(voice, keywords) {
  const name = (voice.name || "").toLowerCase();
  return keywords.some((keyword) => name.includes(keyword.toLowerCase()));
}

function filterVoicesByType(type) {
  const voices = systemVoices.slice();
  if (type === "chinese") {
    const chineseVoices = voices.filter(isChineseVoice);
    if (chineseVoices.length) {
      voiceNotice.textContent = "已优先显示当前系统中的中文声音。";
      return chineseVoices;
    }
    voiceNotice.textContent = "当前系统没有检测到中文声音，请从全部系统声音中选择。";
    return voices;
  }

  if (type === "female") {
    const femaleVoices = voices.filter((voice) => nameMatches(voice, femaleKeywords));
    if (femaleVoices.length) {
      voiceNotice.textContent = "已优先显示检测到的女声。";
      return femaleVoices;
    }
    const chineseVoices = voices.filter(isChineseVoice);
    voiceNotice.textContent = "当前系统没有检测到明显的女声，请从系统声音列表中选择。";
    return chineseVoices.length ? chineseVoices : voices;
  }

  if (type === "male") {
    const maleVoices = voices.filter((voice) => nameMatches(voice, maleKeywords));
    if (maleVoices.length) {
      voiceNotice.textContent = "已优先显示检测到的男声。";
      return maleVoices;
    }
    const chineseVoices = voices.filter(isChineseVoice);
    voiceNotice.textContent = "当前系统没有检测到明显的男声，请从系统声音列表中选择。";
    return chineseVoices.length ? chineseVoices : voices;
  }

  voiceNotice.textContent = "不同电脑和浏览器支持的系统声音不同，男声 / 女声选项会根据当前设备可用声音自动匹配。";
  return voices;
}

function chooseVoice(voices) {
  if (!voices.length) {
    return null;
  }

  const savedVoice = voices.find((voice) => voice.name === voiceSettings.selectedVoiceName);
  if (savedVoice) {
    return savedVoice;
  }

  const chineseVoice = voices.find(isChineseVoice);
  return chineseVoice || voices[0];
}

function renderVoiceOptions() {
  if (!window.speechSynthesis) {
    voiceSelect.innerHTML = "<option>当前浏览器不支持系统语音</option>";
    voiceSelect.disabled = true;
    voiceNotice.textContent = "当前浏览器不支持 speechSynthesis，无法使用个性化声音。";
    return;
  }

  filteredVoices = filterVoicesByType(voiceSettings.voiceType);
  voiceSelect.innerHTML = "";

  if (!filteredVoices.length) {
    const option = document.createElement("option");
    option.textContent = "未检测到系统声音";
    option.value = "";
    voiceSelect.appendChild(option);
    voiceSelect.disabled = true;
    voiceSettings.selectedVoiceName = "";
    saveVoiceSettings();
    return;
  }

  voiceSelect.disabled = false;
  filteredVoices.forEach((voice) => {
    const option = document.createElement("option");
    option.value = voice.name;
    option.textContent = `${voice.name} - ${voice.lang || "未知语言"}`;
    voiceSelect.appendChild(option);
  });

  const selectedVoice = chooseVoice(filteredVoices);
  voiceSettings.selectedVoiceName = selectedVoice ? selectedVoice.name : "";
  voiceSelect.value = voiceSettings.selectedVoiceName;
  saveVoiceSettings();
}

function getSelectedVoice() {
  return systemVoices.find((voice) => voice.name === voiceSettings.selectedVoiceName) || null;
}

function updateVoiceLabels() {
  volumeValue.textContent = `音量：${Math.round(voiceSettings.volume * 100)}%`;
  rateValue.textContent = `语速：${voiceSettings.rate.toFixed(1)}x`;
  pitchValue.textContent = `音高：${voiceSettings.pitch.toFixed(1)}`;
}

function syncVoiceControls() {
  volumeSlider.value = String(voiceSettings.volume);
  rateSlider.value = String(voiceSettings.rate);
  pitchSlider.value = String(voiceSettings.pitch);
  voiceTypeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.voiceType === voiceSettings.voiceType);
  });
  updateVoiceLabels();
}

function loadSystemVoices() {
  if (!window.speechSynthesis) {
    renderVoiceOptions();
    return;
  }
  systemVoices = window.speechSynthesis.getVoices();
  renderVoiceOptions();
}

function applyVoicePreset(presetName) {
  const presets = {
    female: { rate: 0.9, pitch: 1.25, volume: 0.9, voiceType: "female" },
    neutral: { rate: 1.0, pitch: 1.0, volume: 1.0, voiceType: "chinese" },
    male: { rate: 0.95, pitch: 0.75, volume: 1.0, voiceType: "male" },
  };
  const preset = presets[presetName];
  if (!preset) {
    return;
  }

  voiceSettings.rate = preset.rate;
  voiceSettings.pitch = preset.pitch;
  voiceSettings.volume = preset.volume;
  voiceSettings.voiceType = preset.voiceType;
  syncVoiceControls();
  renderVoiceOptions();
  saveVoiceSettings();
}

function initVoiceSettings() {
  syncVoiceControls();
  loadSystemVoices();

  if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = loadSystemVoices;
  }

  volumeSlider.addEventListener("input", () => {
    voiceSettings.volume = Number(volumeSlider.value);
    updateVoiceLabels();
    saveVoiceSettings();
  });

  rateSlider.addEventListener("input", () => {
    voiceSettings.rate = Number(rateSlider.value);
    updateVoiceLabels();
    saveVoiceSettings();
  });

  pitchSlider.addEventListener("input", () => {
    voiceSettings.pitch = Number(pitchSlider.value);
    updateVoiceLabels();
    saveVoiceSettings();
  });

  voiceTypeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      voiceSettings.voiceType = button.dataset.voiceType;
      syncVoiceControls();
      renderVoiceOptions();
      saveVoiceSettings();
    });
  });

  voiceSelect.addEventListener("change", () => {
    voiceSettings.selectedVoiceName = voiceSelect.value;
    saveVoiceSettings();
  });

  presetButtons.forEach((button) => {
    button.addEventListener("click", () => applyVoicePreset(button.dataset.voicePreset));
  });

  testVoiceButton.addEventListener("click", async () => {
    if (busy) {
      return;
    }
    await speakText("这是 SignX 的个性化语音播报效果。");
    if (!busy) {
      setStatus(mediaStream ? "idle" : "preparing", mediaStream ? "试听完成，可以开始识别。" : "试听完成，正在等待摄像头。")
    }
  });
}

function speakText(text) {
  return new Promise((resolve) => {
    if (!window.speechSynthesis || !text) {
      resolve();
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    utterance.volume = voiceSettings.volume;
    utterance.rate = voiceSettings.rate;
    utterance.pitch = voiceSettings.pitch;
    const selectedVoice = getSelectedVoice();
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    utterance.onend = resolve;
    utterance.onerror = resolve;
    setStatus("speaking", "正在播报识别结果。");
    window.speechSynthesis.speak(utterance);
  });
}

async function startRecognition() {
  if (busy || !mediaStream) {
    return;
  }

  busy = true;
  setControlsDisabled(true);
  resetResult(true);

  try {
    await runCountdown();
    const videoBlob = await recordVideo();
    const result = await uploadVideo(videoBlob);
    renderResult(result);
    await speakText(result.spoken_text);
    setStatus("done", getMode().doneHint);
  } catch (error) {
    console.error(error);
    setError(error.message || "识别流程出错，请确认后端服务正常运行后重试。");
  } finally {
    busy = false;
    setControlsDisabled(false);
    document.body.classList.remove("is-recording");
  }
}

function retryRecognition() {
  if (busy) {
    return;
  }
  window.speechSynthesis?.cancel();
  resetResult(true);
  if (mediaStream) {
    startRecognition();
  }
}

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});
startButton.addEventListener("click", startRecognition);
retryButton.addEventListener("click", retryRecognition);
setMode("program", false);
initVoiceSettings();
initCamera();
