import asyncio
import os
import logging
from dotenv import load_dotenv
import redis.asyncio as redis

# Load biến môi trường
load_dotenv()

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ClearCache")

async def clear_chat_cache():
    """
    Xóa toàn bộ bộ nhớ Cache (Redis) của Sen NPC.
    """
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.error("❌ Không tìm thấy REDIS_URL trong .env")
        return

    try:
        r = redis.from_url(redis_url, decode_responses=True)
        
        # 1. Tìm các key Semantic Cache
        keys = await r.keys("sen:cache:*")
        
        if keys:
            await r.delete(*keys)
            logger.info(f"✅ Đã xóa {len(keys)} records khỏi Cache (sen:cache:*).")
        else:
            logger.info("ℹ️ Cache trống, không có gì để xóa.")

        # 2. Xóa Cache History (nếu cần)
        # keys_hist = await r.keys("chat_history:*")
        # if keys_hist: await r.delete(*keys_hist)

        await r.close()
        print("\n✨ Dọn dẹp hoàn tất! Hệ thống đã quên hết quá khứ sai lầm.")
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi xóa cache: {e}")

if __name__ == "__main__":
    asyncio.run(clear_chat_cache())
