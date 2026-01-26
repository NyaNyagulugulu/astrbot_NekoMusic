import aiohttp
import asyncio
import io
from PIL import Image, ImageDraw, ImageFont
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp


@register("nekomusic", "NyaNyagulugulu", "Neko云音乐点歌插件", "1.2.0", "https://github.com/NyaNyagulugulu/astrbot_NekoMusic")
class Main(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.regex(r"^点歌.*")
    async def search_music(self, event: AstrMessageEvent):
        """搜索音乐"""
        # 获取消息文本
        msg_text = event.message_str

        # 提取搜索关键词
        keyword = msg_text[2:].strip()

        if not keyword:
            yield event.plain_result("请输入要搜索的歌曲名称,例如:点歌 Lemon")
            return

        # 调用 API 搜索音乐
        api_url = "https://music.cnmsb.xin/api/music/search"
        json_data = {"query": keyword}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=json_data, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        result_data = self.handle_search_result(data)

                        # 合成图片
                        image_bytes = await self.create_search_result_image(keyword, result_data, session)

                        if image_bytes:
                            yield event.chain_result([
                                Comp.Plain(f"🎵 搜索结果: {keyword}\n共找到 {result_data.get('total', 0)} 首歌曲"),
                                Comp.Image.fromBase64(image_bytes)
                            ])
                        else:
                            yield event.plain_result("图片生成失败，请稍后重试")
                    else:
                        yield event.plain_result(f"搜索失败,API 返回状态码: {response.status}")
        except asyncio.TimeoutError:
            yield event.plain_result("搜索超时,请稍后重试")
        except Exception as e:
            logger.error(f"搜索音乐时发生错误: {str(e)}")
            yield event.plain_result(f"搜索失败: {str(e)}")

    async def create_search_result_image(self, keyword: str, result_data: dict, session) -> str:
        """创建搜索结果图片"""
        try:
            # 设置图片尺寸
            img_width = 600
            padding = 20
            item_height = 120
            header_height = 80

            # 计算总高度
            total_items = len(result_data.get("songs", []))
            total_height = header_height + (total_items * item_height) + padding * 2

            # 创建白色背景图片
            img = Image.new('RGB', (img_width, total_height), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)

            # 尝试加载中文字体，如果失败使用默认字体
            try:
                # Windows 常见中文字体
                font_paths = [
                    "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                    "C:/Windows/Fonts/simhei.ttf",  # 黑体
                    "C:/Windows/Fonts/simsun.ttc",  # 宋体
                ]
                title_font = None
                text_font = None

                for font_path in font_paths:
                    try:
                        title_font = ImageFont.truetype(font_path, 28)
                        text_font = ImageFont.truetype(font_path, 18)
                        break
                    except:
                        continue

                if title_font is None:
                    title_font = ImageFont.load_default()
                    text_font = ImageFont.load_default()
            except:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()

            # 绘制标题
            title_text = f"🎵 搜索结果: {keyword}"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (img_width - title_width) // 2
            draw.text((title_x, padding), title_text, fill=(50, 50, 50), font=title_font)

            subtitle_text = f"共找到 {result_data.get('total', 0)} 首歌曲"
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=text_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (img_width - subtitle_width) // 2
            draw.text((subtitle_x, padding + 40), subtitle_text, fill=(100, 100, 100), font=text_font)

            # 绘制分割线
            draw.line([(padding, header_height - 10), (img_width - padding, header_height - 10)], fill=(200, 200, 200), width=2)

            # 下载封面并绘制每首歌曲信息
            y_offset = header_height
            for idx, song_info in enumerate(result_data.get("songs", []), 1):
                # 绘制序号
                draw.text((padding, y_offset + 10), f"{idx}.", fill=(50, 50, 50), font=title_font)

                # 下载封面图片
                cover_url = song_info.get("cover_url")
                if cover_url:
                    try:
                        async with session.get(cover_url, timeout=5) as cover_response:
                            if cover_response.status == 200:
                                cover_data = await cover_response.read()
                                cover_img = Image.open(io.BytesIO(cover_data))
                                cover_img = cover_img.resize((100, 100), Image.Resampling.LANCZOS)
                                img.paste(cover_img, (50, y_offset + 10))
                    except:
                        pass

                # 绘制歌曲信息
                text_x = 160
                text_lines = song_info.get("text", "").split('\n')
                line_y = y_offset + 10

                for line in text_lines:
                    draw.text((text_x, line_y), line, fill=(80, 80, 80), font=text_font)
                    line_y += 25

                # 绘制分割线
                y_offset += item_height
                if idx < total_items:
                    draw.line([(padding, y_offset), (img_width - padding, y_offset)], fill=(240, 240, 240), width=1)

            # 将图片转换为 base64
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            import base64
            return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        except Exception as e:
            logger.error(f"创建搜索结果图片时发生错误: {str(e)}")
            return None

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