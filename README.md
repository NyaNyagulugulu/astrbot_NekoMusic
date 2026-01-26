# Neko云音乐点歌插件

一个基于 AstrBot 框架的 Neko 云音乐点歌插件,支持群内点歌、搜索音乐并生成精美图片展示。

## 功能特性

- 🎵 **点歌功能**: 发送 `点歌 歌曲名` 即可搜索音乐
- 🖼️ **图片生成**: 自动生成精美的搜索结果图片,包含封面和详细信息
- 📝 **详细信息**: 显示歌曲名、歌手、专辑和歌曲 ID
- 🔍 **智能搜索**: 支持模糊搜索,返回所有相关结果
- 🎨 **精美UI**: 采用渐变背景、圆角卡片等现代设计元素

## 安装方法

### 方法一: 通过 AstrBot WebUI 安装

1. 打开 AstrBot WebUI
2. 进入插件管理页面
3. 点击"安装插件"
4. 上传 `astrbot_NekoMusic.zip` 或输入仓库地址: `https://github.com/NyaNyagulugulu/astrbot_NekoMusic`
5. 等待安装完成

### 方法二: 手动安装

1. 下载插件压缩包或克隆仓库到 AstrBot 的 `data/plugins` 目录
2. 重启 AstrBot 或在插件管理中重载插件

## 使用方法

### 基本用法

在群聊中直接发送:

```
点歌 Lemon
点歌 告白气球
点歌 周杰伦
```

插件会自动搜索并返回结果,包含:
- 搜索结果统计信息
- 精美的搜索结果图片(包含每首歌的封面和详细信息)
- 歌曲数量

### 示例

用户发送:
```
点歌 Lemon
```

机器人回复:
```
🎵 搜索结果: Lemon
共找到 6 首歌曲

[精美图片,包含所有搜索结果]
```

图片内容包括:
- 渐变背景
- 搜索关键词和结果数量
- 每首歌的封面(100x100)
- 歌曲名称、歌手、专辑、ID
- 底部版权信息

## 配置说明

本插件无需额外配置,安装即可使用。

## 依赖项

- aiohttp >= 3.8.0
- Pillow >= 9.0.0 (PIL)

## 字体说明

插件使用内置字体文件 `DouyinSansBold.otf` 进行中文渲染,确保在各种环境下都能正确显示中文。

## 技术支持

- GitHub: https://github.com/NyaNyagulugulu/astrbot_NekoMusic
- Issues: https://github.com/NyaNyagulugulu/astrbot_NekoMusic/issues

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 获取详细更新记录。

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 强大的 QQ 机器人框架
- [Neko云音乐](https://music.cnmsb.xin) - 音乐数据来源

## 作者

不穿胖次の小奶猫（NyaNyagulugulu）

---

**注意**: 本插件仅供学习和交流使用,请勿用于商业用途。