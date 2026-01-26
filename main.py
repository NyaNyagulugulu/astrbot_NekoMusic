import asyncio
import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register("nekomusic", "NyaNyagulugulu", "Neko云音乐点歌插件", "1.0.0", "https://github.com/NyaNyagulugulu/astrbot_NekoMusic")
class NekoMusicPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("点歌", block=False)
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
                        result = self.handle_search_result(data)
                        yield event.plain_result(result)
                    else:
                        yield event.plain_result(f"搜索失败,API 返回状态码: {response.status}")
        except asyncio.TimeoutError:
            yield event.plain_result("搜索超时,请稍后重试")
        except Exception as e:
            logger.error(f"搜索音乐时发生错误: {str(e)}")
            yield event.plain_result(f"搜索失败: {str(e)}")

    def handle_search_result(self, data: dict) -> str:
        """处理搜索结果"""
        if data.get("success") and data.get("results"):
            songs = data["results"]
            
            if not songs:
                return "未找到相关歌曲"
            
            # 构建回复消息
            reply_text = f"🎵 搜索结果:\n\n"
            
            # 显示前 5 首歌曲
            for idx, song in enumerate(songs[:5], 1):
                song_name = song.get("name", song.get("title", "未知歌曲"))
                artist = song.get("artist", song.get("singer", song.get("ar", "未知歌手")))
                album = song.get("album", song.get("al", "未知专辑"))
                song_id = song.get("id", "")
                
                reply_text += f"{idx}. {song_name} - {artist}\n"
                reply_text += f"   专辑: {album}\n"
                if song_id:
                    reply_text += f"   ID: {song_id}\n"
                reply_text += "\n"
            
            reply_text += f"共找到 {len(songs)} 首歌曲"
            return reply_text
        else:
            return f"搜索失败: {data.get('message', '未知错误')}"