import asyncio
import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp


@register("nekomusic", "NyaNyagulugulu", "Neko云音乐点歌插件", "1.2.0", "https://github.com/NyaNyagulugulu/astrbot_NekoMusic")
class NekoMusicPlugin(Star):
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
                        
                        # 构建转发消息列表
                        forward_messages = []
                        
                        # 添加标题消息
                        forward_messages.append({
                            "content": f"🎵 搜索结果: {keyword}\n共找到 {result_data.get('total', 0)} 首歌曲"
                        })
                        
                        # 添加每首歌的封面和信息
                        for idx, song_info in enumerate(result_data.get("songs", []), 1):
                            # 构建歌曲消息
                            song_message = f"{idx}. {song_info['text']}"
                            if song_info.get("cover_url"):
                                song_message = f"[CQ:image,file={song_info['cover_url']}]\n{song_message}"
                            forward_messages.append({
                                "content": song_message
                            })
                        
                        # 发送合并转发消息
                        yield event.forward_result(forward_messages)
                    else:
                        yield event.plain_result(f"搜索失败,API 返回状态码: {response.status}")
        except asyncio.TimeoutError:
            yield event.plain_result("搜索超时,请稍后重试")
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