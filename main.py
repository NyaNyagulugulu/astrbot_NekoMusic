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
            img_width = 800
            padding = 25
            item_height = 130
            header_height = 100
            footer_height = 30

            # 计算总高度
            total_items = len(result_data.get("songs", []))
            total_height = header_height + (total_items * item_height) + footer_height + padding * 3

            # 创建渐变背景图片
            img = Image.new('RGB', (img_width, total_height), color=(245, 248, 255))
            draw = ImageDraw.Draw(img)

            # 尝试加载中文字体
            try:
                # Windows 常见中文字体，添加更多候选字体
                font_paths = [
                    "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
                    "C:/Windows/Fonts/msyhbd.ttc",    # 微软雅黑粗体
                    "C:/Windows/Fonts/simhei.ttf",    # 黑体
                    "C:/Windows/Fonts/simsun.ttc",    # 宋体
                    "C:/Windows/Fonts/SimHei-02.ttf", # 备用黑体
                ]
                title_font = None
                text_font = None
                small_font = None

                for font_path in font_paths:
                    try:
                        title_font = ImageFont.truetype(font_path, 36)
                        text_font = ImageFont.truetype(font_path, 20)
                        small_font = ImageFont.truetype(font_path, 16)
                        break
                    except:
                        continue

                if title_font is None:
                    title_font = ImageFont.load_default()
                    text_font = ImageFont.load_default()
                    small_font = ImageFont.load_default()
            except Exception as e:
                logger.error(f"加载字体失败: {str(e)}")
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()

            # 绘制顶部装饰条
            draw.rectangle([(0, 0), (img_width, 8)], fill=(100, 149, 237))

            # 绘制标题
            title_text = f"🎵 搜索结果"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text((padding, 25), title_text, fill=(65, 105, 225), font=title_font)

            # 绘制关键词
            keyword_text = f"关键词: {keyword}"
            keyword_bbox = draw.textbbox((0, 0), keyword_text, font=text_font)
            keyword_width = keyword_bbox[2] - keyword_bbox[0]
            draw.text((img_width - padding - keyword_width, 32), keyword_text, fill=(100, 100, 100), font=text_font)

            # 绘制结果数量
            subtitle_text = f"共找到 {result_data.get('total', 0)} 首歌曲"
            draw.text((padding, 70), subtitle_text, fill=(128, 128, 128), font=small_font)

            # 绘制分割线
            draw.line([(padding, header_height - 5), (img_width - padding, header_height - 5)], fill=(200, 200, 200), width=2)

            # 下载封面并绘制每首歌曲信息
            y_offset = header_height
            for idx, song_info in enumerate(result_data.get("songs", []), 1):
                # 绘制背景卡片（交替颜色）
                if idx % 2 == 1:
                    draw.rectangle([(padding, y_offset + 5), (img_width - padding, y_offset + item_height - 5)],
                                 fill=(255, 255, 255), outline=(220, 220, 220), width=1)
                else:
                    draw.rectangle([(padding, y_offset + 5), (img_width - padding, y_offset + item_height - 5)],
                                 fill=(248, 250, 255), outline=(220, 220, 220), width=1)

                # 绘制序号
                draw.text((padding + 15, y_offset + 15), f"{idx}", fill=(100, 149, 237), font=title_font)

                # 下载封面图片
                cover_url = song_info.get("cover_url")
                if cover_url:
                    try:
                        async with session.get(cover_url, timeout=8) as cover_response:
                            if cover_response.status == 200:
                                cover_data = await cover_response.read()
                                cover_img = Image.open(io.BytesIO(cover_data))
                                # 圆角封面处理
                                cover_img = cover_img.resize((110, 110), Image.Resampling.LANCZOS)
                                img.paste(cover_img, (padding + 55, y_offset + 10))
                    except Exception as e:
                        logger.error(f"下载封面失败: {str(e)}")
                        pass

                # 解析歌曲信息
                text_lines = song_info.get("text", "").split('\n')
                line_y = y_offset + 15
                text_x = padding + 180

                for line_idx, line in enumerate(text_lines):
                    if line_idx == 0:  # 歌曲名（第一行）
                        draw.text((text_x, line_y), line, fill=(50, 50, 50), font=text_font)
                    else:  # 其他信息
                        draw.text((text_x, line_y), line, fill=(100, 100, 100), font=small_font)
                    line_y += 24

                y_offset += item_height

            # 绘制底部装饰条
            draw.rectangle([(0, total_height - footer_height), (img_width, total_height)],
                         fill=(245, 248, 255))

            # 绘制底部文字
            footer_text = "Neko云音乐 - Powered by AstrBot"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=small_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (img_width - footer_width) // 2
            draw.text((footer_x, total_height - 22), footer_text, fill=(150, 150, 150), font=small_font)

            # 将图片转换为 base64
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG', quality=95)
            img_byte_arr.seek(0)
            import base64
            return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        except Exception as e:
            logger.error(f"创建搜索结果图片时发生错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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