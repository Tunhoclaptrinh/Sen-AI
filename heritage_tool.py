import httpx

import re
from datetime import datetime, timezone, timedelta
from data_manager import get_site_config, get_data_source_info
import logging

logger = logging.getLogger("uvicorn")

# Timezone Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

def get_vietnam_time():
    """Lấy thời gian hiện tại ở Việt Nam (UTC+7)"""
    return datetime.now(VN_TZ).replace(tzinfo=None)

class HeritageTools:
    @staticmethod
    def _evaluate_weather(temp: float) -> tuple:
        """
        🔧 NEW: Đánh giá thời tiết và đưa ra lời khuyên
        """
        if temp < 10:
            return "Rất lạnh", "❄️ Bạn nên mặc áo khoác dày, mũ, khăn ấm. Tránh ở ngoài lâu."
        elif temp < 15:
            return "Lạnh", "🧥 Nên mặc áo khoác, có thể mang khăn. Tham quan từ từ, dừng nghỉ khi cần."
        elif temp < 20:
            return "Mát mẻ", "👕 Mặc áo dài tay là hợp lý. Thời tiết lý tưởng để tham quan."
        elif temp < 25:
            return "Thoải mái", "🌤️ Thời tiết rất tốt. Mặc áo thường. Đừng quên sunscreen!"
        elif temp < 30:
            return "Nóng", "☀️ Rất nóng. Mặc áo nhẹ, thoáng mát. Mang nước, mũ, kính chống nắng."
        else:
            return "Rất nóng", "🔥 Cực kỳ nóng. Nên tránh hoạt động ngoài từ 11h-15h. Uống nhiều nước!"

    @staticmethod
    async def get_weather(site_key: str):
        site = get_site_config(site_key)
        if not site: return None
        lat, lon = site["coords"]["lat"], site["coords"]["lon"]
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, timeout=5)
                temp = resp.json()['current_weather']['temperature']
                
                # 🔧 NEW: Thêm đánh giá + lời khuyên
                evaluation, advice = HeritageTools._evaluate_weather(temp)
                
                weather_info = f"Thời tiết ở {site['name']}: {temp}°C\n"
                weather_info += f"Đánh giá: {evaluation}\n"
                weather_info += f"Lời khuyên: {advice}"
                
                logger.info(f"🌡️ Weather at {site['name']}: {temp}°C ({evaluation})")
                return weather_info
            except Exception as e: 
                logger.error(f"❌ Weather API error: {e}")
                return "Sen chưa xem được thời tiết rồi hihi."

    @staticmethod
    def _evaluate_opening_status(current_hour: int, current_minute: int, open_hour: int, close_hour: int, site_name: str) -> tuple:
        """
        🔧 NEW: Đánh giá trạng thái mở cửa và đưa ra lời khuyên
        """
        is_open = open_hour <= current_hour < close_hour
        
        if not is_open:
            # Đã đóng cửa
            hours_until_open = (open_hour - current_hour) if current_hour < open_hour else (24 - current_hour + open_hour)
            return {
                "status": "Đóng cửa",
                "reason": f"📍 Hiện tại {site_name} đã đóng. Sẽ mở lại vào {open_hour}h.",
                "advice": f"💡 Nên quay lại vào {open_hour}h. Bạn còn có thể tham quan những địa điểm khác."
            }
        
        hours_until_close = close_hour - current_hour
        
        if hours_until_close <= 0.5:  # Dưới 30 phút
            return {
                "status": "Sắp đóng cửa",
                "reason": f"⏰ {site_name} sắp đóng cửa trong vài phút (đóng {close_hour}h).",
                "advice": f"🏃 Bạn nên nhanh hoàn thành tham quan. Tập trung vào những di vật chính. Chuẩn bị ra về!"
            }
        elif hours_until_close <= 1:  # Dưới 1 giờ
            return {
                "status": "Sắp đóng cửa",
                "reason": f"⏰ {site_name} sắp đóng cửa trong {hours_until_close:.1f} giờ ({close_hour}h).",
                "advice": f"⚠️ Thời gian còn lại không nhiều. Ưu tiên tham quan những khu chính, hạn chế dừng lâu."
            }
        elif hours_until_close <= 2:  # Dưới 2 giờ
            return {
                "status": "Có thời gian hạn chế",
                "reason": f"🕒 {site_name} đang mở. Còn {hours_until_close:.1f} giờ (đóng {close_hour}h).",
                "advice": f"📋 Thời gian vừa vặn. Lên kế hoạch tham quan trước để không bỏ sót."
            }
        else:
            return {
                "status": "Mở cửa đầy đủ",
                "reason": f"✅ {site_name} đang mở cửa bình thường. Còn {hours_until_close:.1f} giờ (đóng {close_hour}h).",
                "advice": f"🎉 Bạn có thời gian dư dả. Tham quan thong thả, khám phá chi tiết, chụp ảnh."
            }

    @staticmethod
    def get_opening_status(site_key: str):
        site = get_site_config(site_key)
        if not site: return None
        
        # 🔧 FIX: Lấy thời gian Việt Nam thay vì UTC
        now = get_vietnam_time()
        current_hour = now.hour
        current_minute = now.minute
        open_hour = site['open_hour']
        close_hour = site['close_hour']
        
        logger.info(f"⏰ Thời gian hiện tại (VN): {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🏛️ {site['name']}: Mở {open_hour}h - Đóng {close_hour}h")
        
        # 🔧 NEW: Sử dụng evaluation function
        eval_result = HeritageTools._evaluate_opening_status(current_hour, current_minute, open_hour, close_hour, site['name'])
        
        status_info = f"Trạng thái {site['name']}: {eval_result['status']}\n"
        status_info += f"Bây giờ là {current_hour}h{current_minute:02d}\n"
        status_info += f"{eval_result['reason']}\n"
        status_info += f"{eval_result['advice']}"
        
        return status_info
    
    @staticmethod
    async def get_ticket_prices(site_key: str):
        """
        Lấy thông tin giá vé (Trả về LINK TRANG CHỦ để user tự xem).
        Bỏ qua việc hiện giá tiền cụ thể.
        """
        site = get_site_config(site_key)
        if not site: return None
        
        ticket_url = site.get("ticket_url")
        home_url = site.get("home_url")
        website = site.get("website") # Support fallback field
        
        # Ưu tiên: ticket_url > website > home_url
        final_url = ticket_url or website or home_url
        
        if final_url:
            logger.info(f"✅ Trả về link giá vé cho {site['name']}")
            return f"Để xem thông tin giá vé và các ưu đãi mới nhất, bạn vui lòng truy cập trang chủ của {site['name']} tại đây:\n👉 [Xem chi tiết Giá vé & Đặt chỗ]({final_url})"
        else:
            return f"Hiện tại Sen chưa có đường link bán vé trực tuyến của {site['name']}. Bạn vui lòng kiểm tra trực tiếp tại quầy nhé!"


