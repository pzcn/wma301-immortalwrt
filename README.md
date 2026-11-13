# WMA301 v2.0 · ImmortalWrt (upstream-tracking)

只维护 **TP-Link WMA301 v2.0** 的固件适配，不 fork ImmortalWrt，不维护第三套 U-Boot，不锁定 ImmortalWrt 的 commit。

## 仓库分工

- [pzcn/bl-mt798x-dhcpd](https://github.com/pzcn/bl-mt798x-dhcpd/tree/wma301)：自定义 Yuzhii BL33 / Web / DHCP。
- [pzcn/wma301-openwrt](https://github.com/pzcn/wma301-openwrt)：原厂 NAND 迁移、首装、FIP 重打包和恢复工具。
- **这里**：每次从官方 `immortalwrt/immortalwrt` 的 `openwrt-25.12` 分支获取实时 HEAD，使用本仓库设备适配构建两种 FIT 固件。

## 官方 ImageBuilder 快速构建（实验）

新增独立工作流 [official-builder.yml](.github/workflows/official-builder.yml)，
优先复用官方 ImmortalWrt `25.12-SNAPSHOT/mediatek/filogic`
已经编译好的内核、驱动、基础软件包和 ImageBuilder。以官方二进制的
`version.buildinfo` 源码修订为基准，增量注入本设备 DTS、profile、
网络/MAC/环境/升级逻辑，**只单独编译设备树，不重新编译内核**。

该流程目前仅生成 `squashfs-sysupgrade.itb`，运行当前 FIT/DTS/NAND
离线校验，仅上传 GitHub Actions 实验 Artifact，不发布 Release，
也不自动刷入设备。官方配套 SDK 只记录名称和 SHA256，暂未接入缺包补编。
详情：[官方 Builder 设计与限制](docs/OFFICIAL-IMAGEBUILDER.md)。

**原 `firmware.yml` 完整源码构建、双 FIT 输出和成功才发布的策略均保留，作为后备。**
新快速路径修改不会触发旧工作流的 push 全量构建。

## 自动化策略

- GitHub Actions 每天执行一次；未发现上游或本仓库代码变化时不重复编译。
- 有变化即构建并做 FIT 哈希、Linux DTS / NAND 边界、卷名、文件尺寸等离线验证。
- **只有所有步骤完成才新建 GitHub Release**；失败不覆盖、不删除、不改动之前成功发布的 Release。下一次检查会再次尝试。
- 发布带实际使用的上游 SHA、本仓库 SHA、SHA256SUMS；为了区分离线测试与实机验证，当前使用 **pre-release** 标记。
- 支持 Actions 页面手动运行，`force=true` 时即使没有上游变化也可重新测试。
- GitHub Actions 定时计划是近似调度，偶尔可能延迟或跳过；不保证精确到分钟。

工作流：[.github/workflows/firmware.yml](.github/workflows/firmware.yml)

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
- `firmware.yml`：每日检查、拉取官方分支最新提交、编译、审计、发布。

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
