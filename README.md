# SignX-Demo

## 项目简介

SignX-Demo 是一款面向听障用户的桌面式手语语音翻译终端 SignX 的技术演示项目。它通过电脑摄像头模拟 SignX 的视觉感知模块，录制用户的手语动作，并通过本地后端返回识别结果，最后使用电脑扬声器进行语音播报。

本项目主要用于展示 SignX 的核心交互闭环：

摄像头感知 → 手语动作录制 → 后端分析 → 语义结果 → 语音播报

## SignX 是什么

SignX 是一款面向听障用户的桌面式手语语音翻译终端。它希望将听障用户的手语表达转化为自然语音，让不懂手语的人也能及时理解并回应，从而帮助听障用户更自然地参与会议、小组讨论、课堂互动、医疗问诊和公共交流场景。

## 当前 Demo 功能

- 摄像头实时预览
- 3 秒倒计时
- 5 秒视频录制
- 程序模式
- 演示模式
- 会议 / 小组讨论语句库
- 自动语音播报
- 个性化声音调节
- 音量、语速、音高调节
- 男声 / 女声 / 系统声音选择
- Windows 一键启动

## 两种模式说明

### 程序模式

程序模式用于展示真实技术链路。

当前版本可以作为后续接入真实手语识别算法、AI API 或同学识别模型的接口入口。

流程：

摄像头录制手语视频 → 上传后端 → 返回识别结果 → 前端语音播报

### 演示模式

演示模式用于现场汇报展示。

它不会真的分析手语内容，而是从预设的会议 / 小组讨论语句库中随机返回一句话，保证课堂展示稳定流畅。

流程：

任意手语动作 → 录制视频 → 随机返回会议语句 → 语音播报

## 个性化声音功能

用户可以在网页里调整 SignX 的播报声音，包括：

- 音量
- 语速
- 音高
- 声音类型
- 男声优先
- 女声优先
- 系统声音选择
- 试听当前声音

这体现了 SignX 的设计理念：听障用户不只是被机器翻译，也可以选择自己希望被听见的声音状态。

## 技术架构

前端：

- HTML
- CSS
- JavaScript
- MediaRecorder
- speechSynthesis

后端：

- Python
- FastAPI
- Uvicorn

运行方式：

- 本地运行
- 浏览器访问 http://127.0.0.1:8000

## 项目结构

```text
SignX-Demo/
├─ backend/
│  ├─ main.py
│  ├─ config.py
│  ├─ demo_sentences.py
│  ├─ sign_phrases.py
│  ├─ ai_clients/
│  │  ├─ __init__.py
│  │  ├─ base.py
│  │  ├─ mock_client.py
│  │  └─ qwen_client.py
│  └─ temp/
├─ frontend/
│  ├─ index.html
│  ├─ style.css
│  └─ app.js
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ run.bat
├─ setup.bat
├─ start.bat
└─ README.md
```

## Windows 一键启动

1. 下载或 clone 项目。
2. 进入项目文件夹。
3. 双击 `run.bat`。

或者在 PowerShell 中运行：

```powershell
.\run.bat
```

浏览器会自动打开：

```text
http://127.0.0.1:8000
```

注意：不要把中文句号写进网址里。

## 手动启动方式

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

然后打开：

```text
http://127.0.0.1:8000
```

## 使用方法

1. 打开网页。
2. 允许浏览器访问摄像头。
3. 选择程序模式或演示模式。
4. 点击开始识别。
5. 等待 3 秒倒计时。
6. 做 5 秒手语动作。
7. 等待系统返回结果。
8. 电脑会自动播报识别内容。
9. 可以在声音设置中调整音量、语速、音高和声音类型。

## 程序模式真实 API 配置

程序模式支持 `mock` 和 `qwen` 两种 provider。复制 `.env.example` 为 `.env` 后可以修改配置。

### mock 测试方式

```env
AI_PROVIDER=mock
DASHSCOPE_API_KEY=
QWEN_MODEL=qwen-vl-plus
```

mock 模式不需要 API Key，适合先跑通流程。

### 通义千问 / 阿里云百炼方式

```env
AI_PROVIDER=qwen
DASHSCOPE_API_KEY=your_dashscope_api_key_here
QWEN_MODEL=qwen-vl-plus
```

如果 `qwen-vl-plus` 在账号中不可用，请根据阿里云百炼控制台支持的视频理解模型名称修改 `QWEN_MODEL`。

当前程序模式是基于多模态大模型的视频理解 demo，不是专业中国手语识别模型。为了保证课堂展示稳定，目前采用限定语义库识别。未来可以接入专门训练的连续手语识别模型。


## Keypoint 程序模式：真实手语模板识别

当前项目提供一个基础的真实识别原型。它不是完整连续手语翻译，而是限定词库模板匹配识别。

使用步骤：

1. 在 `.env` 中设置：

```env
AI_PROVIDER=keypoint
```

2. 双击 `run.bat` 启动项目。
3. 浏览器打开：

```text
http://127.0.0.1:8000
```

4. 进入程序模式。
5. 在“模板录入 / Training”区域选择一个手语标签。
6. 点击“录入当前手语模板”。
7. 倒计时结束后，对着摄像头做对应手语动作 5 秒。
8. 每个手语建议录入 2 到 3 条模板。
9. 录入完成后，点击程序模式里的“开始识别”。
10. 系统会将当前动作与模板进行匹配，并播报最接近的结果。

限制说明：

- 当前是限定词库识别，不是完整连续手语翻译。
- 识别效果依赖摄像头画面质量。
- 光线太暗会影响识别。
- 手部不要离摄像头太远。
- 模板最好由同一个用户录入。
- 模板越多，识别越稳定。
- 后续可以升级为 LSTM、Transformer 或更专业的连续手语识别模型。

## 注意事项

- 如果摄像头无法打开，请检查浏览器权限。
- 如果网页打不开，请确认 `run.bat` 窗口是否正常运行。
- 如果提示 `127.0.0.1` 拒绝连接，说明后端服务没有启动。
- 如果没有男声或女声选项，是因为浏览器只能使用当前电脑系统支持的声音。
- 演示模式不是真实识别，而是现场展示用的稳定模式。
- 程序模式后续可以继续接入真实手语识别模型或外部 API。
- `.env`、`venv/`、`backend/temp/` 和临时视频文件不应上传到 GitHub。

## 后续计划

- 接入真实手语识别模型
- 接入通义千问 / Gemini 等多模态 API
- 支持更长时间的连续手语识别
- 增加用户档案
- 增加个性化手语习惯参数
- 增加本地化隐私设置
- 支持更多公共交流场景

## License

This project is for academic and design demo purposes.

