# ECNUchat v2 Windows 桌面版

解压整个 `ECNUchat-v2-Windows.zip`，在 `ECNUchat-v2` 文件夹中双击 `ECNUchat-v2.exe`。首次启动需要本机已有 Microsoft Edge 或 Google Chrome。压缩包已包含 Java 运行时、客户端和加密依赖。请保留 EXE 旁边的 `app` 和 `runtime` 文件夹。

## 本机聊天

在解压后的文件夹里打开 PowerShell，执行以下命令启动随包提供的中继。需要 Python 3.10 或更新版本，使用标准库即可。

```powershell
py -3 .\relay.py --host 127.0.0.1 --port 8765 --db .\relay.db
```

保持中继窗口打开，在客户端选择 Relay 模式并注册。测试第二个身份时可使用页面的第二个身份窗口。两个身份注册后交换邀请并添加好友，即可发送加密消息。SQLite 文件保存中继的设备目录和待投递密文。在无 Python 的电脑上，仍可打开桌面应用并使用本地演示模式，或连接已配置的兼容中继。演示消息采用公开的演示密钥派生。

## 配置和数据位置

- 桌面版固定从 `http://127.0.0.1:38765/` 提供打包的页面。宿主只绑定 IPv4 回环地址，读取内置资源；关闭专用浏览器窗口后宿主退出。端口已被占用时启动器会提示，换端口会产生不同的浏览器存储来源。
- Edge 优先，找不到时尝试 Chrome。浏览器使用独立配置目录 `%LOCALAPPDATA%\ECNUchat\v2\EdgeProfile`。关闭并重新启动或将解压目录移到其他位置，使用同一浏览器、页面端口和配置目录即可继续使用原有身份。本机的身份私钥和历史记录由 PWA 存在浏览器 localStorage 中。
- 中继地址依次取自环境变量 `ECNU_RELAY_URL`、`ECNU_DESKTOP_CONFIG` 指向的 UTF-8 JSON 文件中的 `relayUrl`、页面保存的中继地址和默认值 `http://127.0.0.1:8765`。显式设置优先于页面输入，生效于下次启动。远程 HTTP 地址会被拒绝，非回环地址要求 HTTPS。
- 如需自定义，可设置 `ECNU_DESKTOP_PROFILE`（独立浏览器数据目录）、`ECNU_DESKTOP_PORT`（本机页面端口）和 `ECNU_DESKTOP_BROWSER`（Edge 或 Chrome 可执行文件的绝对路径）。

下例只修改当前 PowerShell 进程启动的客户端。

```powershell
$env:ECNU_RELAY_URL = 'http://127.0.0.1:9000'
.\ECNUchat-v2.exe
```

## 离线构建和验证

在仓库根目录下，使用已安装的 Python 与 64 位 JDK 21 或更新版本。将 `javac` 和 `jpackage` 放入 PATH。

```powershell
py -3 v2/desktop/build_windows.py
py -3 v2/desktop/test_windows_package.py
```

构建产生 `dist/ECNUchat-v2-Windows.zip`。测试另外调用本机 Node.js 来验证浏览器配置逻辑，使用临时文件夹和独立端口。`--serve-only` 可供自动化或调试使用，只启动本机静态页面服务；终止进程即可关闭。

`Desktop.java` 使用 JDK 的 HTTP 服务，`build_windows.py` 将 `v2/pwa` 整个目录嵌入桌面 JAR，并在页面脚本运行前加载中继配置。此版本的 Windows 启动器由 `jpackage` 生成。目录中的 Electron 脚手架保留供开发参考。
