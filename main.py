import asyncio
import io
import json
import os
import re
import shutil
import tempfile
import time
import traceback
import textwrap
from typing import Dict, List, Tuple

import aiohttp
from PIL import Image, ImageDraw, ImageFont
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp


class MusicSearchDrawer:
    """音乐搜索结果图片绘制器"""

    # 常量定义
    FONT_PATHS = [
        FONT_PATH_REGULAR := os.path.join(os.path.dirname(__file__), "DreamHanSans-W17.ttc"),
        FONT_PATH_BOLD := FONT_PATH_REGULAR,
    ]

    # 颜色定义 - 二次元风格配色
    COLOR_BG_START = (255, 245, 248)  # 樱花粉渐变起始
    COLOR_BG_END = (245, 248, 255)    # 天空蓝渐变结束
    COLOR_HEADER = (102, 78, 163)     # 梦幻紫
    COLOR_SUBTITLE = (158, 158, 158)  # 柔和灰
    COLOR_SONG_NAME = (68, 68, 68)    # 深灰
    COLOR_SONG_INFO = (142, 142, 142) # 浅灰
    COLOR_CARD_BG = (255, 255, 255)   # 纯白
    COLOR_CARD_OUTLINE = (230, 230, 250) # 淡紫边框
    COLOR_ACCENT = (255, 107, 157)    # 粉色强调色
    COLOR_ACCENT_SECOND = (78, 205, 196) # 青色辅助色
    COLOR_FOOTER = (180, 180, 180)    # 底部文字颜色
    COLOR_NUMBER_BG = (255, 107, 157) # 序号背景粉色
    COLOR_NUMBER_TEXT = (255, 255, 255) # 序号文字白色

    # 布局尺寸
    # Telegram 图片限制: 宽度最大 1280px, 高度最大 2560px, 大小最大 10MB
    # 使用较小的宽度以确保兼容性和快速加载
    IMG_WIDTH = 720  # 优化宽度
    PADDING = 24     # 内边距
    HEADER_HEIGHT = 140  # 标题区域高度（增加）
    ITEM_HEIGHT = 120    # 每首歌曲的高度
    FOOTER_HEIGHT = 60   # 底部高度（减少）

    def __init__(self):
        self._load_fonts()

    def _load_fonts(self):
        """加载字体"""
        import os
        try:
            loaded = False
            for font_path in self.FONT_PATHS:
                # 检查文件是否存在
                if not os.path.exists(font_path):
                    logger.warning(f"字体文件不存在: {font_path}")
                    continue

                # 检查文件是否可读
                if not os.access(font_path, os.R_OK):
                    logger.warning(f"字体文件不可读: {font_path}")
                    continue

                logger.info(f"字体文件存在且可读: {font_path}")

                try:
                    logger.info(f"尝试加载字体: {font_path}")

                    # 尝试多种加载方式
                    # 方式1: 指定索引加载 TTC 字体
                    try:
                        self.font_title = ImageFont.truetype(font_path, 36, index=0)
                        self.font_subtitle = ImageFont.truetype(font_path, 18, index=0)
                        self.font_song_name = ImageFont.truetype(font_path, 22, index=0)
                        self.font_song_info = ImageFont.truetype(font_path, 16, index=0)
                        self.font_footer = ImageFont.truetype(font_path, 12, index=0)
                        logger.info(f"成功加载字体（方式1）: {font_path}")
                        loaded = True
                        break
                    except Exception as e1:
                        logger.warning(f"方式1加载失败 {font_path}: {str(e1)}")
                        pass

                    # 方式2: 不指定索引
                    try:
                        self.font_title = ImageFont.truetype(font_path, 36)
                        self.font_subtitle = ImageFont.truetype(font_path, 18)
                        self.font_song_name = ImageFont.truetype(font_path, 22)
                        self.font_song_info = ImageFont.truetype(font_path, 16)
                        self.font_footer = ImageFont.truetype(font_path, 12)
                        logger.info(f"成功加载字体（方式2）: {font_path}")
                        loaded = True
                        break
                    except Exception as e2:
                        logger.warning(f"方式2加载失败 {font_path}: {str(e2)}")
                        pass

                except Exception as e:
                    logger.warning(f"加载字体 {font_path} 失败: {str(e)}")
                    logger.warning(traceback.format_exc())
                    continue

            if not loaded:
                logger.warning("所有自定义字体加载失败，使用默认字体（中文可能无法正常显示）")
                self.font_title = ImageFont.load_default()
                self.font_subtitle = ImageFont.load_default()
                self.font_song_name = ImageFont.load_default()
                self.font_song_info = ImageFont.load_default()
                self.font_footer = ImageFont.load_default()
        except Exception as e:
            logger.error(f"字体加载过程发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            self.font_title = ImageFont.load_default()
            self.font_subtitle = ImageFont.load_default()
            self.font_song_name = ImageFont.load_default()
            self.font_song_info = ImageFont.load_default()
            self.font_footer = ImageFont.load_default()

    @staticmethod
    def _draw_gradient(draw, width: int, height: int, start: Tuple[int, int, int], end: Tuple[int, int, int]):
        """绘制渐变背景"""
        for y in range(height):
            r = int(start[0] + (end[0] - start[0]) * y / height)
            g = int(start[1] + (end[1] - start[1]) * y / height)
            b = int(start[2] + (end[2] - start[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

    @staticmethod
    def _draw_rounded_rectangle(draw, xy, radius, fill=None, outline=None, width=1):
        """绘制圆角矩形"""
        x1, y1, x2, y2 = xy
        if x1 >= x2 or y1 >= y2:
            return
        radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)

        if fill:
            draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill)
            draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill)
            draw.pieslice((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=fill)
            draw.pieslice((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=fill)
            draw.pieslice((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=fill)
            draw.pieslice((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=fill)

        if outline and width > 0:
            draw.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=outline, width=width)
            draw.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=outline, width=width)
            draw.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=outline, width=width)
            draw.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=outline, width=width)
            draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)
            draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=outline, width=width)
            draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=outline, width=width)
            draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)

    async def draw_search_result(self, keyword: str, result_data: dict, session) -> bytes:
        """绘制搜索结果图片 - 二次元风格（使用 PIL）"""
        try:
            songs = result_data.get("songs", [])
            total = result_data.get("total", 0)

            # 检查 songs 是否为 None
            if songs is None:
                logger.error("songs 为 None，无法绘制图片")
                return None

            # 计算总高度
            total_height = self.HEADER_HEIGHT + len(songs) * self.ITEM_HEIGHT + self.FOOTER_HEIGHT + self.PADDING * 3

            # 创建图片
            img = Image.new('RGB', (self.IMG_WIDTH, total_height), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)

            # 绘制渐变背景
            self._draw_gradient(draw, self.IMG_WIDTH, total_height, self.COLOR_BG_START, self.COLOR_BG_END)

            # 绘制顶部装饰条（渐变色）
            self._draw_gradient(draw, self.IMG_WIDTH, 6, self.COLOR_ACCENT, self.COLOR_ACCENT_SECOND)

            # 绘制标题区域背景
            header_bg_y = self.HEADER_HEIGHT - 20
            self._draw_rounded_rectangle(
                draw,
                (self.PADDING - 8, 6, self.IMG_WIDTH - self.PADDING + 8, header_bg_y),
                radius=12,
                fill=(255, 255, 255),
                outline=self.COLOR_CARD_OUTLINE,
                width=1
            )

            # 绘制标题（带阴影效果）
            title_text = "音乐搜索"
            title_bbox = draw.textbbox((0, 0), title_text, font=self.font_title)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.IMG_WIDTH - title_width) // 2

            # 阴影
            draw.text((title_x + 2, 28 + 2), title_text, font=self.font_title, fill=(200, 200, 200))
            # 主标题
            draw.text((title_x, 28), title_text, font=self.font_title, fill=self.COLOR_HEADER)

            # 绘制关键词标签
            keyword_label = f"搜索: {keyword}"
            keyword_bbox = draw.textbbox((0, 0), keyword_label, font=self.font_subtitle)
            keyword_width = keyword_bbox[2] - keyword_bbox[0]
            keyword_x = (self.IMG_WIDTH - keyword_width) // 2
            draw.text((keyword_x, 70), keyword_label, font=self.font_subtitle, fill=self.COLOR_ACCENT)

            # 绘制结果数
            result_text = f"找到 {total} 首歌曲"
            result_bbox = draw.textbbox((0, 0), result_text, font=self.font_subtitle)
            result_width = result_bbox[2] - result_bbox[0]
            result_x = (self.IMG_WIDTH - result_width) // 2
            draw.text((result_x, 92), result_text, font=self.font_subtitle, fill=self.COLOR_SUBTITLE)

            # 绘制每首歌曲
            y_offset = self.HEADER_HEIGHT
            for idx, song_info in enumerate(songs, 1):
                # 绘制卡片背景（圆角矩形）
                card_y_start = y_offset + 8
                card_y_end = y_offset + self.ITEM_HEIGHT - 8

                # 卡片阴影
                shadow_offset = 3
                self._draw_rounded_rectangle(
                    draw,
                    (self.PADDING + shadow_offset, card_y_start + shadow_offset,
                     self.IMG_WIDTH - self.PADDING + shadow_offset, card_y_end + shadow_offset),
                    radius=16,
                    fill=(240, 240, 245)
                )

                # 卡片主体
                self._draw_rounded_rectangle(
                    draw,
                    (self.PADDING, card_y_start, self.IMG_WIDTH - self.PADDING, card_y_end),
                    radius=16,
                    fill=self.COLOR_CARD_BG,
                    outline=self.COLOR_CARD_OUTLINE,
                    width=2
                )

                # 绘制序号（圆形背景）
                number_x = self.PADDING + 28
                number_y = y_offset + 52
                number_radius = 20
                draw.ellipse([
                    (number_x - number_radius, number_y - number_radius),
                    (number_x + number_radius, number_y + number_radius)
                ], fill=self.COLOR_NUMBER_BG)

                # 序号文字
                number_bbox = draw.textbbox((0, 0), str(idx), font=self.font_song_name)
                number_w = number_bbox[2] - number_bbox[0]
                number_h = number_bbox[3] - number_bbox[1]
                draw.text((number_x - number_w // 2, number_y - number_h // 2), str(idx),
                         font=self.font_song_name, fill=self.COLOR_NUMBER_TEXT)

                # 下载封面图片
                cover_url = song_info.get("cover_url")
                if cover_url:
                    try:
                        async with session.get(cover_url, timeout=8) as cover_response:
                            if cover_response.status == 200:
                                cover_data = await cover_response.read()
                                cover_img = Image.open(io.BytesIO(cover_data))

                                # 制作圆形封面
                                cover_size = 90
                                mask = Image.new('L', (cover_size, cover_size), 0)
                                draw_mask = ImageDraw.Draw(mask)
                                draw_mask.ellipse([(0, 0), (cover_size, cover_size)], fill=255)

                                cover_img = cover_img.resize((cover_size, cover_size), Image.Resampling.LANCZOS)
                                cover_img.putalpha(mask)

                                # 封面阴影
                                cover_shadow_x = self.PADDING + 70 + 2
                                cover_shadow_y = y_offset + 20 + 2
                                draw.ellipse([
                                    (cover_shadow_x, cover_shadow_y),
                                    (cover_shadow_x + cover_size, cover_shadow_y + cover_size)
                                ], fill=(220, 220, 230))

                                # 封面主体
                                img.paste(cover_img, (self.PADDING + 70, y_offset + 20), cover_img)
                    except Exception as e:
                        logger.error(f"下载封面失败: {str(e)}")

                # 解析歌曲信息
                text_lines = song_info.get("text", "").split('\n')
                line_y = y_offset + 20
                text_x = self.PADDING + 185

                for line_idx, line in enumerate(text_lines):
                    if line_idx == 0:  # 歌曲名
                        draw.text((text_x, line_y), line, font=self.font_song_name, fill=self.COLOR_SONG_NAME)
                        line_y += 24  # 歌曲名后间距
                    else:  # 其他信息（歌手、专辑、ID）
                        draw.text((text_x, line_y), line, font=self.font_song_info, fill=self.COLOR_SONG_INFO)
                        line_y += 20  # 其他信息行间距

                y_offset += self.ITEM_HEIGHT

            # 绘制底部装饰区域
            footer_y_start = total_height - self.FOOTER_HEIGHT - self.PADDING
            self._draw_rounded_rectangle(
                draw,
                (self.PADDING, footer_y_start, self.IMG_WIDTH - self.PADDING, total_height - self.PADDING // 2),
                radius=16,
                fill=(255, 255, 255),
                outline=self.COLOR_CARD_OUTLINE,
                width=1
            )

            # 绘制底部装饰条
            self._draw_gradient(draw, self.IMG_WIDTH - self.PADDING * 2, 4,
                               self.COLOR_ACCENT, self.COLOR_ACCENT_SECOND)
            draw.rectangle([
                (self.PADDING, footer_y_start),
                (self.IMG_WIDTH - self.PADDING, footer_y_start + 4)
            ], fill=self.COLOR_ACCENT)

            # 绘制底部版权（两行）
            footer_text1 = "Neko云音乐 - Powered by 不穿胖次の小奶猫"
            footer_text2 = "music.cnmsb.xin | 黔ICP备2026007098号"

            # 第一行
            footer_bbox1 = draw.textbbox((0, 0), footer_text1, font=self.font_footer)
            footer_width1 = footer_bbox1[2] - footer_bbox1[0]
            footer_x1 = (self.IMG_WIDTH - footer_width1) // 2
            draw.text((footer_x1, footer_y_start + 12), footer_text1,
                     font=self.font_footer, fill=self.COLOR_FOOTER)

            # 第二行
            footer_bbox2 = draw.textbbox((0, 0), footer_text2, font=self.font_footer)
            footer_width2 = footer_bbox2[2] - footer_bbox2[0]
            footer_x2 = (self.IMG_WIDTH - footer_width2) // 2
            draw.text((footer_x2, footer_y_start + 26), footer_text2,
                     font=self.font_footer, fill=self.COLOR_FOOTER)

            # 转换为 bytes
            with io.BytesIO() as output:
                img.save(output, format='PNG', optimize=True)
                return output.getvalue()

        except Exception as e:
            logger.error(f"绘制搜索结果图片失败: {str(e)}")
            logger.error(traceback.format_exc())
            return None


@register("nekomusic", "NyaNyagulugulu", "Neko云音乐点歌插件", "1.9.1", "https://github.com/NyaNyagulugulu/astrbot_NekoMusic")
class Main(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.drawer = MusicSearchDrawer()
        # 存储每个消息的搜索结果，格式: {message_id: {"songs": [...], "platform": ..., "ts": ...}}
        # 使用消息ID而不是session_id，这样同一会话中多次搜索不会互相覆盖
        self.search_results = {}
        # 搜索结果 TTL（秒），超时自动清理
        self.SEARCH_TTL = 1800  # 30 分钟

        # 从配置文件 schema 读取默认值
        schema_path = os.path.join(os.path.dirname(__file__), "_conf_schema.json")
        schema_defaults = {}
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                for key, value in schema.items():
                    schema_defaults[key] = value.get("default")
        except Exception as e:
            logger.warning(f"读取配置 schema 失败: {e}")

        # 从配置文件读取配置，如果不存在则使用 schema 中的默认值
        self.config = config or {}
        try:
            self.use_local_server = self.config.get("use_local_server", schema_defaults.get("use_local_server", False))
            self.local_server_port = self.config.get("local_server_port", schema_defaults.get("local_server_port", 65535))
            self.audio_bitrate = int(self.config.get("audio_bitrate", schema_defaults.get("audio_bitrate", 96)))
            self.cache_expire_hours = int(self.config.get("cache_expire_hours", schema_defaults.get("cache_expire_hours", 24)))
            self.auto_play_first = self.config.get("auto_play_first", schema_defaults.get("auto_play_first", False))
            self.show_auto_play_hint = self.config.get("show_auto_play_hint", schema_defaults.get("show_auto_play_hint", True))
            self.show_play_link = self.config.get("show_play_link", schema_defaults.get("show_play_link", True))
            self.show_transcode_hint = self.config.get("show_transcode_hint", schema_defaults.get("show_transcode_hint", True))
        except Exception:
            self.use_local_server = schema_defaults.get("use_local_server", False)
            self.local_server_port = schema_defaults.get("local_server_port", 65535)
            self.audio_bitrate = int(schema_defaults.get("audio_bitrate", 96))
            self.cache_expire_hours = int(schema_defaults.get("cache_expire_hours", 24))
            self.auto_play_first = schema_defaults.get("auto_play_first", False)
            self.show_auto_play_hint = schema_defaults.get("show_auto_play_hint", True)
            self.show_play_link = schema_defaults.get("show_play_link", True)
            self.show_transcode_hint = schema_defaults.get("show_transcode_hint", True)

        # 设置API基础URL
        if self.use_local_server:
            self.api_base_url = f"http://localhost:{self.local_server_port}"
            logger.info(f"使用本机服务器模式，端口: {self.local_server_port}")
        else:
            self.api_base_url = "https://music.cnmsb.xin"
            logger.info("使用在线服务器模式")

        # 初始化本地音频缓存目录，并清理过期缓存
        self.cache_dir = os.path.join(tempfile.gettempdir(), "nekomusic_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self._startup_cache_cleanup()

    @filter.regex(r"^点歌.*")
    async def search_music(self, event: AstrMessageEvent):
        """搜索音乐"""
        msg_text = event.message_str
        keyword = msg_text[2:].strip()

        if not keyword:
            yield event.plain_result("请输入要搜索的歌曲名称,例如:点歌 Lemon")
            return

        api_url = f"{self.api_base_url}/api/music/search"
        json_data = {"query": keyword}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=json_data, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_data = self.handle_search_result(data)

                        # 获取当前消息的消息ID（用户发送的点歌消息ID）
                        user_message_id = self._get_message_id(event)
                        logger.info(f"搜索音乐，用户消息ID: {user_message_id}")

                        # 获取当前平台
                        platform = self._get_platform(event)

                        # 保存搜索结果前先清理过期条目
                        self._cleanup_expired_searches()
                        results = data.get("results")
                        if results is None:
                            results = []
                        self.search_results[user_message_id] = {
                            "songs": results,
                            "platform": platform,
                            "ts": time.time()
                        }
                        total_count = len(results)
                        logger.info(f"搜索结果已保存，用户消息ID: {user_message_id}, 歌曲数: {total_count}")

                        # 自动播放：单条结果 或 开启 auto_play_first 配置
                        if results and (total_count == 1 or self.auto_play_first):
                            song = results[0]
                            song_name = song.get("name", song.get("title", "未知歌曲"))
                            artist = song.get("artist", song.get("singer", "未知歌手"))
                            reason = "唯一命中" if total_count == 1 else "auto_play_first 已开启"
                            logger.info(f"自动播放 ({reason}): {song_name} - {artist}")
                            if self.show_auto_play_hint:
                                yield event.plain_result(f"🎵 {reason}，自动播放: {song_name} - {artist}")
                            async for result in self._play_song(song, platform, event):
                                yield result
                            return

                        # 0 条结果：简短提示，跳过图片渲染
                        if total_count == 0:
                            yield event.plain_result(f"🎵 未找到与 \"{keyword}\" 相关的歌曲")
                            return

                        # 使用 drawer 绘制图片
                        image_bytes = await self.drawer.draw_search_result(keyword, result_data, session)

                        if image_bytes:
                            # 构建提示文本（在文本中嵌入用户消息ID，用于后续匹配）
                            hint_text = f"🎵 搜索结果: {keyword}\n共找到 {result_data.get('total', 0)} 首歌曲\n💡 点击回复按钮并输入序号即可播放，例如: 1\n[MID:{user_message_id}]"

                            yield event.chain_result([
                                Comp.Plain(hint_text),
                                Comp.Image.fromBytes(image_bytes)
                            ])
                        else:
                            yield event.plain_result("图片生成失败，请稍后重试")
                    else:
                        yield event.plain_result(f"搜索失败,API 返回状态码: {response.status}")
        except Exception as e:
            logger.error(f"搜索音乐时发生错误: {str(e)}")
            yield event.plain_result(f"搜索失败: {str(e)}")

    def handle_search_result(self, data: dict) -> dict:
        """处理搜索结果"""
        result = {"songs": [], "total": 0}

        if data.get("success") and data.get("results"):
            songs = data["results"]

            # 检查 songs 是否为 None
            if songs is None:
                logger.error("API 返回的 results 为 None")
                result["songs"] = [{"cover_url": None, "text": "搜索结果为空"}]
                return result

            if not songs:
                result["songs"] = [{"cover_url": None, "text": "未找到相关歌曲"}]
                return result

            result["total"] = len(songs)

            # 显示所有歌曲
            for idx, song in enumerate(songs, 1):
                song_name = song.get("name", song.get("title", "未知歌曲"))
                artist = song.get("artist", song.get("singer", song.get("ar", "未知歌手")))
                album = song.get("album", song.get("al", "未知专辑"))
                song_id = song.get("id", "")

                # 打印完整的歌曲数据结构用于调试
                logger.info(f"歌曲 {idx} 数据: {song}")

                # 使用封面 API 获取封面图片
                cover_url = None
                if song_id:
                    cover_url = f"{self.api_base_url}/api/music/cover/{song_id}"

                # 构建歌曲信息文本
                song_text = f"{song_name}\n"
                song_text += f"歌手: {artist}\n"
                song_text += f"专辑: {album}\n"
                if song_id:
                    song_text += f"平台音乐ID: {song_id}"

                result["songs"].append({
                    "cover_url": cover_url,
                    "text": song_text
                })
        else:
            result["songs"] = [{"cover_url": None, "text": f"搜索失败: {data.get('message', '未知错误')}"}]

        return result

    def _get_platform(self, event: AstrMessageEvent) -> str:
        """获取当前平台类型"""
        logger.info(f"_get_platform 开始执行，event 类型: {type(event)}")

        # 尝试从事件中获取平台信息
        logger.info(f"检查 event.platform: {hasattr(event, 'platform')}")
        if hasattr(event, 'platform'):
            platform = event.platform
            logger.info(f"event.platform 类型: {type(platform)}, 值: {platform}")
            # 处理 PlatformMetadata 对象
            if hasattr(platform, 'name'):
                result = platform.name.lower()
                logger.info(f"从 platform.name 获取到: {result}")
                return result
            elif isinstance(platform, str):
                result = platform.lower()
                logger.info(f"从 platform 字符串获取到: {result}")
                return result

        # 尝试从 message_obj 中获取
        logger.info(f"检查 event.message_obj: {hasattr(event, 'message_obj')}")
        if hasattr(event, 'message_obj'):
            logger.info(f"检查 event.message_obj.platform: {hasattr(event.message_obj, 'platform')}")
            if hasattr(event.message_obj, 'platform'):
                platform = event.message_obj.platform
                logger.info(f"message_obj.platform 类型: {type(platform)}, 值: {platform}")
                # 处理 PlatformMetadata 对象
                if hasattr(platform, 'name'):
                    result = platform.name.lower()
                    logger.info(f"从 message_obj.platform.name 获取到: {result}")
                    return result
                elif isinstance(platform, str):
                    result = platform.lower()
                    logger.info(f"从 message_obj.platform 字符串获取到: {result}")
                    return result

        # 默认返回 unknown
        logger.info("使用默认平台: unknown")
        return 'unknown'

    def _get_message_id(self, event: AstrMessageEvent) -> str:
        """获取消息ID"""
        # 尝试从 message_obj 中获取 message_id
        if hasattr(event, 'message_obj') and hasattr(event.message_obj, 'message_id'):
            message_id = event.message_obj.message_id
            logger.info(f"从 message_obj.message_id 获取到消息ID: {message_id}")
            return str(message_id)

        # 尝试从 message 对象中获取
        if hasattr(event, 'message_obj') and hasattr(event.message_obj, 'message'):
            components = event.message_obj.message
            # 查找是否有包含 message_id 的组件
            for comp in components:
                if hasattr(comp, 'message_id'):
                    logger.info(f"从组件中获取到消息ID: {comp.message_id}")
                    return str(comp.message_id)

        # 如果都获取不到，返回 session_id 作为备用
        logger.warning(f"无法获取消息ID，使用 session_id 作为备用: {event.session_id}")
        return str(event.session_id)

    @filter.regex(r"^/?\s*\d+$")
    async def play_music(self, event: AstrMessageEvent):
        """播放音乐（通过序号）"""
        logger.info(f"===== play_music 被触发 =====")
        logger.info(f"原始 message_str: {repr(event.message_str)}")
        logger.info(f"event 类型: {type(event)}")
        logger.info(f"event.message_str 类型: {type(event.message_str)}")

        msg_text = event.message_str.strip()
        logger.info(f"去除空白后的 message_str: {repr(msg_text)}")

        # 去除可能的前导斜杠
        msg_text = msg_text.lstrip('/')
        logger.info(f"去除斜杠后的 message_str: {repr(msg_text)}")

        # 去除所有空白字符
        msg_text = msg_text.strip()
        logger.info(f"去除所有空白后的 message_str: {repr(msg_text)}")

        # 检查是否是纯数字
        if not msg_text.isdigit():
            logger.info(f"消息不是纯数字: {repr(msg_text)}，跳过")
            return

        try:
            logger.info("开始调用 _get_platform")
            platform = self._get_platform(event)
            logger.info(f"当前平台: {platform}")
        except Exception as e:
            logger.error(f"_get_platform 调用失败: {str(e)}")
            logger.error(traceback.format_exc())
            platform = 'telegram'  # Telegram 平台默认值

        # Discord 平台特殊处理：尝试从事件对象中获取引用消息
        reply_msg = None
        reply_message_id = None

        if platform == 'discord':
            logger.info("Discord 平台：尝试从事件对象获取引用消息")
            # Discord 平台可能在 event 对象中存储引用消息信息
            # 尝试多种可能的属性
            if hasattr(event, 'message_obj'):
                message_obj = event.message_obj

                # 方法1: 检查 message_obj 是否有 message_reference 属性
                if hasattr(message_obj, 'message_reference'):
                    logger.info(f"找到 message_reference: {message_obj.message_reference}")
                    msg_ref = message_obj.message_reference
                    if hasattr(msg_ref, 'message_id'):
                        reply_message_id = str(msg_ref.message_id)
                        logger.info(f"从 message_reference.message_id 获取到: {reply_message_id}")

                # 方法2: 检查 message_obj 是否有 raw_message 属性（原始 Discord 消息对象）
                if not reply_message_id and hasattr(message_obj, 'raw_message'):
                    raw_msg = message_obj.raw_message
                    logger.info(f"找到 raw_message: {type(raw_msg)}")
                    if hasattr(raw_msg, 'reference') and raw_msg.reference:
                        if hasattr(raw_msg.reference, 'message_id'):
                            reply_message_id = str(raw_msg.reference.message_id)
                            logger.info(f"从 raw_message.reference.message_id 获取到: {reply_message_id}")

                # 方法3: 检查 message_obj 是否有 referenced_message_id 属性
                if not reply_message_id and hasattr(message_obj, 'referenced_message_id'):
                    reply_message_id = str(message_obj.referenced_message_id)
                    logger.info(f"从 referenced_message_id 获取到: {reply_message_id}")

                # 方法4: 检查 message_obj.message 中的 Reply 组件（有些 Discord 适配器可能使用）
                if not reply_message_id and hasattr(message_obj, 'message'):
                    components = message_obj.message
                    if components:
                        for comp in components:
                            if hasattr(comp, 'type') and comp.type == 'Reply':
                                reply_msg = comp
                                logger.info(f"从消息链中找到 Reply 组件: {reply_msg}")
                                break

        # 非 Discord 平台：从消息链中查找 Reply 组件
        else:
            logger.info(f"检查 event 是否有 message_obj: {hasattr(event, 'message_obj')}")
            if hasattr(event, 'message_obj'):
                logger.info(f"检查 message_obj 是否有 message: {hasattr(event.message_obj, 'message')}")
                if hasattr(event.message_obj, 'message'):
                    components = event.message_obj.message
                    logger.info(f"消息链组件数量: {len(components) if components else 0}")
                    logger.info(f"消息链组件类型: {[type(c).__name__ for c in components] if components else []}")

                    # 遍历消息链查找 Reply 组件
                    for idx, comp in enumerate(components):
                        logger.info(f"组件 {idx}: type={type(comp).__name__}, hasattr type={hasattr(comp, 'type')}")
                        if hasattr(comp, 'type'):
                            logger.info(f"组件 {idx} type={comp.type}")
                            if comp.type == 'Reply':
                                reply_msg = comp
                                logger.info(f"找到 Reply 组件: {reply_msg}")
                                break

        # 如果没有找到引用消息，跳过播放
        if not reply_msg and not reply_message_id:
            logger.info("没有引用消息，跳过播放")
            return

        # 检查引用的消息发送者是否是机器人自己
        # Telegram 平台: sender_id 是数字, bot_id 可能是字符串名称
        # QQ 平台: 两者都是数字字符串
        # Discord 平台: 直接使用 reply_message_id，不需要验证发送者（因为 reply_message_id 是机器人发送的消息ID）

        if platform != 'discord' and reply_msg:
            # 非 Discord 平台需要验证发送者
            if hasattr(reply_msg, 'sender_id'):
                reply_sender_id = reply_msg.sender_id
                bot_id = event.get_self_id()

                # Telegram 特殊处理: 检查 Reply 组件的 sender_nickname 是否与 bot_id 匹配
                if platform == 'telegram':
                    # 在 Telegram 上,bot_id 可能是机器人名称(如 'nekoMcServer_bot')
                    # 检查 Reply 组件是否有 sender_nickname 属性
                    if hasattr(reply_msg, 'sender_nickname'):
                        reply_sender_name = reply_msg.sender_nickname
                        if str(reply_sender_name) != str(bot_id):
                            logger.info(f"Telegram: 引用消息发送者昵称: {reply_sender_name}, 机器人ID: {bot_id}，不匹配，跳过播放")
                            return
                    else:
                        # 如果没有 sender_nickname,尝试其他方式验证
                        logger.info(f"Telegram: Reply 组件缺少 sender_nickname，跳过验证")
                else:
                    # QQ 平台或其他平台: 直接比较 ID
                    if str(reply_sender_id) != str(bot_id):
                        logger.info(f"引用的消息发送者: {reply_sender_id}, 机器人ID: {bot_id}，不匹配，跳过播放")
                        return
            else:
                logger.info("reply_msg 没有 sender_id 属性，跳过播放")
                return

        index = int(msg_text) - 1  # 转换为 0-based 索引
        logger.info(f"用户输入序号: {msg_text}, 转换后索引: {index}")

        # Discord 平台：尝试从引用消息的内容中获取用户消息 ID
        # 非 Discord 平台：从引用消息中获取被引用消息的消息ID
        if platform == 'discord':
            # Discord 平台：reply_message_id 是引用消息 ID（机器人发送的搜索结果消息）
            # 我们需要从引用消息的文本中提取用户消息 ID
            logger.info(f"Discord 平台：尝试从引用消息获取用户消息 ID")

            # 尝试从 message_obj 中获取引用消息的内容
            user_message_id = None
            if hasattr(event, 'message_obj') and hasattr(event.message_obj, 'message_obj'):
                # Discord 平台可能有 referenced_message 属性
                if hasattr(event.message_obj.message_obj, 'referenced_message'):
                    ref_msg = event.message_obj.message_obj.referenced_message
                    if hasattr(ref_msg, 'content'):
                        mid_match = re.search(r'\[MID:(\d+)\]', ref_msg.content)
                        if mid_match:
                            user_message_id = mid_match.group(1)
                            logger.info(f"从引用消息内容中提取到用户消息ID: {user_message_id}")

            if not user_message_id:
                # 尝试其他方式获取引用消息内容
                if hasattr(event, 'message_obj') and hasattr(event.message_obj, 'raw_message'):
                    raw_msg = event.message_obj.raw_message
                    if hasattr(raw_msg, 'reference') and raw_msg.reference:
                        if hasattr(raw_msg.reference, 'resolved') and raw_msg.reference.resolved:
                            ref_msg = raw_msg.reference.resolved
                            if hasattr(ref_msg, 'content'):
                                mid_match = re.search(r'\[MID:(\d+)\]', ref_msg.content)
                                if mid_match:
                                    user_message_id = mid_match.group(1)
                                    logger.info(f"从 raw_message.reference.resolved.content 中提取到用户消息ID: {user_message_id}")

            if not user_message_id:
                logger.error(f"无法从引用消息中提取用户消息 ID")
                return

            logger.info(f"Discord 平台：使用用户消息 ID = {user_message_id}")
            reply_message_id = user_message_id
        else:
            # 从引用消息中获取被引用消息的消息ID
            reply_message_id = None

            # 方法1: 从引用消息的文本中提取 [MID:xxx] 格式的消息ID
            if hasattr(reply_msg, 'text'):
                mid_match = re.search(r'\[MID:(\d+)\]', reply_msg.text)
                if mid_match:
                    reply_message_id = mid_match.group(1)
                    logger.info(f"从引用消息文本中提取到消息ID: {reply_message_id}")

            # 方法2: 如果没有找到，尝试直接使用Reply组件的id（这个是机器人回复的消息ID）
            if not reply_message_id and hasattr(reply_msg, 'id'):
                reply_message_id = str(reply_msg.id)
                logger.info(f"从 Reply 组件 id 获取到消息ID: {reply_message_id}")

            # 方法3: 尝试从message_id获取
            if not reply_message_id and hasattr(reply_msg, 'message_id'):
                reply_message_id = str(reply_msg.message_id)
                logger.info(f"从 Reply 组件 message_id 获取到消息ID: {reply_message_id}")

            if not reply_message_id:
                logger.error("无法从 Reply 组件获取消息ID")
                return

        logger.info(f"已保存的搜索结果消息ID: {list(self.search_results.keys())}")

        # 检查是否有匹配的搜索结果
        if reply_message_id not in self.search_results:
            logger.info(f"消息ID {reply_message_id} 没有对应的搜索结果，跳过播放")
            return

        search_data = self.search_results[reply_message_id]
        songs = search_data["songs"]
        logger.info(f"找到 {len(songs)} 首歌曲")

        # 检查索引是否有效
        if index < 0 or index >= len(songs):
            yield event.plain_result(f"序号无效，请输入 1-{len(songs)} 之间的数字")
            return

        # 获取歌曲信息并委托给 _play_song
        logger.info(f"准备播放第 {index + 1} 首歌曲")
        song = songs[index]
        async for result in self._play_song(song, platform, event):
            yield result
        return

    async def _play_song(self, song: dict, platform: str, event: AstrMessageEvent):
        """播放单首歌曲的完整流程：链接→预检→缓存→转码→发送。

        从 search_music（自动播放）和 play_music（序号播放）共享调用。
        """
        song_name = song.get("name", song.get("title", "未知歌曲"))
        song_id = song.get("id", "")

        if not song_id:
            yield event.plain_result("该歌曲没有有效的 ID，无法播放")
            return

        # 生成播放链接
        play_url = f"https://music.cnmsb.xin/detail/{song_id}"
        audio_url = f"{self.api_base_url}/api/music/file/{song_id}"

        # 先返回播放链接
        send_type = "文件" if platform == 'discord' else "语音"
        if self.show_play_link:
            yield event.chain_result([
                Comp.Plain(f"🎶 Neko云音乐。听见好音乐\n🔗 {play_url}\n🎵 正在发送音乐{send_type}，请稍后\n平台内均为无损音质，发送可能较慢，请耐心等待..."),
            ])

        # 下载音频并发送语音（流式管道转码 + 本地缓存）
        try:
            async with aiohttp.ClientSession() as session:
                # 第一步：HEAD 预检文件大小，按转码后估算判断
                head_size_mb = await self._head_check_size(session, audio_url, song_id, song_name)
                if head_size_mb is not None:
                    # 安全上限：原始文件超大 (>500MB) 直接拒绝
                    if head_size_mb > 500:
                        yield event.plain_result(
                            f"⚠️ 音频文件过大 ({head_size_mb:.1f}MB)，不支持下载\n"
                            f"请直接点击播放链接收听: {play_url}"
                        )
                        return

                    # 按目标码率估算转码后 MP3 大小（假设 FLAC 平均 ~900kbps）
                    est_mp3_mb = head_size_mb * self.audio_bitrate / 900
                    platform_max = self._get_platform_max_size(platform)
                    if est_mp3_mb > platform_max:
                        yield event.plain_result(
                            f"⚠️ 原始文件 {head_size_mb:.1f}MB，预计转码后 ~{est_mp3_mb:.1f}MB，"
                            f"仍超过平台限制 ({platform_max}MB)\n"
                            f"请直接点击播放链接收听: {play_url}"
                        )
                        return
                    logger.info(
                        f"原始 {head_size_mb:.1f}MB → 预估 MP3 {est_mp3_mb:.1f}MB "
                        f"(码率 {self.audio_bitrate}kbps, 平台限制 {platform_max}MB)"
                    )

                # 第二步：检查本地缓存
                cache_path = self._get_cache_path(song_id)
                if os.path.exists(cache_path):
                    cache_size_mb = os.path.getsize(cache_path) / (1024 * 1024)
                    logger.info(f"命中本地缓存: {cache_path} ({cache_size_mb:.2f}MB)")

                    max_size_mb = self._get_platform_max_size(platform)
                    if cache_size_mb > max_size_mb:
                        logger.info(f"缓存文件 ({cache_size_mb:.2f}MB) 超过平台限制 ({max_size_mb}MB)，重新压缩")
                        temp_path = await self._recompress_file(
                            cache_path, song_id, song_name, max_size_mb
                        )
                        if temp_path is None:
                            yield event.plain_result(f"❌ 压缩失败，请直接点击播放链接收听: {play_url}")
                            return
                        send_path = temp_path
                        needs_cleanup = True
                    else:
                        send_path = cache_path
                        needs_cleanup = False
                else:
                    # 第三步：缓存未命中 → 流式下载 + ffmpeg 管道转码
                    logger.info(f"缓存未命中，开始流式下载并转码 (song_id={song_id})")
                    if self.show_transcode_hint:
                        yield event.plain_result("🎵 正在下载并转码音频，请稍候...")

                    temp_path = await self._stream_download_and_compress(
                        session, audio_url, song_id, song_name, platform
                    )
                    if temp_path is None:
                        yield event.plain_result(f"❌ 音频处理失败，请直接点击播放链接收听: {play_url}")
                        return

                    # 处理后的文件移动到缓存目录
                    try:
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        shutil.move(temp_path, cache_path)
                        logger.info(f"已缓存: {cache_path}")
                        send_path = cache_path
                        needs_cleanup = False
                    except Exception as move_err:
                        logger.warning(f"移动缓存失败，直接发送临时文件: {move_err}")
                        send_path = temp_path
                        needs_cleanup = True

                # 第四步：发送音频
                logger.info(f"开始发送音频到 {platform} 平台")
                filename = os.path.basename(send_path)

                try:
                    if platform == 'discord':
                        yield event.chain_result([
                            Comp.File(name=filename, file=send_path)
                        ])
                        logger.info("Discord 音频文件发送成功")
                    else:
                        yield event.chain_result([
                            Comp.Record(file=send_path)
                        ])
                        logger.info("语音发送成功")
                except Exception as send_error:
                    logger.error(f"发送失败: {str(send_error)}")
                    yield event.plain_result(f"⚠️ 发送失败，请直接点击播放链接收听: {play_url}")

                # 仅清理临时文件（缓存文件保留）
                if needs_cleanup:
                    asyncio.create_task(self._safe_cleanup(send_path, delay=5.0))

        except asyncio.TimeoutError:
            logger.error("下载音频超时")
            yield event.plain_result(f"❌ 下载音频超时，请直接点击播放链接收听: {play_url}")
        except Exception as e:
            logger.error(f"下载或发送音频时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            yield event.plain_result(f"❌ 发送音乐失败: {str(e)}\n请直接点击播放链接收听: {play_url}")


    # ─── 以下为内部辅助方法 ───

    def _cleanup_expired_searches(self):
        """清理过期的搜索结果（超过 SEARCH_TTL 秒未使用的条目）。"""
        now = time.time()
        expired = [mid for mid, v in self.search_results.items()
                    if now - v.get("ts", 0) > self.SEARCH_TTL]
        for mid in expired:
            del self.search_results[mid]
        if expired:
            logger.info(f"清理了 {len(expired)} 条过期搜索结果")

    async def _head_check_size(self, session: aiohttp.ClientSession,
                               audio_url: str, song_id, song_name: str) -> float | None:
        """HEAD 预检远端文件大小，返回 MB 数；失败返回 None。"""
        try:
            async with session.head(audio_url, timeout=15) as resp:
                cl = resp.headers.get("Content-Length")
                if cl:
                    size_mb = int(cl) / (1024 * 1024)
                    logger.info(f"HEAD 预检: {song_name} (id={song_id}) = {size_mb:.2f}MB")
                    return size_mb
        except Exception as e:
            logger.warning(f"HEAD 预检失败: {e}")
        return None

    def _get_cache_path(self, song_id) -> str:
        """获取指定 song_id 的本地缓存文件路径。"""
        return os.path.join(self.cache_dir, f"{song_id}.mp3")

    def _get_platform_max_size(self, platform: str) -> int:
        """返回平台允许的最大音频文件大小（MB）。"""
        if platform == 'discord':
            return 10
        elif platform == 'telegram':
            return 50
        else:
            return 10  # QQ / aiocqhttp / unknown

    async def _stream_download_and_compress(self, session: aiohttp.ClientSession,
                                             audio_url: str, song_id,
                                             song_name: str, platform: str) -> str | None:
        """流式下载 FLAC 并通过 ffmpeg 管道实时转码为 MP3。

        边下边压，磁盘上只存压缩后的 MP3，避免 50MB FLAC 暂存。
        返回临时文件路径，失败返回 None。
        """
        # 检查 ffmpeg 是否可用
        if not shutil.which('ffmpeg'):
            logger.error("ffmpeg 未安装，无法转码")
            return None

        max_size_mb = self._get_platform_max_size(platform)
        temp_path = os.path.join(tempfile.gettempdir(),
                                 f"nekomusic_stream_{song_id}_{int(time.time())}.mp3")

        try:
            # 启动 ffmpeg：从 stdin 读取，输出 MP3 到文件
            ffmpeg_cmd = [
                'ffmpeg', '-i', 'pipe:0',          # stdin 接收原始音频
                '-b:a', f'{self.audio_bitrate}k',   # 目标码率
                '-ar', '44100', '-ac', '2',
                '-f', 'mp3', temp_path,
                '-y',
            ]
            proc = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 流式下载 → 直接喂给 ffmpeg stdin
            async with session.get(audio_url, timeout=120) as audio_resp:
                if audio_resp.status != 200:
                    logger.error(f"下载音频失败,状态码: {audio_resp.status}")
                    proc.kill()
                    return None

                downloaded = 0
                async for chunk in audio_resp.content.iter_chunked(65536):
                    proc.stdin.write(chunk)
                    await proc.stdin.drain()
                    downloaded += len(chunk)

            proc.stdin.close()
            await proc.wait()

            if proc.returncode != 0:
                stderr_text = (await proc.stderr.read()).decode('utf-8', errors='replace')
                logger.error(f"ffmpeg 转码失败 (returncode={proc.returncode}): {stderr_text[:500]}")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None

            out_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            logger.info(f"流式转码完成: {downloaded / (1024*1024):.1f}MB FLAC → {out_size_mb:.2f}MB MP3 "
                        f"({song_name}, id={song_id})")

            # 如果压缩后仍然超过平台限制，尝试降码率再压一次
            if out_size_mb > max_size_mb:
                logger.info(f"压缩后 ({out_size_mb:.2f}MB) 仍超平台限制 ({max_size_mb}MB)，降码率重试")
                retry_path = await self._recompress_file(temp_path, song_id, song_name, max_size_mb)
                if retry_path:
                    os.unlink(temp_path)
                    return retry_path
                # 降码率失败，原文件继续用（让它尝试发送）

            return temp_path

        except Exception as e:
            logger.error(f"流式下载转码异常: {e}")
            logger.error(traceback.format_exc())
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            return None

    async def _recompress_file(self, src_path: str, song_id,
                                song_name: str, max_size_mb: int) -> str | None:
        """对已有文件用更低码率重新压缩，返回新文件路径。"""
        if not shutil.which('ffmpeg'):
            return None

        # 逐次降码率：当前码率 → 64k → 32k
        fallback_bitrates = [64, 32]
        for br in fallback_bitrates:
            if br >= self.audio_bitrate:
                continue
            dst_path = os.path.join(tempfile.gettempdir(),
                                    f"nekomusic_recomp_{song_id}_{br}k.mp3")
            try:
                proc = await asyncio.create_subprocess_exec(
                    'ffmpeg', '-i', src_path,
                    '-b:a', f'{br}k', '-ar', '22050', '-ac', '1',
                    '-f', 'mp3', dst_path, '-y',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.wait()
                if proc.returncode == 0:
                    new_size = os.path.getsize(dst_path) / (1024 * 1024)
                    logger.info(f"降码率重压: {song_name} → {br}kbps = {new_size:.2f}MB")
                    return dst_path
                else:
                    if os.path.exists(dst_path):
                        os.unlink(dst_path)
            except Exception as e:
                logger.warning(f"降码率重压失败 ({br}k): {e}")
                if os.path.exists(dst_path):
                    try:
                        os.unlink(dst_path)
                    except Exception:
                        pass
        return None

    async def _safe_cleanup(self, path: str, delay: float = 5.0):
        """延迟删除临时文件，确保 AstrBot 已完成读取。"""
        try:
            await asyncio.sleep(delay)
            if os.path.exists(path):
                os.unlink(path)
                logger.info(f"✅ 已清理临时文件: {path}")
        except Exception as e:
            logger.warning(f"⚠️ 清理临时文件失败（可忽略）: {e}")

    def _startup_cache_cleanup(self):
        """启动时清理超过 cache_expire_hours 小时的缓存文件。"""
        try:
            now = time.time()
            cutoff = now - self.cache_expire_hours * 3600
            cleaned = 0
            for fname in os.listdir(self.cache_dir):
                fpath = os.path.join(self.cache_dir, fname)
                try:
                    if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                        os.unlink(fpath)
                        cleaned += 1
                except Exception:
                    pass
            if cleaned:
                logger.info(f"启动缓存清理: 删除了 {cleaned} 个过期文件 (>{self.cache_expire_hours}h)")
        except Exception as e:
            logger.warning(f"缓存清理出错: {e}")