# 穿越次元壁，也要拯救你

**DeepSeek 鲸鱼娘 · 4K 动态壁纸**

这是一个离线构建的 Wallpaper Engine 视频壁纸。默认成片为 3840 × 2160、60 fps、816 帧、13.6 秒静音循环。

![默认成片首帧](docs/preview.jpg)

## 安装和构建

准备 Python 3.12–3.14、Node.js 22 或更新版本和支持 OpenGL 3.3 的环境。Ubuntu 使用 EGL 离屏渲染。精简版 Ubuntu 还需要 `libegl1`、`libgl1-mesa-dri`，以及可创建带 pip 的虚拟环境的 `python3-venv`。Windows 使用系统 OpenGL 驱动。

在 `deepseek-save-you-across-dims-wp` 仓库目录执行。安装脚本默认走清华 PyPI 镜像和 npmmirror，切换官方源可用 Windows 的 `-Official` 或 Ubuntu 的 `--official`。

**Windows**

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe wallpaper.py build
```

**Ubuntu**

```bash
bash setup.sh
.venv/bin/python wallpaper.py build
```

第一次构建会烘焙遮罩、身体运动场、HUD 和粒子，并将产物缓存到 `build/cache/`。构建完成后，将 `build/wallpaper/` 作为视频壁纸工程导入 Wallpaper Engine。目录中包含 `wallpaper.mp4`、`project.json` 和由首帧生成的 `preview.jpg`。自动编码模式会探测 NVENC 可用性，并在需要时选用 libx264。

## 配置

编辑 [config.toml](config.toml) 后重新构建。可用 `wallpaper.py --config my-wallpaper.toml build --output build/my-wallpaper` 同时保留多个版本。

| 配置 | 作用 |
| --- | --- |
| `dof.strength` | 景深强度倍率。`0.0` 去掉虚化，`1.0` 为默认强度。 |
| `dof.focus_pull` | 保留跟随动作的焦点转移，设为 `false` 时固定在开场焦点。 |
| `speed.rate` | 播放速度倍率。时长约为 `13.6 / rate` 秒，取整到输出帧。 |
| `glitch.enabled` | 在两处故障时间窗启用信号撕裂，默认关闭。 |
| `glitch.style` | `scanline` 扫描线撕裂、`jitter` 抖动错位或 `displacement` 冲击位移。 |
| `hud.panels` | 修改四块浮窗的标题、侧标、日志类型和词条。Warning 对应 `id = "warning"`。 |
| `output` | 设置导出尺寸、帧率和编码器。渲染内部使用统一的 4K 工作分辨率。 |

Ubuntu 默认使用参考 HUD 贴图。修改过的面板才用本地字体重新绘制，字体回退时字形可能与默认稿不同。已有 Arial 和 Consolas 时，将 `WHALE_FONT_DIR` 设为含 `arialbd.ttf`、`consola.ttf`、`consolab.ttf` 的目录。WSL 可指向已有的 `/mnt/c/Windows/Fonts`。WSL 的 llvmpipe 软件渲染耗时会高于 GPU 渲染。

## 渲染链路

素材烘焙入口是 `wallpaper.py bake`。Python 烘焙程序从底图、原画眼部、水面层和追踪数据生成纹理和运动场。Node 烘焙程序生成 HUD 和粒子。渲染以水层、场景合成、收尾着色三个 pass 输出 RGB，再交给 FFmpeg 编码。源素材位于 `assets/`。

## 制作记录

从封面重绘到分层动态壁纸的尝试和取舍，见 [2026 年 11 月 22 日制作记录](docs/production-notes.md)。

## 署名和许可

原画 **dy翩翩**，原视频和原壁纸 **偶鲸鲸**。代码使用 MIT 许可证，素材使用范围见 [NOTICE.md](NOTICE.md)。

## English

An offline, configurable build of the DeepSeek live wallpaper **I'll Cross Dimensions to Save You** for Wallpaper Engine. The default export is a silent 4K, 60 fps loop. Run the setup script for your platform, then run `wallpaper.py build` with the virtual environment's Python. Adjust depth of field, speed, signal glitch, and HUD copy in `config.toml`.
