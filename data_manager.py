"""
DATA_MANAGER - QUẢN LÝ NGUỒN DỮ LIỆU
Module này quản lý dữ liệu các di tích từ file JSON cấu hình.
"""

import logging
import json
import os
from typing import Dict, Any, List

logger = logging.getLogger("uvicorn")

# Đường dẫn mác định tới file data
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "monuments.json")

def load_heritage_data() -> Dict[str, Any]:
    """
    Load data from JSON file.
    Returns a dict keyed by site_key.
    """
    if not os.path.exists(DATA_FILE_PATH):
        logger.error(f"❌ Không tìm thấy file dữ liệu: {DATA_FILE_PATH}")
        return {}
    
    try:
        with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
            
        # Convert list of objects to dict keyed by 'key'
        data_dict = {}
        for item in data_list:
            if "key" in item:
                data_dict[item["key"]] = item
        
        logger.info(f"✅ Đã load {len(data_dict)} di tích từ {DATA_FILE_PATH}")
        return data_dict
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc file dữ liệu: {e}")
        return {}

# Load data on import
_HERITAGE_DATA = load_heritage_data()

def get_heritage_config() -> Dict[str, Any]:
    """
    Lấy toàn bộ cấu hình di tích.
    """
    return _HERITAGE_DATA

def get_site_config(site_key: str) -> Dict[str, Any]:
    """
    Lấy cấu hình của một di tích cụ thể.
    """
    return _HERITAGE_DATA.get(site_key)

def get_default_site_key() -> str:
    """
    Lấy key của site mặc định (nếu có config is_default=True), 
    hoặc trả về site đầu tiên.
    """
    for key, data in _HERITAGE_DATA.items():
        if data.get("is_default"):
            return key
    
    # Fallback: return first key
    if _HERITAGE_DATA:
        return next(iter(_HERITAGE_DATA))
    return "hoang_thanh" # Final fallback

def reload_data():
    """
    Hàm để reload dữ liệu từ file (dùng khi file JSON thay đổi).
    """
    global _HERITAGE_DATA
    _HERITAGE_DATA = load_heritage_data()
    logger.info("🔄 Đã reload dữ liệu di tích.")

def get_data_source_info():
    """
    Lấy thông tin về nguồn dữ liệu.
    """
    return {
        "source": "JSON File",
        "path": DATA_FILE_PATH,
        "count": len(_HERITAGE_DATA)
    }
