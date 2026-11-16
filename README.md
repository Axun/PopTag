# PopTag 2010 本地修复与国服内容移植

基于美服 2010 客户端及 BnbEmu 的本地扩展项目，含服务端适配、汉化、商城与装备同步、练习／激战和怪物模式修复，以及国服 057／324 的部分地图、脚本与商品资源适配。

这是本机运行版。目前不包含可用的跨电脑联机功能，也不是国服 057 原客户端的服务端适配版。

## 游玩

使用 Release 中的 `PopTag-2010-Local-v2026.11.16.7z`，解压后运行 `Start.cmd`，结束时运行 `Stop.cmd`。内置 Java 21，无需 Maven。

## 构建服务端

安装 JDK 21、Maven 3.9+，在 `server` 目录执行：

```powershell
mvn -Dtest=!PassportTest test
mvn compile exec:java
```

客户端另行从整合包取得，放在 `server` 的同级 `client` 目录。本源码包不包含客户端素材、个人存档、历史抓包或本机 Maven 缓存。历史抓包回放依赖未附带的 `cap/` 原始资料；`PassportTest` 也依赖历史抓包，不将其列入本次 220 项通过的测试。修复脚本是开发工具快照，含外部 `PopTag-shop` 资源解析模块及本地资源版本依赖，不是一键重新移植全部资源的流水线，请勿直接对唯一客户端副本执行。

## 来源与致谢

- [krrr/BnbEmu](https://github.com/krrr/BnbEmu)：上游服务端模拟器及协议、资源格式、逆向和工具资料。
- [chuichuide/pingu](https://github.com/chuichuide/pingu)：上游项目所基于的早期实现。
- [泡泡堂国服官网](https://bnb.web.sdo.com/)：国服客户端与内容来源。057 原始安装包作为版本对照附件，未改造成可直接游玩的 057 单机版。
- [Eclipse Temurin](https://adoptium.net/)：整合包内 Java 21，保留运行环境版权及许可文件。
- [Kotlin](https://kotlinlang.org/)、[Netty](https://netty.io/)、[kaml](https://github.com/charleskorn/kaml)、[ClassGraph](https://github.com/classgraph/classgraph)、[JUnit](https://junit.org/)：服务端开发与测试依赖。
- [Ghidra](https://github.com/NationalSecurityAgency/ghidra)、[REA](https://github.com/morluto/rea)、[Capstone](https://www.capstone-engine.org/)、[pefile](https://github.com/erocarrera/pefile)、[Wireshark](https://www.wireshark.org/)、[7-Zip](https://www.7-zip.org/)：项目分析、验证与打包使用的工具；未把工具调用等同于全部修改成果。

游戏程序、图像、音乐及国服素材的权利归原权利人；本项目不将其声明为原创或另行授予其许可。依赖的许可文件保留于 JAR 的 META-INF 与 runtime/legal。
