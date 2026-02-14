"""
Script để xóa file temp khỏi Vector Database
"""
import asyncio
import logging
from vector_db import VectorDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clean_temp_files():
    """Xóa tất cả chunks từ file temp_*.md"""
    v_db = VectorDatabase(db_name="vector_db")
    
    # List of collections to clean
    collections = ["heritage", "culture", "history", "sites"]
    
    total_deleted = 0
    
    for collection_name in collections:
        try:
            # Xóa tất cả documents có source bắt đầu bằng "temp_"
            deleted_count = v_db.db[collection_name].delete_many({
                "metadata.source": {"$regex": "^temp_"}
            }).deleted_count
            
            if deleted_count > 0:
                logger.info(f"🗑️ Đã xóa {deleted_count} chunks từ '{collection_name}' (source: temp_*)")
                total_deleted += deleted_count
        except Exception as e:
            logger.error(f"❌ Lỗi khi xóa từ '{collection_name}': {e}")
    
    if total_deleted == 0:
        logger.info("✅ Không tìm thấy file temp nào trong database")
    else:
        logger.info(f"✨ Hoàn tất! Đã xóa tổng cộng {total_deleted} chunks từ các file temp")

if __name__ == "__main__":
    asyncio.run(clean_temp_files())
