# reflection.py
from typing import Dict, List
from openai import OpenAI


class Reflection:
    """
    Rewrite câu hỏi thành câu độc lập để retrieval chuẩn hơn.
    """

    def __init__(self, llm_client: OpenAI):
        self.client = llm_client

    def rewrite(self, messages: List[Dict], current_query: str) -> str:
        chat_history = [m for m in messages if m["role"] in ("user", "assistant")][-10:]

        history_text = ""
        for m in chat_history:
            role = "Khách" if m["role"] == "user" else "Bot"
            history_text += f"{role}: {m['content']}\n"
        history_text += f"Khách: {current_query}\n"

        prompt = [
            {
                "role": "system",
                "content": (
                    "Bạn là chuyên gia về văn hóa - di sản Việt Nam. "
                    "Hãy viết lại câu hỏi cuối thành một câu hỏi ĐỘC LẬP để tra cứu dữ liệu. "
                    "YÊU CẦU: giữ nguyên ngôn ngữ gốc, không trả lời, chỉ trả về câu hỏi đã viết lại."
                )
            },
            {"role": "user", "content": f"Lịch sử chat:\n{history_text}\n\nCâu hỏi độc lập:"}
        ]

        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=prompt,
                temperature=0
            )
            rewritten = resp.choices[0].message.content.strip()
            rewritten = rewritten.replace('"', "").replace("“", "").replace("”", "")
            return rewritten or current_query
        except Exception:
            return current_query



# from typing import List, Dict
# import openai

# class Reflection:
#     def __init__(self, llm_client):
#         """
#         :param llm_client: OpenAI client đã khởi tạo (vd: openai)
#         """
#         self.llm_client = llm_client

#     def rewrite(self, messages: List[Dict], current_query: str) -> str:
#         """
#         Viết lại current_query thành câu hỏi độc lập từ context.

#         :param messages: Lịch sử chat (dạng OpenAI chat messages)
#         :param current_query: Câu hỏi hiện tại từ người dùng
#         :return: Câu hỏi đã viết lại
#         """
#         # Lấy 10 messages gần nhất không phải role = system
#         chat_history = [msg for msg in messages if msg['role'] in ('user', 'assistant')][-10:]

#         # Xây dựng text cho lịch sử chat
#         history_text = ""
#         for msg in chat_history:
#             role = "Khách" if msg["role"] == "user" else "Bot"
#             history_text += f"{role}: {msg['content']}\n"
#         history_text += f"Khách: {current_query}\n"

#         prompt = [
#             {
#                 "role": "system",
#                 "content": (
#                     "Given a chat history and the latest user question which might reference context in the chat history, "
#                     "formulate a standalone question which can be understood without the chat history. Do NOT answer the question."
#                 )
#             },
#             {
#                 "role": "user",
#                 "content": history_text
#             }
#         ]

#         try:
#             # Gọi LLM để rewrite câu hỏi
#             response = self.llm_client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=prompt
#             )

#             # Kiểm tra nếu phản hồi hợp lệ
#             if response and 'choices' in response and len(response['choices']) > 0:
#                 rewritten = response['choices'][0]['message']['content'].strip()
#                 print(f"🔁 Reflection: \"{rewritten}\"")
#                 return rewritten
#             else:
#                 raise ValueError("API response does not contain valid data.")
#         except Exception as e:
#             print(f"Error during LLM reflection: {str(e)}")
#             return current_query  # Nếu gặp lỗi, trả lại câu hỏi ban đầu làm fallback



