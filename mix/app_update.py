import os
import base64
import re
import io
import time
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from gtts import gTTS
from langdetect import detect

from embeddings import Embeddings
from vector_db import VectorDatabase
from reflection import Reflection
from rerank import Reranker

from semantic_router.route import Route
from semantic_router.router import SemanticRouter
import semantic_router.samples as samples

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Tải biến môi trường
load_dotenv()

# ====== CONFIG ======
DB_NAME = "vector_db"
COLLECTION_NAME = "culture_collection"
VECTOR_INDEX_NAME = "vector_index"
VECTOR_PATH = "embedding"

TOP_K_RETRIEVAL = 15
TOP_K_FINAL = 5

CULTURE_FILES = [
    ("mua_roi_nuoc", "mua_roi_nuoc.md"),
    ("hoang_thanh", "hoang_thanh.md"),
]

# SYSTEM_PROMPT = (
#     "You are a Vietnamese Cultural Heritage NPC guide.\n"
#     "- ALWAYS answer in the language the user used (English or Vietnamese).\n"
#     "- ONLY answer based on the provided CONTEXT.\n"
#     "- If the context lacks information, strictly say: \"Xin lỗi, tôi không có đủ dữ liệu để trả lời chính xác câu hỏi này, bạn hãy thử lại bằng cách đặt câu hỏi rõ hơn nhé!\"\n"
#     "- Answer clearly, concisely, and directly. Use proper punctuation for better speech synthesis."
# )

SYSTEM_PROMPT = (
    "Bạn là một hướng dẫn viên ảo tên là 'Minh', chuyên gia về Di sản Văn hóa Việt Nam.\n"
    "--- NGÔN NGỮ (LANGUAGE RULES) ---\n"
    "- Nếu khách hỏi bằng tiếng Việt, hãy trả lời bằng tiếng Việt.\n"
    "- If the user asks in English, you MUST respond in English.\n"
    "- Tuyệt đối không trả lời song ngữ trong cùng một câu (trừ tên riêng di tích).\n"
    "--- PHONG CÁCH DIỄN ĐẠT ---\n"
    "- TÔNG GIỌNG: Thân thiện, niềm nở, tự hào và giàu cảm xúc. Hãy coi người dùng như một khách du lịch đang đứng trước di tích.\n"
    "- CÁCH XƯNG HÔ: Sử dụng 'Tôi' hoặc 'Mình' và gọi người dùng là 'Bạn' hoặc 'Quý khách'.\n"
    "- BIỂU CẢM: Thỉnh thoảng thêm các từ cảm thán nhẹ nhàng ở đầu câu như: 'Chào bạn!', 'Rất thú vị là...', 'Có thể bạn chưa biết...', 'Thật tự hào khi...' để tăng tính tương tác.\n"
    "\n--- QUY TẮC NỘI DUNG ---\n"
    "1. NGÔN NGỮ: Phản hồi bằng ngôn ngữ người dùng đã hỏi (Tiếng Anh hoặc Tiếng Việt).\n"
    "2. GIỚI HẠN DỮ LIỆU: Chỉ trả lời dựa trên thông tin trong CONTEXT. Không được bịa đặt.\n"
    "3. XỬ LÝ KHI THIẾU TIN: Nếu không có dữ liệu, hãy nói: 'Tiếc quá, hiện tại mình chưa có thông tin chi tiết về phần này. Bạn có muốn tìm hiểu về [gợi ý một chủ đề trong context] không?'.\n"
    "4. TỐI ƯU CHO GIỌNG ĐỌC (TTS):\n"
    "   - Trình bày dạng đoạn văn mạch lạc, KHÔNG dùng gạch đầu dòng hay danh sách số.\n"
    "   - Ưu tiên câu ngắn, ngắt nghỉ đúng chỗ bằng dấu chấm, dấu phẩy.\n"
    "   - Tránh các ký tự đặc biệt, icon hoặc bảng biểu trong lời nói."
)

# ====== AUDIO ENGINE ======
def tts_play(text: str):
    text = (text or "").strip()
    clean_text = re.sub(r'[^\w\s,.!??áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ]', '', text).strip()
    
    if not clean_text or len(clean_text) < 2:
        return
        
    try:
        # Tự động nhận diện ngôn ngữ của câu trả lời
        lang_code = 'vi'
        try:
            detected_lang = detect(text)
            if detected_lang == 'en':
                lang_code = 'en'
        except:
            pass # Nếu lỗi thì mặc định là tiếng Việt
            
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)

        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode()
        audio_uri = f"data:audio/mp3;base64,{b64}"
        
        js_code = f"""
            <script>
                (function() {{
                    const audioUri = "{audio_uri}";
                    
                    // 1. Đưa câu mới vào hàng đợi chung
                    let queue = JSON.parse(localStorage.getItem('audio_queue') || '[]');
                    queue.push(audioUri);
                    localStorage.setItem('audio_queue', JSON.stringify(queue));

                    // 2. Hàm quản lý việc phát nhạc
                    function startManager() {{
                        if (window.audioManagerInterval) clearInterval(window.audioManagerInterval);
                        
                        window.audioManagerInterval = setInterval(() => {{
                            // Nếu đang phát thì thôi, đợi vòng lặp kế tiếp kiểm tra lại
                            if (localStorage.getItem('is_audio_playing') === 'true') return;

                            let currentQueue = JSON.parse(localStorage.getItem('audio_queue') || '[]');
                            if (currentQueue.length === 0) {{
                                clearInterval(window.audioManagerInterval);
                                return;
                            }}

                            // Lấy câu tiếp theo ra phát
                            localStorage.setItem('is_audio_playing', 'true');
                            let nextUri = currentQueue.shift();
                            localStorage.setItem('audio_queue', JSON.stringify(currentQueue));

                            let audio = new Audio(nextUri);
                            audio.playbackRate = 1.4;
                            
                            audio.onended = function() {{
                                localStorage.setItem('is_audio_playing', 'false');
                            }};
                            
                            audio.play().catch(e => {{
                                localStorage.setItem('is_audio_playing', 'false');
                            }});
                        }}, 200); // Kiểm tra hàng đợi mỗi 0.2 giây
                    }}

                    startManager();
                }})();
            </script>
        """
        st.components.v1.html(js_code, height=0)
    except Exception:
        pass

# ====== HELPERS ======
def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def chunk_markdown(md_text: str) -> List[Dict]:
    headers_to_split_on = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    splitter1 = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    sections = splitter1.split_text(md_text)
    splitter2 = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=180)
    docs = splitter2.split_documents(sections)
    return [{"content": d.page_content.strip(), "metadata": d.metadata} for d in docs if d.page_content.strip()]

@st.cache_resource(show_spinner="🔄 NPC đang khởi động...")
def setup_system():
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    embedding = Embeddings(model_name="text-embedding-3-small")
    vector_db = VectorDatabase(db_name=DB_NAME)
    reflector = Reflection(llm_client=client)
    reranker = None #Reranker(model_name="BAAI/bge-reranker-v2-m3")

    routes = [
        Route(name="roi_nuoc", samples=samples.roiNuocSample, filter_dict={"culture_type": "mua_roi_nuoc"}),
        Route(name="hoang_thanh", samples=samples.hoangThanhSample, filter_dict={"culture_type": "hoang_thanh"}),
        Route(name="chitchat", samples=samples.chitchatSample, filter_dict={}),
    ]
    router = SemanticRouter(embedding=embedding, routes=routes, threshold=0.5)

    # Ingest data
    for culture_type, file_path in CULTURE_FILES:
        if vector_db.count_documents(COLLECTION_NAME, {"culture_type": culture_type}) == 0:
            if os.path.exists(file_path):
                md = open(file_path, "r", encoding="utf-8").read()
                chunks = chunk_markdown(md)
                vectors = embedding.encode([c["content"] for c in chunks])
                docs = [{"content": c["content"], "embedding": vectors[i], "culture_type": culture_type, "metadata": c["metadata"]} for i, c in enumerate(chunks)]
                vector_db.insert_many(COLLECTION_NAME, docs)
    return client, embedding, vector_db, router, reflector, reranker

# ====== LOGIC XỬ LÝ CHÍNH ======
def handle_query(user_input: str, client: OpenAI, embedding: Embeddings, vector_db: VectorDatabase,
                 router: SemanticRouter, reflector: Reflection, reranker: Reranker):

    if len(user_input.strip().split()) <= 2:
        ans = "Chào bạn! Tôi có thể giúp gì cho bạn về Múa rối nước hoặc Hoàng thành Thăng Long?"
        st.markdown(ans)
        tts_play(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        return

    # 1) SMART REFLECTION (Tối ưu tốc độ)
    ambiguous_keywords = ["nó", "đó", "đấy", "kia", "ấy", "họ", "ông ấy", "bà ấy", "ở đó", "chỗ đó"]
    is_ambiguous = any(word in user_input.lower() for word in ambiguous_keywords)
    word_count = len(user_input.strip().split())

    # Nếu câu hỏi dài (>10 từ) và không chứa từ mơ hồ, hoặc là câu hỏi đầu tiên -> Bỏ qua Rewrite
    if word_count > 10 and not is_ambiguous:
        rewritten = user_input
        st.caption("⚡ **Fast-Track**: Bỏ qua bước làm rõ (Câu hỏi đủ ý)")
    elif len(st.session_state.messages) <= 1:
        rewritten = user_input
        st.caption("⚡ **First Query**: Đi thẳng vào tìm kiếm")
    else:
        # Chỉ gọi GPT rewrite khi thực sự cần ngữ cảnh câu trước
        rewritten = reflector.rewrite(st.session_state.messages, user_input)
        st.caption(f"🔍 **Reflected**: {rewritten}")
    
    # 2) ROUTER
    score, route_name, filter_dict = router.guide(rewritten)
    st.caption(f"🧭 Route: {route_name} ({score:.2f})")

    if route_name in ("uncertain", "chitchat"):
        ans = "Tôi là NPC chuyên trách di sản. Bạn vui lòng hỏi cụ thể về Múa rối nước hoặc Hoàng thành nhé!"
        st.markdown(ans)
        tts_play(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        return

    # Retrieval & Rerank
    # 1. Retrieval (Lấy rộng ra một chút) -> dùng hybrid(xử lí thô: tìm sl từ giống nhau + gpt) để kiểm tra rerank
    # BƯỚC 1: RETRIEVAL
    q_vec = embedding.encode([rewritten])[0]
    results = vector_db.query(COLLECTION_NAME, q_vec, limit=15, filter_dict=filter_dict)

    if not results:
        st.warning("Không tìm thấy dữ liệu phù hợp.")
        return

    # BƯỚC 2: LỌC THÔ (HEURISTIC)
    import re
    def simple_keyword_score(text, query):
        # Chỉ lấy các từ có nghĩa (độ dài > 2) để tránh stopwords
        query_words = set(re.findall(r'\w{3,}', query.lower()))
        text_lower = text.lower()
        # Thưởng điểm cho từ khóa: +1 điểm mỗi từ xuất hiện
        score = sum(1.5 if w in text_lower else 0 for w in query_words)
        # Thưởng thêm nếu chứa từ viết hoa (tên riêng) từ câu hỏi gốc
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', rewritten)
        for pn in proper_nouns:
            if pn.lower() in text_lower: score += 2.0
        return score

    for r in results:
        k_score = simple_keyword_score(r['content'], rewritten)
        # Vector score thường nhỏ (0.5-0.8), nên k_score cần trọng số phù hợp
        r['hybrid_score'] = r.get('score', 0) + (k_score * 0.1)

    results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    top_candidates = results[:5]
    passages = [r["content"] for r in top_candidates]

    # BƯỚC 3: LỌC TINH (LLM RERANK)
    # Thêm phân cách rõ ràng để GPT không bị "loạn" mắt
    rerank_input = "\n\n".join([f"--- ĐOẠN [{i}] ---\n{p}" for i, p in enumerate(passages)])
    
    rerank_prompt = f"""
    Dựa vào các đoạn văn sau, hãy chọn ra ID của những đoạn chứa thông tin trực tiếp để trả lời câu hỏi.
    Câu hỏi: {rewritten}
    
    {rerank_input}
    
    Chỉ trả về số thứ tự [index] trong ngoặc vuông, ví dụ: [0, 2]. Nếu không có thông tin, trả về [None].
    """

    context = ""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Bạn là bộ lọc dữ liệu chính xác. Chỉ trả về ID."},
                      {"role": "user", "content": rerank_prompt}],
            temperature=0,
            timeout=5
        )
        
        raw_res = response.choices[0].message.content.strip()
        # Regex này sẽ lấy mọi con số nằm trong chuỗi
        selected_indices = [int(i) for i in re.findall(r'\d+', raw_res)]
        
        final_passages = [passages[i] for i in selected_indices if i < len(passages)]
        context = "\n\n".join(final_passages) if final_passages else passages[0]
        
    except Exception as e:
        # Bảo vệ: nếu passages trống thì gán chuỗi rỗng, nếu có thì lấy cái đầu tiên
        context = passages[0] if passages else ""
#----- c2: Retrieval & Rerank(sử dụng model có sẵn)

    # q_vec = embedding.encode([rewritten])[0]
    # results = vector_db.query(COLLECTION_NAME, q_vec, limit=TOP_K_RETRIEVAL, filter_dict=filter_dict)
    
    # if not results:
    #     ans = "Xin lỗi, tôi chưa có dữ liệu về phần này."
    #     st.markdown(ans)
    #     tts_play(ans)
    #     return

    # passages = [r["content"] for r in results if r.get("content")]
    # _, ranked_passages = reranker.rerank(rewritten, passages, threshold=0.4)
    # context = "\n\n".join(ranked_passages[:TOP_K_FINAL] if ranked_passages else passages[:3])

#-------c3: bỏ rerank -> rủi ro chính xác

    ## 3) Retrieval (Chỉ giữ lại phần này, bỏ Rerank)
    # q_vec = embedding.encode([rewritten])[0]
    # results = vector_db.query(
    #     collection_name=COLLECTION_NAME, 
    #     query_vector=q_vec, 
    #     limit=5, # Lấy thẳng 5 kết quả tốt nhất thay vì 15
    #     filter_dict=filter_dict
    # )
    
    # if not results:
    #     ans = "Xin lỗi, tôi chưa có dữ liệu về phần này."
    #     st.markdown(ans)
    #     tts_play(ans)
    #     st.session_state.messages.append({"role": "assistant", "content": ans})
    #     return

    # # Lấy nội dung trực tiếp từ kết quả tìm kiếm (Skip bước Rerank)
    # context_passages = [r["content"] for r in results if r.get("content")]
    # context = "\n\n".join(context_passages).strip()

    # Generator with Streaming + Real-time TTS
    ph = st.empty()
    full_answer = ""
    sentence_buffer = ""

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"CONTEXT:\n{context}\n\nQ: {rewritten}"}],
        stream=True
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            full_answer += delta
            sentence_buffer += delta
            ph.markdown(full_answer + "▌")
            
            # Nếu gặp dấu ngắt câu, phát âm thanh ngay
            if any(p in delta for p in [".", "?", "!", "\n", ":"]):
                if len(sentence_buffer.strip()) > 5:
                    tts_play(sentence_buffer)
                    sentence_buffer = ""

    if sentence_buffer.strip():
        tts_play(sentence_buffer)

    ph.markdown(full_answer)
    st.session_state.messages.append({"role": "assistant", "content": full_answer})

# ====== UI UI UI ======
st.set_page_config(page_title="NPC Di sản Việt Nam", layout="wide")
st.title("🏯 NPC Di sản Việt Nam (Real-time Voice)")

init_session()
client, embedding, vector_db, router, reflector, reranker = setup_system()

for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Hỏi về di sản...")
if user_input:

    st.components.v1.html("""
        <script>
            localStorage.setItem('audio_queue', '[]'); 
            localStorage.setItem('is_audio_playing', 'false');
            // Dừng ngay lập tức âm thanh đang phát (nếu có)
            if (window.currentAudio) { window.currentAudio.pause(); } 
        </script>
    """, height=0)

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        handle_query(user_input, client, embedding, vector_db, router, reflector, reranker)