# PopTag 本地版启动与更新器

游戏启动器：固定从 Fish0731/PopTag 的正式 Release 读取更新清单。

## 玩家怎么用

首次仍下载一个完整游戏包。把 `PopTagLauncher.exe` 放在游戏根目录，和 `client`、`server`、`runtime` 文件夹并列，双击它或创建指向它的桌面快捷方式。

- “更新并启动”：检查正式 Release，下载变化组件，校验、备份、替换，再启动本地服务端及游戏。
- “离线启动”：使用当前文件，不联网检查。
- “关闭本地游戏”：请求本目录客户端正常退出，再停止经路径和命令行确认归属本目录的服务端；不强杀无响应客户端。
- “回滚上次更新”：恢复更新前的程序文件和版本索引，账号存档不会被更新或回滚。

更新源固定为 `Fish0731/PopTag` 的 GitHub 正式 Releases。仓库尚未发布时会显示提示，可继续离线启动已有完整版本。直接点击 `client/CA.exe` 会绕过更新器。

运行环境：Windows 10/11，系统 .NET Framework 4.8。不需要玩家安装 Python、Maven 或额外的 .NET 桌面运行时。完整游戏包仍需自带 Java。

## 作者怎么发更新

1. 完成修改和游戏内测试，准备一份干净的完整发布目录。不要直接从仍被修改的开发目录发布。
2. 把 `PopTagLauncher.exe` 放进完整包根目录，以后新玩家从完整包进入更新流程。
3. 运行以下打包命令，输出目录须为新目录且不在游戏目录内部：

```powershell
python publish_update.py --root "D:\某个干净发布目录" --version v0.1.0 --out "D:\发布附件\v0.1.0" --notes "本次更新说明"
```

4. 新建标签为 `v0.1.0` 的 GitHub Release，上传输出目录内所有 ZIP 及 `update-manifest.json`。全部上传完成后才公开发布。首次及阶段性稳定版另外提供完整包。
5. 下一版改用 `v0.1.1` 等新标签，不覆盖旧标签附件。更新器可跨版本更新，每版清单均完整列出所需文件。

玩家只下载不同的组件。服务端代码、服务端依赖、客户端程序、各 `.idd` 大资源文件、Java 环境分别打包。大型 `.idd` 内部发生改变时，当前首版仍需下载整个对应组件，不做二进制差分。作者端每个 Release 必须有完整所需组件；玩家端“按需下载”不等于 GitHub 会自动产生更新包。

## 数据保护与回滚

只允许指定程序目录及文件进入清单。`server/data/local-accounts`、日志、客户端 NMDATA/ndadata 等本地数据不在更新范围。

每个 ZIP 及每个文件都校验 SHA-256；拒绝越界路径、重复文件、保留文件名和不匹配的 ZIP 内容。HTTPS 仓库来源与 SHA-256 用于来源约束和完整性校验，不将它们描述为独立的数字签名体系。

所有组件先下载和校验，之后才改动安装目录。改动前保存事务和旧文件；失败时回滚，中断后下一次启动会要求恢复。旧清单中已移除的程序文件只在内容仍匹配时删除；回滚遇到用户后续手动修改会停止，避免覆盖修改。历史备份保留于 `.updater/history`，后续可手动清理，首版不自动删除。

不在游戏运行时热替换文件。启动器本体的自动自我更新尚未实现，首版升级启动器需随完整包或手动替换 EXE。首版网络中断后重新下载对应组件，不支持断点续传。

## 开发与验证

```powershell
.\build.ps1
.\test.ps1
python -m unittest test_publisher -v
```

`CoreTests.cs` 覆盖原生文件事务、失败回滚、存档保护、错误包拒绝、废弃文件回滚及重启恢复。`test_publisher.py` 覆盖组件复用和输出边界。另有 Python 产物到 C# 安装器的跨语言验证。

测试覆盖文件事务、存档保护、失败回滚和发布格式；联网可用性取决于用户访问 GitHub 的网络环境。

参考：
- GitHub Releases API：https://docs.github.com/en/rest/releases/releases
- .NET ZIP API：https://learn.microsoft.com/en-us/dotnet/api/system.io.compression.ziparchive?view=netframework-4.8
