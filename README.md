# Neko云音乐点歌插件

一个基于 AstrBot 框架的 Neko 云音乐点歌插件,支持群内点歌、搜索音乐并生成精美图片展示。

> **2.0.0 升级提示**：旧版的 `client_id`、`client_platform`、`client_secret` 已不再使用，
> 升级后可直接删除这三项配置，无需重新申请客户端凭据。

## 功能特性

- 🎵 **点歌功能**: 发送 `点歌 歌曲名` 即可搜索音乐
- 🖼️ **图片生成**: 自动生成精美的搜索结果图片,包含封面和详细信息
- 🎶 **一键播放**: 回复序号即可播放对应歌曲
- 🔗 **播放链接**: 自动生成 Neko云音乐播放链接
- 🎤 **语音发送**: 自动下载音频并发送语音消息
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

1. 下载插件压缩包或克隆仓库到 AstrBot 的 `data/addons/plugins` 目录
2. 重启 AstrBot 或在插件管理中重载插件

## 使用方法

### 搜索音乐

在群聊中直接发送:

```
点歌 Lemon
点歌 告白气球
点歌 周杰伦
点歌 4855
```

歌曲 ID 可直接从 Neko 云音乐详情页地址 `/detail/{歌曲ID}` 获取。

插件会自动搜索并返回结果,包含:
- 搜索结果统计信息
- 使用提示
- 精美的搜索结果图片(包含每首歌的封面和详细信息)
- 歌曲数量

### 播放音乐

搜索结果返回后,直接回复对应的序号即可播放:

```
1
```

机器人会返回播放链接,包含:
- 歌曲名称
- Neko云音乐宣传语
- 播放链接 (https://music.nekocore.cn/detail/{歌曲ID})

### 示例

**搜索示例:**

用户发送:
```
点歌 Lemon
```

机器人回复:
```
🎵 搜索结果: Lemon
共找到 6 首歌曲
💡 回复序号即可播放,例如: 1

[精美图片,包含所有搜索结果]
```

**播放示例:**

用户回复:
```
1
```

机器人回复:
```
🎵 正在播放: Lemon
🎶 Neko云音乐。听见好音乐
🔗 https://music.nekocore.cn/detail/524

[自动发送语音消息，可直接播放收听]
```

### 图片内容

搜索结果图片包含:
- 渐变背景
- 搜索关键词和结果数量
- 每首歌的封面(90x90)
- 歌曲名称、歌手、专辑、时长、最高音质、ID
- 底部版权信息

搜索结果超过 18 首时，为避免图片超过 Telegram 的高度限制，会改用完整文本列表展示。

## 配置说明

在线 API 为公开接口，不需要 Client ID、Client Secret 或额外鉴权配置。插件会优先读取
AstrBot WebUI 中的配置，未配置时使用下列默认值：

| 配置项 | 说明 |
|--------|------|
| `use_local_server` | 是否改用本机服务，默认 `false` |
| `local_server_port` | 本机服务端口，默认 `65535` |
| `audio_quality` | 请求音源音质，可选 `standard` / `hq` / `sq` / `hires`，默认 `hq` |
| `audio_bitrate` | 发送前转码码率，默认 `96` kbps |
| `cache_expire_hours` | 本地音频缓存时长，默认 `24` 小时 |
| `auto_play_first` | 是否自动播放第一条搜索结果，默认 `false` |
| `show_auto_play_hint` | 是否显示自动播放提示，默认 `true` |
| `show_play_link` | 是否显示详情页播放链接，默认 `true` |
| `show_transcode_hint` | 是否显示下载转码提示，默认 `true` |

### API 说明

默认 API 地址为 `https://music.nekocore.cn`。插件使用当前文档中的公开接口：
`POST /api/music/search` 搜索歌曲，`GET /api/music/file/{id}?quality=...` 获取音源直链。
服务端会对请求频率进行限制，返回 `429` 时插件会读取 `Retry-After` 并有限次重试。

接口约定以 [NekoMusicDocs](https://github.com/FantasyNetworkCN/NekoMusicDocs) 为准。插件只调用
公开音乐搜索、封面与播放接口，不涉及用户登录、注册或人机验证流程。

### 注意事项

- 搜索结果会在当前会话中缓存,回复序号即可播放
- 每次搜索会更新会话中的搜索结果
- 序号从 1 开始,对应图片中的歌曲序号
- 音频会自动下载并发送为语音消息
- 音频文件使用临时存储,发送后自动清理

## 依赖项

- aiohttp >= 3.8.0
- Pillow >= 10.0.0 (PIL)
- 系统依赖 `ffmpeg`（用于音频转码与压缩）

## 字体说明

插件使用内置字体文件 `DreamHanSans-W17.ttc` 进行中文渲染，确保在各种环境下都能正确显示中文。

## 技术支持

- GitHub: https://github.com/NyaNyagulugulu/astrbot_NekoMusic
- Issues: https://github.com/NyaNyagulugulu/astrbot_NekoMusic/issues

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 获取详细更新记录。

## 许可证

本项目采用 AGPL-3.0 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 强大的 QQ 机器人框架
- [Neko云音乐](https://music.nekocore.cn) - 音乐数据来源
- [NekoMusicDocs](https://github.com/FantasyNetworkCN/NekoMusicDocs) - API 文档

## 作者

不穿胖次の小奶猫（NyaNyagulugulu）

---

**注意**: 本插件仅供学习和交流使用,请勿用于商业用途。
