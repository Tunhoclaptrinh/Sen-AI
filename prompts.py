import json
import os
import logging
from data_manager import get_heritage_config
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# File cấu hình Prompts
PROMPT_FILE = os.path.join(os.path.dirname(__file__), "data", "prompts.json")

def load_prompts():
    """Load prompts from JSON file."""
    if not os.path.exists(PROMPT_FILE):
        return {}
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        # 🔧 NEW: Tự động nối list thành string để file JSON dễ đọc hơn
        processed_data = {}
        for key, value in raw_data.items():
            if isinstance(value, list):
                processed_data[key] = "\n".join(value)
            else:
                processed_data[key] = value
        
        return processed_data
    except Exception as e:
        logger.error(f"❌ Error loading prompts: {e}")
        return {}

# Initial Load
_PROMPTS = load_prompts()

def get_bot_name():
    return os.getenv("BOT_NAME", "Sen")

def get_sen_persona():
    global _PROMPTS
    raw = _PROMPTS.get("sen_persona", "Bạn là {bot_name} - trợ lý ảo AI.")
    return raw.replace("{bot_name}", get_bot_name())

def get_planner_prompt(candidate_sites, hint_str=""):
    """
    Construct dynamic planner prompt using stored template via Dynamic In-Context Learning.
    candidate_sites: List of site dicts (filtered by semantic search).
    hint_str: Optional hints.
    """
    global _PROMPTS
    base_prompt = _PROMPTS.get("planner_prompt", "")
    
    # Inject Bot Name
    base_prompt = base_prompt.replace("{bot_name}", get_bot_name())
    
    # Nếu không có file config, dùng default hardcode để tránh crash
    if not base_prompt:
        base_prompt = """Bạn là Nhạc trưởng điều phối Sen NPC. Trả về JSON intent: heritage, realtime, chitchat, out_of_scope."""

    # Chuẩn bị context danh sách site
    if not candidate_sites: 
        # Fallback lấy full list nếu chưa filter
        full_config = get_heritage_config()
        candidate_sites = list(full_config.values())

    site_info_str = "\n".join([f"- {v['key']}: {v['name']}\n  Mô tả: {v.get('context_description', '')}" for v in candidate_sites])
    site_keys = [v['key'] for v in candidate_sites]

    # Inject dynamic data
    dynamic_part = f"""
DANH SÁCH DI TÍCH HỢP LỆ (Context):
{site_info_str}

DANH SÁCH KEY: {site_keys} hoặc null.

⭐ SỬ DỤNG SITE HINT:
{hint_str}

⚠️ QUY TẮC ĐẶC BIỆT:
- Nếu người dùng hỏi gợi ý địa điểm, hỏi chung chung (VD: "đi đâu chơi", "giới thiệu chỗ khác", "khám phá gì", "còn chỗ nào không") -> Intent: "chitchat" (để AI tự gợi ý) hoặc "heritage" (site: null).
- KHÔNG trả về "out_of_scope" nếu câu hỏi liên quan đến du lịch/tham quan/lịch sử, kể cả khi không khớp site key nào.
"""
    
    return base_prompt + "\n" + dynamic_part



def reload_prompts():
    global _PROMPTS
    _PROMPTS = load_prompts()
    logger.info("🔄 Prompts reloaded from JSON.")

def get_verifier_prompt():
    global _PROMPTS
    return _PROMPTS.get("verifier_prompt", """
Bạn là Trưởng ban Kiểm duyệt Nội dung của Sen NPC.
Nhiệm vụ: Đánh giá câu trả lời của Sen có an toàn, đúng trọng tâm và không bịa đặt hay không.
Nếu câu trả lời tốt, trả về {"valid": true}.
Nếu nội dung độc hại, sai lệch nghiêm trọng, hoặc bịa đặt (hallucination) khi không có context, trả về {"valid": false, "reason": "..."}.
""")

def get_contextualize_prompt():
    global _PROMPTS
    return _PROMPTS.get("contextualize_prompt", """
Bạn là chuyên gia ngôn ngữ học, nhiệm vụ là VIẾT LẠI (Rewrite) câu nói của người dùng thành một câu đầy đủ ngữ nghĩa, dựa trên Lịch sử hội thoại.

QUY TẮC QUAN TRỌNG:
1. Phân tích câu cuối cùng của AI trong lịch sử:
   - Nếu AI đang hỏi/mời mọc (Ví dụ: "Bạn có muốn gợi ý địa điểm khác không?", "Tôi kể tiếp nhé?").
   - Và người dùng trả lời ngắn (Ví dụ: "Có", "Không", "Ok", "Tôi không muốn", "Sao cũng được").
   -> HÃY VIẾT LẠI thành hành động cụ thể mà người dùng muốn.
   
2. Ví dụ minh họa:
   - AI: "...Cần mình gợi ý chỗ ăn ngon không?" -> User: "Có" => Rewrite: "Hãy gợi ý cho tôi quán ăn ngon."
   - AI: "...Muốn nghe lịch sử tiếp không?" -> User: "Thôi" => Rewrite: "Tôi không muốn nghe lịch sử nữa, hãy chuyển chủ đề."
   - AI: "...Hoàng Thành đóng cửa rồi." -> User: "Thế đi đâu giờ?" => Rewrite: "Gợi ý địa điểm tham quan khác thay thế cho Hoàng Thành Thăng Long."

3. Nếu câu nói đã đủ ý hoặc là chủ đề mới -> Giữ nguyên.

OUTPUT: Chỉ trả về câu đã viết lại, không giải thích thêm.
""")

# Backward compatibility & Export
SEN_CHARACTER_PROMPT = get_sen_persona()
PLANNER_SYSTEM_PROMPT = "Use get_planner_prompt() function instead."
VERIFIER_SYSTEM_PROMPT = get_verifier_prompt()