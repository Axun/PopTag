# PopTag 2010 本地修复与国服内容移植

基于 Nexon 美服 2010 客户端与 BnbEmu 的本地扩展项目。支持单人练习、激战、怪物模式及同机双人（2P）；跨电脑联机尚未开放。不是国服057原客户端的服务端适配版。

## 游玩与更新

在 [Release](https://github.com/Fish0731/PopTag/releases) 下载 `PopTag-2010-Local-v2026.11.16.1.7z`，完整解压后双击 `Start.cmd`，结束时运行 `Stop.cmd`。整合包含 Java 21，无需 Maven。不能同时运行两份本地服务端。

账号支持中文，密码使用任意6～12位英文字母或数字；不要填写其他服务的真实密码。双人登录时使用两个不同的本地账号，两人的背包、金币、经验分别保存。新账号初始300万金币，购买正常扣款。

更新前备份旧版 `server/data/local-accounts`，关闭旧版后，将自己的该目录复制到新版同一路径。发布包仅附“潜在游鱼”一条展示历史，不附带作者账号的金币、经验、装备或登录缓存；历史列表不代表在线状态。

## 本次更新

- 新增同机2P的登录、房间及开局适配；按玩家编号处理资料、角色、道具、商城扣款和物品归属，修正第二玩家踢海星被误判为第一玩家的问题。
- 加入国服057地牢01～22、原版缩略图与中文选图分组，保留原有怪物地图内容。
- 扩充057经典服饰与国服商品，修复批量商品目录加载、购买后重复图标、商城试穿配色；调整商城首页。
- 同步激战金银岛炮台脚本控制权，恢复红色迷幻水泡的发射与爆炸；作者实测通过。
- 补充大厅双人页签、选择玩家及选图窗口中文；修正双人列表顺序、重复记录、第二玩家资料和金币缓存。

更多内容见 [更新说明](RELEASE-NOTES.md)。这些是当前修复范围和已完成的检查，不表示每款商品、地图和设备都经过逐项实测。

## 构建服务端

JDK21、Maven3.9+，在 `server` 目录运行：

```powershell
mvn -Dtest=!PassportTest test
mvn compile exec:java
```

测试账号写入 `server/target/test-accounts`，与实际游戏存档隔离。`PassportTest` 及历史抓包回放工具需要未附带的原始抓包。客户端从整合包取得，放到 `server` 同级的 `client` 目录。本源码不含客户端图像、音乐、个人存档、抓包或本机依赖缓存。

`tools/client-repair` 是开发脚本快照，部分脚本依赖作者本地版本目录和外部资源解析模块，不是一键从原版重建全部内容的流水线。

## 来源与工具

- [krrr/BnbEmu](https://github.com/krrr/BnbEmu)：美服PopTag服务端模拟器、协议及逆向资料、资源格式和Python工具；官方美服客户端来自其Release中的PopTag.7z。
- [chuichuide/pingu](https://github.com/chuichuide/pingu)：上游项目所基于的早期实现。
- [泡泡堂国服官网](https://bnb.web.sdo.com/)：本地国服057、324客户端内容及名称对照。057原始安装包保留在上一版Release中，仅作版本研究对照。
- [Eclipse Temurin](https://adoptium.net/)：包内Java21，保留运行环境版权和许可文件。
- [Kotlin](https://kotlinlang.org/)、[Netty](https://netty.io/)、[kaml](https://github.com/charleskorn/kaml)、[ClassGraph](https://github.com/classgraph/classgraph)、[JUnit](https://junit.org/)：服务端和测试依赖。
- [Ghidra](https://github.com/NationalSecurityAgency/ghidra)、[REA](https://github.com/morluto/rea)、[Capstone](https://www.capstone-engine.org/)、[pefile](https://github.com/erocarrera/pefile)、[Wireshark](https://www.wireshark.org/)、[7-Zip](https://www.7-zip.org/)：分析、验证及打包工具。

游戏程序、美术、音乐及国服素材的权利归原权利人；本项目不将其声明为原创或另行授予其许可。依赖许可保留在JAR的META-INF和runtime/legal中。

## 游戏启动器

[v2026.11.17](https://github.com/Fish0731/PopTag/releases/tag/v2026.11.17) 提供带自动更新的游戏启动器。新玩家下载完整包；已有玩家下载 `PopTagLauncher.exe` 放进游戏根目录。工具源码和发布步骤见 [启动器说明](tools/PopTagUpdater/README.md)。
