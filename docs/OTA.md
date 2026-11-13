# WMA301 v2.0 专属 OTA：运行和发布流程

此功能独立于亚瑟的 PPE/NSS OTA，也**不覆盖原生 LuCI「备份/升级」页**。只适用已迁移至本项目单 UBI 四卷布局的 WMA301 v2.0。

## 功能及当前边界

- LuCI：**系统 → WMA301 在线更新**，提供检查最新版本、下载并校验、人工确认升级。
- 后端：`/usr/sbin/wma301-ota {status|check|download|start}`。使用 HTTPS 从 `pzcn/wma301-immortalwrt` 独立 OTA Release 获取镜像。
- 设备/渠道校验：必须匹配 `tplink,wma301-v2`、`tplink_wma301-v2`、固定单 UBI 方案和构建时内嵌 `/etc/wma301-ota-release`。
- 发布格式：`wma301-ota-testing-r<GitHubRunID>` 或 `wma301-ota-stable-r<GitHubRunID>`，元数据 `ota.json` 含版本、设备、SHA256、精确 FIT 文件名和大小。
- 检查时比较构建编号，不允许 OTA 降级；下载后强制校验 SHA256、大小和 `sysupgrade -T`。
- 升级前再检查 `/proc/mtd` 的 121 MiB `ubi` 分区以及已挂载的 `fit`、`ubootenv`、`ubootenv2`、`rootfs_data` 四卷。**绝不直接写 BL2/FIP/原厂只读分区，也不执行 `ubiformat` 或 `sysupgrade -F`。**
- 自动刷写**始终关闭**；安装按钮默认不可用。只有已经完成实机升级与恢复路径验证的设备，才应由管理员手动启用。
- 常规 `sysupgrade` 默认保留配置；但**目前不自动重新安装用户额外安装的 APK**。这项能力需在实机确定保留配置、软件源可用性后再加，避免恢复未知包（例如用户明确不要的 sing-box）。

## 1. 构建带 OTA 身份的 FIT

快速构建：`.github/workflows/official-builder.yml`。

1. 正常按官方 ImageBuilder SHA256 复用缓存、注入 WMA301 DTB、软件包和 Aurora。
2. 在生成 rootfs 之前，`scripts/wma301_ota.py stamp` 把**构建运行 ID、仓库 commit、官方 Builder SHA256、板型和分区布局**写入临时固件根目录的 `/etc/wma301-ota-release`。
3. `scripts/verify_official.py` 对 FIT 做原有检查，同时核对生成时的 OTA 身份与精确 Builder 来源，加入 Artifact 的 `manifest.json`。
4. 仅上传 14 天实验 Artifact，**不自动发布 OTA Release、不自动刷机**。完整源码后备也内嵌构建身份，但其双 FIT 预发布不自动进入 OTA 通道。

## 2. 人工发布 OTA Release（不可跳过）

在 GitHub Actions 选择 **WMA301 | Promote verified FIT to dedicated OTA Release**，选择：

- `source_run_id`：成功的快速构建 Run ID，必须仍在 Artifact 保存期内。
- `channel=testing`：测试发布，创建 GitHub prerelease；默认设备不会检测它，需明确切换测试通道。
- `channel=stable`：公开稳定发布；必须输入确认字串 `WMA301_UBI_SYSUPGRADE_HARDWARE_VERIFIED`，表示已在实机验证 UBI 环境卷、保留配置、启动及回退。

发布工作流再次从原运行下载 Artifact，检查该运行成功、属于本仓库主分支及指定快速工作流，再核验镜像 SHA256、真实 FIT/DTS 和本机嵌入 OTA 身份。由于官方 ImageBuilder 产物带有快照版本前缀，发布器会**严格验证原始文件名后统一重命名为固定 OTA FIT 附件名**，重新生成对应 SHA256SUMS 和 `ota.json`，以**不可覆盖的独立 tag**发布 FIT、校验和与 manifest。重复 tag 直接失败。

**未完成实机验证时，只允许 testing prerelease，不应创建 stable OTA Release。**

## 3. 路由器上检查和下载

安装包含本功能的固件后，打开 LuCI「系统 → WMA301 在线更新」即可检查，或 SSH：

```sh
wma301-ota status
wma301-ota check
wma301-ota download
```

默认通道为 `stable`。想主动测试人工发布的 prerelease：

```sh
uci set wma301-ota.main.channel='testing'
uci commit wma301-ota
wma301-ota status
```

如果尚未手工发布相应 Release，提示「No OTA Release on the selected channel」是正常的，**不代表 ImageBuilder 编译失败**。只有最近构建的固件包含 OTA 身份；旧固件缺少身份时拒绝启用本 OTA，应先通过原生升级方式完成受控首次迁移。

## 4. 确认实机安全后启用手动升级

在确认四个 UBI 卷、`sysupgrade -T`、配置保留和恢复手段之后，管理员才可通过 SSH 显式开启：

```sh
uci set wma301-ota.main.enable_flash='1'
uci commit wma301-ota
```

随后刷新 LuCI 页面、检查更新、下载并验证、点击「手动安装」。也可执行：

```sh
wma301-ota start
```

它只会在**已经下载并校验**的固件版本上启动后台人工升级；升级之前会再次查询发布、比较版本、核验 SHA256、执行 `sysupgrade -T` 并检查 UBI 四卷。错误日志在 `/tmp/wma301-ota/update.log`。实际升级使用原生 `sysupgrade` 保留配置模式，没有强制刷写、自动升级或定时任务。

取消手动刷写权限：

```sh
uci set wma301-ota.main.enable_flash='0'
uci commit wma301-ota
```

## 5. 下一阶段验收

- [x] WMA301 独立发布渠道、版本身份、元数据生成和人工发布工作流
- [x] LuCI 检查/下载/人工确认入口，后端哈希、设备/UBI 保护
- [ ] GitHub Actions 全绿，验证 FIT 产物含 OTA 构建身份（CI 只检查打包源和元数据）
- [ ] 在实际 WMA301 v2.0 上验证 `/proc/mtd`、四个 UBI 卷、下载校验及启动
- [ ] 经实机测试完成至少多轮 `sysupgrade`、重启、保留配置和恢复验证
- [ ] 经上述验证后，再人工提升为 stable 发布
- [ ] 按需实现额外 APK 恢复，但避免自动安装不希望的软件包

**安全限制：** 校验 HTTPS 和 SHA256 只能检查下载完整性及与发布元数据的一致性，并不是独立密码学签名；若需对抗 Release 账号/渠道被攻破的情况，未来可另外引入固件签名与设备端公钥验证。
