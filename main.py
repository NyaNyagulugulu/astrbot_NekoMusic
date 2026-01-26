import asyncio
import aiohttp
from astrbot import logger, AstrMessageEvent, MessageChain, Plain
from astrbot.plugin import Plugin


class NekoMusicPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.plugin_name = "Neko云音乐点歌"
        self.plugin_desc = "通过点歌指令搜索音乐"
        self.plugin_version = "1.0.0"
        self.plugin_author = "NyaNyagulugulu"
        self.plugin_type = "message"
        self.plugin_priority = 10

    async def on_message(self, event: AstrMessageEvent):
        """监听消息事件"""
        # 获取消息文本
        msg_text = event.message_str
        
        # 检查是否为点歌指令
        if msg_text.startswith("点歌"):
            # 提取搜索关键词
            keyword = msg_text[2:].strip()
            
            if not keyword:
                await event.send_message(MessageChain([
                    Plain("请输入要搜索的歌曲名称,例如:点歌 Lemon")
                ]))
                return
            
            # 搜索音乐
            await self.search_music(event, keyword)

    async def search_music(self, event: AstrMessageEvent, keyword: str):
        """调用 API 搜索音乐"""
        api_url = "https://music.cnmsb.xin/api/music/search"
        json_data = {"query": keyword}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=json_data, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        await self.handle_search_result(event, data)
                    else:
                        await event.send_message(MessageChain([
                            Plain(f"搜索失败,API 返回状态码: {response.status}")
                        ]))
        except asyncio.TimeoutError:
            await event.send_message(MessageChain([
                Plain("搜索超时,请稍后重试")
            ]))
        except Exception as e:
            logger.error(f"搜索音乐时发生错误: {str(e)}")
            await event.send_message(MessageChain([
                Plain(f"搜索失败: {str(e)}")
            ]))

    async def handle_search_result(self, event: AstrMessageEvent, data: dict):
        """处理搜索结果"""
        if data.get("success") and data.get("results"):
            songs = data["results"]
            
            if not songs:
                await event.send_message(MessageChain([
                    Plain("未找到相关歌曲")
                ]))
                return
            
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
            
            await event.send_message(MessageChain([
                Plain(reply_text)
            ]))
        else:
            await event.send_message(MessageChain([
                Plain(f"搜索失败: {data.get('message', '未知错误')}")
            ]))