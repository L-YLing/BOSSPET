# 💼 老板专属智能桌宠 (Boss Desktop Pet)

一个基于 PyQt5 编写的互动式 Windows 桌面宠物。它能根据您的工作状态做出相应的动作，并支持鼠标悬停、拖拽交互以及“抽打老板”隐藏模式！

## ✨ 特色功能

- **工作状态感知**：能够自动监控后台日志，在收到特定事件（例如“递交文件”）时播放动画，并弹出气泡提示。支持通过 config.json 自定义监控路径。
- **互动动画**：
  - **待机状态**：生动自然的待机循环动作。
  - **递交文件**：任务完成时向您递交文件的特殊动画。
  - **工作打字**：键盘敲击工作状态。
  - **鼠标交互**：鼠标悬停唤醒，随意拖拽移动位置。
  - **解压抽打模式**：开启“抽打”模式，鼠标靠近时触发专属连贯受击动作和求饶对话。
- **无感透明背景**：支持无边框透明窗口，完美融入桌面环境。

## 🚀 快速运行 (针对普通用户)

您可以直接下载打包好的 [BossPet.exe](dist/BossPet.exe) (如果在 Release 中提供)，双击即可运行，无需配置任何环境！对于解压抽打模式，请确保同时下载配套的 MouseWhip.exe。

## 🛠️ 本地开发 (针对开发者)

1. 克隆本项目：
   `ash
   git clone https://github.com/您的用户名/boss_pet.git
   cd boss_pet
   `
2. 安装依赖：
   `bash
   pip install -r requirements.txt
   `
3. 运行项目：
   `bash
   python main.py
   `

## 📦 如何打包为 exe

1. 确保安装了 PyInstaller：
   `bash
   pip install pyinstaller
   `
2. 执行打包命令：
   `bash
   pyinstaller --clean --noconsole --onefile --noupx --name BossPet --add-data "assets;assets" main.py
   `
   打包完成后，在 dist 目录下会生成独立的可执行文件。

## 🎨 自定义动画
所有的图片资源均存放在 ssets 目录下。您可以随时替换为您自己的序列帧图集或散图文件夹，然后在 main.py 顶部的 SPRITE_CONFIG 中配置相应的路径、行列数以及帧率即可实现个性化定制！

## 🪄 AI 一键定制玩法（支持导入小红书 RedSkill）

本项目不仅可以作为常规桌宠使用，还支持通过一段专属提示词，交由大语言模型（如小红书 RedSkill、豆包电脑版、Workbuddy、Codex 等）实现“**形象克隆**”与“**应用联动修改**”的一键定制。

如果你希望改变桌宠的形象（提供真人照片生成配套三视图与动效），或者希望修改桌宠联动唤醒的 Agent 软件，可以直接将本仓库下载，并将 
edskill_prompt.md 中的提示词和您的照片发送给您的开发 Agent！

[👉 点击查看完整定制提示词 (redskill_prompt.md)](redskill_prompt.md)
