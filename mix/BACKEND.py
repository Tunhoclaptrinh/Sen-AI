import os
import re
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv() 

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Regex tối ưu: Thêm dấu phẩy (,) và ngắt dòng (\n) vào các điểm ngắt
# Dấu ngắt mạnh: . ! ? ; \n
# Dấu ngắt mềm: ,
SENTENCE_ENDINGS_STRONG = re.compile(r'[.!?;\n]')
SENTENCE_ENDINGS_SOFT = re.compile(r'[.!?;\n,]') # Sử dụng cả dấu phẩy

# Ngưỡng độ dài buffer tối đa giảm xuống 100-120 để buộc ngắt sớm hơn
MAX_BUFFER_LENGTH = 110 
# Ngưỡng độ dài buffer tối thiểu
MIN_BUFFER_LENGTH = 10 

async def process_tts_request(sentence_to_speak: str, websocket: WebSocket):
    """
    Hàm gọi API TTS đồng bộ trong một luồng riêng (thread)
    """
    def sync_tts_call():
        return client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=sentence_to_speak
        )

    try:
        # Sử dụng asyncio.to_thread để chạy TTS song song với LLM stream
        tts_response = await asyncio.to_thread(sync_tts_call)
        
        # Stream các khối âm thanh về client
        for audio_chunk in tts_response.iter_bytes(chunk_size=4096):
            await websocket.send_bytes(audio_chunk)
            
    except Exception as e:
        print(f"Lỗi TTS trong thread: {e}")
        
# --- API WebSocket cho Chat và TTS Stream ---
@app.websocket("/ws/voice_chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    
    try:
        data = await websocket.receive_text()
        prompt = data.replace("PROMPT:", "").strip()
        print(f"Received prompt: {prompt}")

        llm_stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        sentence_buffer = ""
        
        for chunk in llm_stream:
            token = chunk.choices[0].delta.content or ""
            
            # Gửi token văn bản
            await websocket.send_text(f"TEXT:{token}") 
            
            sentence_buffer += token

            # Đã đạt đến ngưỡng ngắt câu chưa?
            if len(sentence_buffer) >= MIN_BUFFER_LENGTH:
                
                # 1. Kiểm tra dấu ngắt câu mạnh (.!?)
                strong_match = SENTENCE_ENDINGS_STRONG.search(token)
                
                # 2. Kiểm tra buffer đã quá dài chưa
                is_buffer_too_long = len(sentence_buffer) >= MAX_BUFFER_LENGTH
                
                should_process = strong_match or is_buffer_too_long

                if should_process:
                    split_point = -1
                    sentence_to_speak = ""
                    
                    if strong_match:
                        # Ưu tiên ngắt tại dấu ngắt mạnh cuối cùng trong buffer hiện tại
                        all_strong_matches = list(SENTENCE_ENDINGS_STRONG.finditer(sentence_buffer))
                        if all_strong_matches:
                            split_point = all_strong_matches[-1].end()
                            
                    elif is_buffer_too_long:
                        # Nếu buffer quá dài và không có dấu ngắt mạnh, tìm dấu phẩy gần nhất
                        soft_match = list(re.finditer(r'[,;]', sentence_buffer))
                        if soft_match:
                            split_point = soft_match[-1].end()
                        else:
                            # Nếu không có dấu phẩy, buộc ngắt ở MAX_BUFFER_LENGTH
                            split_point = MAX_BUFFER_LENGTH
                            
                    if split_point > 0:
                        sentence_to_speak = sentence_buffer[:split_point].strip()
                        sentence_buffer = sentence_buffer[split_point:]
                    
                    if sentence_to_speak:
                        # Chạy TTS song song
                        await process_tts_request(sentence_to_speak, websocket)
                        
        # Xử lý phần văn bản còn lại sau khi stream LLM kết thúc
        if sentence_buffer.strip():
            await process_tts_request(sentence_buffer.strip(), websocket)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.send_text(f"ERROR: Lỗi server: {e}")
    finally:
        await websocket.close()

# --- Endpoint HTML để Test ---
@app.get("/")
async def get():
    html_content = open("frontend.html", "r", encoding="utf-8").read()
    return HTMLResponse(content=html_content)