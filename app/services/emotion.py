"""
Sen AI - Emotion Intelligence System
Phân tích input/output để đề xuất biểu cảm phù hợp (gesture, mouth, eye)
"""
import logging
from typing import Dict, Literal

logger = logging.getLogger("uvicorn")

# Type definitions matching Frontend
GestureType = Literal['normal', 'hello', 'point', 'like', 'flag', 'hand_back']
MouthType = Literal['smile', 'smile_2', 'sad', 'open', 'close', 'half', 'tongue']
EyeType = Literal['normal', 'blink', 'close', 'half', 'like', 'sleep']

class EmotionAnalyzer:
    """
    Phân tích ngữ cảnh và đề xuất biểu cảm cho Sen AI
    """
    
    # Từ khóa để nhận diện cảm xúc/ngữ cảnh
    GREETING_WORDS = ['xin chào', 'chào bạn', 'chào sen', 'hi', 'hello', 'hế nhô', 'hế lô', 'alo']
    THANK_WORDS = ['cảm ơn', 'cám ơn', 'thanks', 'thank you', 'ơn nhiều']
    PRAISE_WORDS = ['tuyệt', 'hay', 'giỏi', 'ngon', 'đỉnh', 'pro', 'good', 'great', 'excellent', 'tốt']
    QUESTION_WORDS = ['gì', 'sao', 'tại sao', 'như thế nào', 'khi nào', 'ở đâu', 'ai', 'bao giờ', 'how', 'what', 'when', 'where', 'why']
    SAD_WORDS = ['buồn', 'khó', 'không hiểu', 'không biết', 'quá khó', 'phức tạp', 'rối', 'lú', 'confused', 'sad']
    EXCITED_WORDS = ['wow', 'ồ', 'ố', 'dễ thương', 'cute', 'đẹp', 'thú vị', 'amazing', 'cool', 'yêu', 'thích']
    
    # Heritage site keywords để đề xuất cử chỉ point
    HERITAGE_KEYWORDS = ['di tích', 'lăng', 'đền', 'chùa', 'cung', 'hoàng cung', 'thành', 'tháp', 'bảo tàng']
    
    @staticmethod
    def analyze(user_input: str, ai_response: str, intent: str = "unknown") -> Dict[str, str]:
        """
        Phân tích input/output và trả về emotion metadata
        
        Args:
            user_input: Câu hỏi của user
            ai_response: Câu trả lời của AI (để detect tone)
            intent: Intent từ workflow (heritage/chitchat/realtime)
            
        Returns:
            {
                "gesture": "hello" | "point" | "like" | ...,
                "mouthState": "smile" | "smile_2" | ...,
                "eyeState": "normal" | "like" | ...
            }
        """
        user_lower = user_input.lower()
        response_lower = ai_response.lower()[:200]  # Chỉ check 200 ký tự đầu để nhanh
        
        # === EMOTION RULES (Priority Order) ===
        
        # 1. THANKS - Cảm ơn → like gesture + smile + like eyes (CHECK FIRST)
        if any(word in user_lower for word in EmotionAnalyzer.THANK_WORDS):
            logger.info("🎭 Emotion: THANKS detected")
            return {
                "gesture": "like",
                "mouthState": "smile",
                "eyeState": "like"
            }
        
        # 2. GREETING - Chào hỏi → hello gesture + smile_2 + normal eyes
        if any(word in user_lower for word in EmotionAnalyzer.GREETING_WORDS):
            logger.info("🎭 Emotion: GREETING detected")
            return {
                "gesture": "hello",
                "mouthState": "smile_2",
                "eyeState": "normal"
            }
        
        # 3. PRAISE - Khen ngợi → like gesture + smile_2 + like eyes
        if any(word in user_lower for word in EmotionAnalyzer.PRAISE_WORDS):
            logger.info("🎭 Emotion: PRAISE detected")
            return {
                "gesture": "like",
                "mouthState": "smile_2",
                "eyeState": "like"
            }
        
        # 4. EXCITED - Hứng thú → flag gesture + open mouth + normal eyes
        if any(word in user_lower for word in EmotionAnalyzer.EXCITED_WORDS):
            logger.info("🎭 Emotion: EXCITED detected")
            return {
                "gesture": "flag",
                "mouthState": "open",
                "eyeState": "normal"
            }
        
        # 5. SAD/CONFUSED - Buồn/Khó → normal gesture + sad mouth + half eyes
        if any(word in user_lower for word in EmotionAnalyzer.SAD_WORDS):
            logger.info("🎭 Emotion: SAD/CONFUSED detected")
            return {
                "gesture": "normal",
                "mouthState": "sad",
                "eyeState": "half"
            }
        
        # 6. HERITAGE SITE - Hỏi về di tích → point gesture + smile + normal eyes
        if intent == "heritage" or any(word in user_lower for word in EmotionAnalyzer.HERITAGE_KEYWORDS):
            logger.info("🎭 Emotion: HERITAGE POINTING detected")
            return {
                "gesture": "point",
                "mouthState": "smile",
                "eyeState": "normal"
            }
        
        # 7. QUESTION - Hỏi thông tin → point gesture + smile + normal eyes
        if any(word in user_lower for word in EmotionAnalyzer.QUESTION_WORDS):
            logger.info("🎭 Emotion: QUESTION detected")
            return {
                "gesture": "point",
                "mouthState": "smile",
                "eyeState": "normal"
            }
        
        # 8. DEFAULT - Trung lập → normal gesture + smile + normal eyes
        logger.info("🎭 Emotion: DEFAULT (neutral)")
        return {
            "gesture": "normal",
            "mouthState": "smile",
            "eyeState": "normal"
        }

    @staticmethod
    async def analyze_with_ai(openai_client, user_input: str, ai_response: str) -> Dict[str, str]:
        """
        🚀 ADVANCED: Sử dụng GPT-4o-mini để phân tích cảm xúc thông minh hơn
        (Optional, chỉ dùng khi cần độ chính xác cao)
        
        Args:
            openai_client: AsyncOpenAI client
            user_input: Câu hỏi của user
            ai_response: Câu trả lời của AI
            
        Returns:
            {
                "gesture": "...",
                "mouthState": "...",
                "eyeState": "...",
                "reason": "Explanation from AI"
            }
        """
        try:
            system_prompt = """Bạn là chuyên gia phân tích cảm xúc cho nhân vật AI Sen.
Nhiệm vụ: Dựa vào input của user và response của AI, hãy đề xuất biểu cảm phù hợp.

**Các biểu cảm có sẵn:**
- gesture: normal, hello, point, like, flag, hand_back
- mouthState: smile, smile_2, sad, open, close, half, tongue
- eyeState: normal, blink, close, half, like, sleep

**Quy tắc:**
1. Chào hỏi → hello + smile_2 + normal
2. Cảm ơn/Khen → like + smile + like
3. Hỏi về di tích → point + smile + normal
4. Buồn/Khó → normal + sad + half
5. Vui vẻ/Hứng khởi → flag + open + normal

Trả về JSON: {"gesture": "...", "mouthState": "...", "eyeState": "...", "reason": "..."}"""

            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User: {user_input}\nAI: {ai_response[:300]}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"🤖 AI Emotion Analysis: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI Emotion Analysis failed: {e}")
            # Fallback to rule-based
            return EmotionAnalyzer.analyze(user_input, ai_response, "unknown")
