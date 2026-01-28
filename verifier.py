import logging
import os
from prompts import VERIFIER_SYSTEM_PROMPT

logger = logging.getLogger("uvicorn")

class Verifier:
    def __init__(self, openai_client):
        self.openai = openai_client

    async def verify(self, question: str, context: str, answer: str) -> dict:
        # Check flag enable/disable (Default: False)
        if os.getenv("ENABLE_VERIFIER", "false").lower() != "true":
             return {"is_valid": True, "reason": "Verifier disabled"}

        """
        Kiểm tra và sửa lỗi câu trả lời nếu không khớp với context.
        Trả về dict: {"is_valid": bool, "reason": str, "filtered_answer": str}
        """
        # Nếu không có context (ví dụ chitchat), không cần verify
        if not context:
             return {"is_valid": True, "reason": "No context to verify"}

        try:
            logger.info("🕵️ VERIFIER: Đang kiểm tra câu trả lời...")
            res = await self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}\n\nProposed Answer: {answer}"}
                ],
                temperature=0.0
            )
            raw_verdict = res.choices[0].message.content
            
            try:
                import json
                cleaned_verdict = raw_verdict.replace("```json", "").replace("```", "").strip()
                verdict_json = json.loads(cleaned_verdict)
                
                is_valid = verdict_json.get("valid", False)
                reason = verdict_json.get("reason", "")
                
                if is_valid:
                     logger.info("✅ VERIFIER: Hợp lệ.")
                     return {"is_valid": True, "reason": "Pass"}
                else:
                    logger.warning(f"⚠️ VERIFIER REJECTED: {reason}")
                    return {
                        "is_valid": False, 
                        "reason": reason,
                        "filtered_answer": f"⚠️ [Cảnh báo nội dung]: Sen nhận thấy câu trả lời có thể chưa chính xác so với tài liệu. ({reason})"
                    }

            except json.JSONDecodeError:
                logger.warning("⚠️ VERIFIER output not JSON. Skipping verify.")
                return {"is_valid": True, "reason": "Non-JSON Output from Verifier"}
                
        except Exception as e:
            logger.error(f"❌ Verifier error: {e}")
            return {"is_valid": True, "reason": f"Error: {e}"}
