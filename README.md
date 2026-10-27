# Neko云音乐点歌插件

一个基于 AstrBot 框架的 Neko 云音乐点歌插件,支持群内点歌、搜索音乐并生成精美图片展示。

# 警告。从`v1.7.2`版本更新肯能够会有安装失败错误。那么请你卸载重新安装

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

1. 下载插件压缩包或克隆仓库到 AstrBot 的 `data/plugins` 目录
2. 重启 AstrBot 或在插件管理中重载插件

## 使用方法

### 搜索音乐

在群聊中直接发送:

```
点歌 Lemon
点歌 告白气球
点歌 周杰伦
```

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
- 每首歌的封面(100x100)
- 歌曲名称、歌手、专辑、ID
- 底部版权信息

## 配置说明

在线 API 需要配置以下两项（请通过 NekoMusic 官方审核流程申请，Client ID 需绑定 `pc` 平台）：

| 配置项 | 说明 |
|--------|------|
| `client_id` | NekoMusic 分配的客户端 ID |
| `client_secret` | 与 Client ID 配对的客户端密钥，请勿泄露 |

未配置或凭据无效时，在线 API 会返回 `401`。首次请求时插件会自动完成客户端实例注册，
并在插件目录生成 `.neko_client_identity.json` 保存实例私钥与短期令牌；该文件已被 `.gitignore`
排除，请勿提交或分享。`client_secret` 仅在实例注册/续签时使用，业务请求通过 Client ID、
实例令牌和每请求签名完成鉴权。

### API 安全与客户端兼容

默认 API 地址为 `https://music.nekocore.cn`。插件按 Neko 云音乐 API 最新约定携带完整浏览器形态
请求头（`User-Agent` / `Accept` / `Accept-Language` / `Origin`），并用 `X-Neko-Client` 标注来源；
音乐搜索与音频解析均按约定处理一次性 nonce、客户端实例令牌和请求签名。
高难度安全挑战会在后台有限度地计算；若服务端要求的难度超出插件处理能力，请稍后重试。

接口约定详见 [NekoMusicDocs](https://github.com/FantasyNetworkCN/NekoMusicDocs)，包括
[客户端身份与 Client ID](https://github.com/FantasyNetworkCN/NekoMusicDocs/blob/main/API-%E5%AE%A2%E6%88%B7%E7%AB%AF%E8%BA%AB%E4%BB%BD%E4%B8%8EClient-ID.md)、
[防爬与客户端识别](https://github.com/FantasyNetworkCN/NekoMusicDocs/blob/main/API-%E9%98%B2%E7%88%AC%E4%B8%8E%E5%AE%A2%E6%88%B7%E7%AB%AF%E8%AF%86%E5%88%AB.md)、
[请求防重放](https://github.com/FantasyNetworkCN/NekoMusicDocs/blob/main/API-%E8%AF%B7%E6%B1%82%E9%98%B2%E9%87%8D%E6%94%BE.md)和
[滑块人机验证](https://github.com/FantasyNetworkCN/NekoMusicDocs/blob/main/API-%E6%BB%91%E5%9D%97%E4%B8%8E%E4%BA%BA%E6%9C%BA%E9%AA%8C%E8%AF%81.md)。
本插件只调用公开音乐搜索与播放接口，不涉及注册或滑块验证流程。

### 注意事项

- 搜索结果会在当前会话中缓存,回复序号即可播放
- 每次搜索会更新会话中的搜索结果
- 序号从 1 开始,对应图片中的歌曲序号
- 音频会自动下载并发送为语音消息
- 音频文件使用临时存储,发送后自动清理

## 依赖项

- aiohttp >= 3.8.0
- Pillow >= 10.0.0 (PIL)
- cryptography >= 41.0.0

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
