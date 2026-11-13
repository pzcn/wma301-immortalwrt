# WMA301 v2.0 · ImmortalWrt (upstream-tracking)

只维护 **TP-Link WMA301 v2.0** 的固件适配，不 fork ImmortalWrt，不维护第三套 U-Boot，不锁定 ImmortalWrt 的 commit。

## 仓库分工

- [pzcn/bl-mt798x-dhcpd](https://github.com/pzcn/bl-mt798x-dhcpd/tree/wma301)：自定义 Yuzhii BL33 / Web / DHCP。
- [pzcn/wma301-openwrt](https://github.com/pzcn/wma301-openwrt)：原厂 NAND 迁移、首装、FIP 重打包和恢复工具。
- **这里**：优先利用官方 `25.12-SNAPSHOT/mediatek/filogic` 已编译的内核、驱动和软件包，快速生成 sysupgrade FIT；必要时手工执行最新 HEAD 完整源码构建，得到双 FIT。

## 构建策略：官方 ImageBuilder 优先

默认使用 [官方 Builder 快速工作流](.github/workflows/official-builder.yml) **每天检查**官方 SNAPSHOT：内核与 APK 直接复用，单独编译 WMA301 设备树。对官方 ImageBuilder、匹配 Linux 头文件使用按 SHA256 命名的 GitHub Actions 缓存；按官方二进制哈希、代码输入和周次判断是否需要重打包。

官方软件包在 [configs/official-packages.txt](configs/official-packages.txt) 管理（包括 Bootstrap 回退主题）。**Aurora v1.4.0** 独立从固定版本源码获取：快速路径只复制已编译的主题文件，不下载 SDK；完整源码后备则编译标准 LuCI 主题 APK。快速路径只生成 sysupgrade FIT，通过离线校验后上传 **14 天验证 Artifact**；**默认不发布 OTA 固件源**。OTA 代码仍保留在仓库中，按需再启用。官方配套 SDK 目前只记录来源，第三方 APK 补编留在后续计划。

原 [完整源码构建后备](.github/workflows/firmware.yml) **改为手动运行**，保留最新 HEAD、双 FIT、离线验证与 pre-release 发布机制；不再每天或在 push 时重复完整编译。

**维护入口：[完整构建计划、流程、故障处理和后续任务](docs/BUILD-RUNBOOK.md)**。另见 [官方 Builder 技术说明](docs/OFFICIAL-IMAGEBUILDER.md)。

## 亚瑟通用软件同步

已将亚瑟的通用 LuCI 插件、简体中文、WireGuard、WOL、SQM 等移入 [固件软件包清单](configs/official-packages.txt)，并增加简体中文初始化。**Tailscale（含 LuCI/中文包及专用 kmod-tun）、DDNS-Go（含 LuCI/中文包）默认以负号排除，配置项保留可恢复；sing-box 仍不安装。** Qualcomm NSS/PPE、eMMC/F2FS、Dr.COM 均不复制；WMA301 OTA 实现保留但默认屏蔽。

完整取舍说明：[亚瑟软件同步清单](docs/ARTHUR-SOFTWARE.md)。


## Aurora 主题

默认使用与亚瑟相同的 [Aurora v1.4.0](https://github.com/eamonxg/luci-theme-aurora/tree/v1.4.0)，源码提交锁定为 `84c27b66952e6fc4be60128067a6b88bfd34afb5`；**不会锁定 ImmortalWrt 上游版本**。首次启动自动注册并默认选中 Aurora，保留官方 Bootstrap 供故障回退，且不覆盖已保存的其他主题选择。

实现细节与回退方法见 [docs/AURORA.md](docs/AURORA.md)。Aurora 不依赖 sing-box；固件仍明确不安装 sing-box 或 HomeProxy。

## WMA301 专属 OTA（默认屏蔽）

WMA301 OTA 后端、LuCI 页面、RPC ACL、配置、构建身份和单源发布代码**全部保留**，但当前两条构建流程均将 `WMA301_ENABLE_OTA` 设为 `'false'`。默认固件不会安装 OTA 页面或后端，不嵌入 OTA 身份，也不自动发布 `wma301-ota-r<RunID>` Release。普通 LuCI「备份/升级」和手动刷写 FIT 功能不受影响。

需要恢复时，将 `.github/workflows/official-builder.yml` 和 `.github/workflows/firmware.yml` 顶层 `WMA301_ENABLE_OTA` 均改为 `'true'` 后重新构建；不要仅启用 OTA 发布而不注入对应设备文件。详细实现留存于 [OTA 手册](docs/OTA.md)。

## 固件格式与分区

**只针对已完成刷入迁移、采用当前单 UBI 布局的 WMA301 v2.0。**

```text
0x000000..0x020000  bl2           (OEM, RO)
0x020000..0x3c0000  fip           (OEM BL31 + 自定义 BL33, RO)
0x3c0000..0x400000  reserved      (RO)
0x400000..0x480000  factory_info  (RO)
0x480000..0x500000  art           (RO)
0x500000..0x700000  config        (RO)
0x700000..0x8000000 ubi           (121 MiB)
```

UBI 中使用 `fit`（本项目的 SquashFS FIT）、`ubootenv`、`ubootenv2`、`rootfs_data`（UBIFS overlay）四卷。**本仓库发布的 FIT 本身不含环境卷，不是 NAND 全片镜像，也不是 `ubiformat` 输入。** 四卷初装和环境持久化由刷入工具负责；升级必须保护 U-Boot 环境卷。

## 源码结构

- `device/`：WMA301 v2.0 Linux DTS、公共 dtsi、极薄的 filogic 设备定义。
- `configs/wma301.config`：系统选项。
- `scripts/prepare.py`：在临时下载的官方树中添加 WMA301 定义、网络、FIT 升级识别；遇到官方原生定义或不匹配直接失败，不强行覆盖。
- `scripts/verify.py`：在编译之后检查两个 FIT 镜像、签名/哈希和实际 DTS 分区协议。
- `official-builder.yml`：每天检查官方二进制、复用缓存、重打包、校验后上传 Artifact；OTA Release 发布默认关闭。
- `firmware.yml`：手工运行的 HEAD 完整源码双 FIT 构建与预发布后备。

**限制：** 当前仅做源码编译/结构与完整性检查，不能证明 Wi-Fi 校准、交换机链路、BL33 加载、overlay 掉电持久化和 Web 恢复均在硬件上通过。首次刷入前须从独立刷入仓库完成备份及实机验证。未经验证不应把预发布固件自动推送到设备上。

## 手工构建

```sh
git clone --depth=1 --branch openwrt-25.12 https://github.com/immortalwrt/immortalwrt.git upstream
python3 scripts/prepare.py --upstream upstream
(cd upstream && ./scripts/feeds update -a && ./scripts/feeds install -a)
cp configs/wma301.config upstream/.config
(cd upstream && make defconfig && make download -j2 && make -j2)
python3 scripts/verify.py --images upstream/bin/targets/mediatek/filogic --output dist
```

编译器工具链和下载依赖由上游维护；本仓库不保存上游源码快照。若官方更新改变 DTS/固件规则，工作流应失败并保留上一成功发行版，而不是用旧文件覆盖官方更改。
