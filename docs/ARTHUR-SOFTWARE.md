# WMA301 与亚瑟固件的软件功能同步

同步来源：[pzcn/openwrt-ppe-nss-ota](https://github.com/pzcn/openwrt-ppe-nss-ota) 的 `config/add.txt`、`config/remove.txt` 及 LuCI 首次启动配置。

**此次明确不安装 sing-box**（既不安装内核，也不移植 sing-box JSON LuCI、开机配置或相关依赖）。HomeProxy 同样不随固件预装。两个路由器硬件和用途不同，不能简单照搬整个文件树。

## 已移植的官方软件包

- LuCI + 简体中文、文件管理、ttyd 终端、nlbwmon、Wi-Fi 历史、IRQBalance、LLDP、PBR、定时重启。
- WireGuard、tcpdump、ip-full、conntrack、curl/jsonfilter 等网络维护工具。
- SQM + BCP38 及其中文包；这里是 MT7981 原生软件队列，不包含亚瑟 Qualcomm PPE/NSS QoS。
- WOL/Etherwake、Tailscale 原生 LuCI 管理及中文包、DDNS-Go 和中文管理界面。
- 移除可能重复或不适合此设计的 HomeProxy、Diskman、Statistics 和 ip-tiny。

统一软件清单：`configs/official-packages.txt`。默认快速构建使用配套官方 ImageBuilder APK；原完整源码构建后备也会引用同一清单。更改清单将触发重新打包。

## 已移植的通用配置

- `files/etc/uci-defaults/95-luci-preferences`：首次启动只设置简体中文 LuCI。不会改变 Wi-Fi、管理员密码、主题或 OTA 通道。

## 此次不移植

| 项目 | 原因 |
| --- | --- |
| sing-box 服务和 JSON LuCI | 用户明确不要；完全不打包 |
| HomeProxy | 无代理组件需求 |
| QCA NSS / PPE 驱动、QoS、遥测页面 | Qualcomm IPQ60xx 特有；WMA301 是 MediaTek MT7981 |
| eMMC / F2FS / extroot 补丁 | WMA301 为单 UBI + UBIFS overlay，不需要亚瑟 eMMC 修复 |
| Dr.COM 校园网认证 | 亚瑟当前也没有默认装进固件，WMA301 不移植 |
| Aurora 主题 | 非官方 25.12 LuCI feed 组件；本轮保持官方主题，避免为外观编译第三方 APK |
| 自定义 OTA / 覆盖官方 flash.js | WMA301 还未完成实机升级与 UBI 环境卷验证；必须独立实现且不能直接套用亚瑟 eMMC 升级逻辑 |
| CPU 频率调节、autocore/default-settings-chn | 与 SoC、设备预置项关联；先不在 WMA301 强行启用 |

## 后续计划

1. CI 对完整包清单打包，定位不存在的 APK、依赖冲突与 FIT 体积。
2. 为无匹配官方二进制的**确实必要**软件包补充同 ABI 官方 SDK 构建；没有缺包不下载 SDK。
3. 实机验证 LuCI、Tailscale、WOL、Wi-Fi MAC、WireGuard、SQM、rootfs_data 和配置保留。
4. 实机通过后再考虑单独适配 WMA301 OTA。不能用亚瑟的升级脚本直接写 WMA301 NAND。

已验证的构建流程和失败回退详见 [BUILD-RUNBOOK.md](BUILD-RUNBOOK.md)。
