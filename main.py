import io
import os
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
        FONT_PATH_REGULAR := os.path.join(os.path.dirname(__file__), "DouyinSansBold.otf"),
        FONT_PATH_BOLD := FONT_PATH_REGULAR,
    ]

    # 颜色定义
    COLOR_BG_START = (248, 250, 255)
    COLOR_BG_END = (255, 252, 248)
    COLOR_HEADER = (0, 40, 100)
    COLOR_SUBTITLE = (80, 80, 80)
    COLOR_SONG_NAME = (0, 60, 130)
    COLOR_SONG_INFO = (70, 70, 70)
    COLOR_CARD_BG = (255, 255, 255)
    COLOR_CARD_OUTLINE = (220, 225, 235)
    COLOR_ACCENT = (0, 90, 180)
    COLOR_FOOTER = (100, 100, 100)

    # 布局尺寸
    IMG_WIDTH = 800
    PADDING = 25
    HEADER_HEIGHT = 100
    ITEM_HEIGHT = 120
    FOOTER_HEIGHT = 40

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
                    import traceback
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
            import traceback
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
        """绘制搜索结果图片"""
        try:
            songs = result_data.get("songs", [])
            total = result_data.get("total", 0)

            # 计算总高度
            total_height = self.HEADER_HEIGHT + len(songs) * self.ITEM_HEIGHT + self.FOOTER_HEIGHT + self.PADDING * 3

            # 创建图片
            img = Image.new('RGB', (self.IMG_WIDTH, total_height), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)

            # 绘制渐变背景
            self._draw_gradient(draw, self.IMG_WIDTH, total_height, self.COLOR_BG_START, self.COLOR_BG_END)

            # 绘制顶部装饰条
            draw.rectangle([(0, 0), (self.IMG_WIDTH, 8)], fill=self.COLOR_ACCENT)

            # 绘制标题
            title_text = "🎵 音乐搜索"
            draw.text((self.PADDING, 25), title_text, font=self.font_title, fill=self.COLOR_HEADER)

            # 绘制关键词和结果数
            keyword_text = f"关键词: {keyword}"
            keyword_bbox = draw.textbbox((0, 0), keyword_text, font=self.font_subtitle)
            keyword_width = keyword_bbox[2] - keyword_bbox[0]
            draw.text((self.IMG_WIDTH - self.PADDING - keyword_width, 32), keyword_text,
                     font=self.font_subtitle, fill=self.COLOR_SUBTITLE)

            result_text = f"共找到 {total} 首歌曲"
            draw.text((self.PADDING, 70), result_text, font=self.font_subtitle, fill=self.COLOR_SUBTITLE)

            # 绘制分割线
            draw.line([(self.PADDING, self.HEADER_HEIGHT - 5), (self.IMG_WIDTH - self.PADDING, self.HEADER_HEIGHT - 5)],
                     fill=(200, 200, 200), width=2)

            # 绘制每首歌曲
            y_offset = self.HEADER_HEIGHT
            for idx, song_info in enumerate(songs, 1):
                # 绘制卡片背景（交替颜色）
                card_bg = self.COLOR_CARD_BG if idx % 2 == 1 else (248, 250, 255)
                self._draw_rounded_rectangle(
                    draw,
                    (self.PADDING, y_offset + 5, self.IMG_WIDTH - self.PADDING, y_offset + self.ITEM_HEIGHT - 5),
                    radius=10,
                    fill=card_bg,
                    outline=self.COLOR_CARD_OUTLINE,
                    width=1
                )

                # 绘制序号
                draw.text((self.PADDING + 15, y_offset + 15), str(idx),
                         font=self.font_song_name, fill=self.COLOR_ACCENT)

                # 下载封面图片
                cover_url = song_info.get("cover_url")
                if cover_url:
                    try:
                        async with session.get(cover_url, timeout=8) as cover_response:
                            if cover_response.status == 200:
                                cover_data = await cover_response.read()
                                cover_img = Image.open(io.BytesIO(cover_data))
                                cover_img = cover_img.resize((110, 110), Image.Resampling.LANCZOS)
                                img.paste(cover_img, (self.PADDING + 55, y_offset + 10))
                    except Exception as e:
                        logger.error(f"下载封面失败: {str(e)}")

                # 解析歌曲信息
                text_lines = song_info.get("text", "").split('\n')
                line_y = y_offset + 15
                text_x = self.PADDING + 180

                for line_idx, line in enumerate(text_lines):
                    if line_idx == 0:  # 歌曲名
                        draw.text((text_x, line_y), line, font=self.font_song_name, fill=self.COLOR_SONG_NAME)
                    else:  # 其他信息
                        draw.text((text_x, line_y), line, font=self.font_song_info, fill=self.COLOR_SONG_INFO)
                    line_y += 24

                y_offset += self.ITEM_HEIGHT

            # 绘制底部版权
            footer_text = "Neko云音乐 - Powered by AstrBot"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=self.font_footer)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (self.IMG_WIDTH - footer_width) // 2
            draw.text((footer_x, total_height - self.FOOTER_HEIGHT + 10), footer_text,
                     font=self.font_footer, fill=self.COLOR_FOOTER)

            # 转换为 bytes
            with io.BytesIO() as output:
                img.save(output, format='PNG', optimize=True)
                return output.getvalue()

        except Exception as e:
            logger.error(f"绘制搜索结果图片失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None


@register("nekomusic", "NyaNyagulugulu", "Neko云音乐点歌插件", "1.2.0", "https://github.com/NyaNyagulugulu/astrbot_NekoMusic")
class Main(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.drawer = MusicSearchDrawer()

    @filter.regex(r"^点歌.*")
    async def search_music(self, event: AstrMessageEvent):
        """搜索音乐"""
        msg_text = event.message_str
        keyword = msg_text[2:].strip()

        if not keyword:
            yield event.plain_result("请输入要搜索的歌曲名称,例如:点歌 Lemon")
            return

        api_url = "https://music.cnmsb.xin/api/music/search"
        json_data = {"query": keyword}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=json_data, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_data = self.handle_search_result(data)

                        # 使用 drawer 绘制图片
                        image_bytes = await self.drawer.draw_search_result(keyword, result_data, session)

                        if image_bytes:
                            yield event.chain_result([
                                Comp.Plain(f"🎵 搜索结果: {keyword}\n共找到 {result_data.get('total', 0)} 首歌曲"),
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
            
            if not songs:
                result["songs"] = [{"cover_url": None, "text": "未找到相关歌曲"}]
                return result
            
            result["total"] = len(songs)
            
            # 显示前 5 首歌曲
            for idx, song in enumerate(songs[:5], 1):
                song_name = song.get("name", song.get("title", "未知歌曲"))
                artist = song.get("artist", song.get("singer", song.get("ar", "未知歌手")))
                album = song.get("album", song.get("al", "未知专辑"))
                song_id = song.get("id", "")
                
                # 使用封面 API 获取封面图片
                cover_url = None
                if song_id:
                    cover_url = f"https://music.cnmsb.xin/api/music/cover/{song_id}"
                
                # 构建歌曲信息文本
                song_text = f"🎶 {song_name}\n"
                song_text += f"🎤 歌手: {artist}\n"
                song_text += f"💿 专辑: {album}\n"
                if song_id:
                    song_text += f"🆔 ID: {song_id}"
                
                result["songs"].append({
                    "cover_url": cover_url,
                    "text": song_text
                })
        else:
            result["songs"] = [{"cover_url": None, "text": f"搜索失败: {data.get('message', '未知错误')}"}]
        
        return result