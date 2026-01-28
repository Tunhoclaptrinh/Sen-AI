# ingest.py
import os
import asyncio
import logging
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# LangChain Splitters & Loaders
# LangChain Splitters & Loaders (Imports moved inside functions for safety)

# Module Database & Config
from vector_db import VectorDatabase
from data_manager import get_heritage_config

# --- 1. CẤU HÌNH ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "vector_db"
COLLECTION_NAME = "culture"
# Model 384 chiều tối ưu cho tiếng Việt/đa ngữ
local_embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

SOURCE_DIR = os.path.join(os.path.dirname(__file__), "data", "documents")

# --- 2. HELPERS: LOADERS & SMART CHUNKERS ---

def clean_text(text: str) -> str:
    """Làm sạch văn bản PDF/Docx để embedding tốt hơn."""
    # Xóa nhiều dấu xuống dòng liên tiếp
    text = re.sub(r'\n+', '\n', text)
    # Xóa khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_markdown(file_path):
    """
    Chiến lược cho Markdown: Tận dụng cấu trúc Header (#, ##, ###) để cắt ngữ nghĩa.
    """
    try:
        try:
            from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
        except ImportError:
            from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # 1. Cắt theo cấu trúc Header (Semantic Splitting)
        headers_to_split_on = [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        md_header_splits = markdown_splitter.split_text(text)

        # 2. Cắt mịn lại nếu header content quá dài
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=200)
        final_docs = text_splitter.split_documents(md_header_splits)
        
        results = []
        for doc in final_docs:
            # Metadata từ Header Splitter rất giá trị (h1, h2, h3)
            # Ta sẽ đưa nó vào nội dung embedding luôn để tăng độ chính xác tìm kiếm
            header_context = ""
            if "h1" in doc.metadata: header_context += f"{doc.metadata['h1']}. "
            if "h2" in doc.metadata: header_context += f"{doc.metadata['h2']}. "
            if "h3" in doc.metadata: header_context += f"{doc.metadata['h3']}. "
            
            # Nội dung thực tế được embed = Context + Content
            enriched_content = f"{header_context}\n{doc.page_content}"
            
            results.append({
                "content": clean_text(doc.page_content), # Lưu nội dung gốc sạch đẹp để hiển thị
                "embedding_content": clean_text(enriched_content), # Dùng nội dung giàu ngữ nghĩa để embed
                "metadata": {
                    "source": os.path.basename(file_path),
                    "chunk_size": len(doc.page_content),
                    **doc.metadata
                }
            })
            
        return results
    except Exception as e:
        logger.error(f"❌ Lỗi xử lý Markdown {file_path}: {e}")
        return []

def process_file_generic(file_path: str, loader_cls) -> List[Dict]:
    """
    Chiến lược cho PDF/DOCX: Recursive Splitting + Overlap sâu (1200/250).
    """
    try:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        loader = loader_cls(file_path)
        raw_docs = loader.load()
        
        # Merge tất cả page thành 1 text lớn để tránh đứt gãy câu giữa các trang (PDF footer issue)
        full_text = "\n".join([d.page_content for d in raw_docs])
        cleaned_text = clean_text(full_text)
        
        # Cắt đoạn: Chunk size lớn hơn MD vì văn bản thường liên tục
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=250, # Overlap lớn để giữ mạch văn
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_text(cleaned_text)
        
        results = []
        for i, chunk in enumerate(chunks):
            results.append({
                "content": chunk,
                "embedding_content": chunk, # PDF không có header structured như MD
                "metadata": {
                    "source": os.path.basename(file_path),
                    "page_estimated": i // 3 + 1 # Ước lượng trang
                }
            })
        return results
    except Exception as e:
        logger.error(f"❌ Lỗi xử lý file {file_path}: {e}")
def process_pdf_advanced(file_path: str) -> List[Dict]:
    """
    Advanced PDF Processor sử dụng `pdfplumber` để giữ layout tốt hơn.
    """
    try:
        import pdfplumber
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        full_text = ""
        logger.info(f"📄 Đang đọc PDF bằng pdfplumber: {os.path.basename(file_path)}")
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # extract_text(x_tolerance=1) giúp join text cùng dòng tốt hơn
                text = page.extract_text(x_tolerance=2, y_tolerance=2) 
                if text:
                    full_text += text + "\n\n"
        
        cleaned_text = clean_text(full_text)
        
        # Chunking: Chiến lược Overlap sâu cho PDF
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=250,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_text(cleaned_text)
        
        results = []
        for i, chunk in enumerate(chunks):
            results.append({
                "content": chunk,
                "embedding_content": chunk, 
                "metadata": {
                    "source": os.path.basename(file_path),
                    "page_estimated": i // 3 + 1
                }
            })
        return results

    except ImportError:
        logger.error("❌ Chưa cài pdfplumber. Fallback sang generic loader.")
        return []
    except Exception as e:
        logger.error(f"❌ Custom PDF Error: {e}")
        return []

# --- 3. MAIN INGEST FLOW ---

async def ingest():
    v_db = VectorDatabase(db_name=DB_NAME)
    logger.info("🚀 Bắt đầu Smart Ingest (MD, PDF, DOCX)...")

    try:
        from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
    except ImportError:
        logger.error("❌ Thiếu 'langchain-community'. Bỏ qua file PDF/DOCX.")
        PyPDFLoader = None
        Docx2txtLoader = None
    
    # 1. Load config để lấy danh sách di tích (Chúng ta sẽ map file với di tích qua tên file hoặc thư mục)
    config = get_heritage_config()
    
    # 2. Quét thư mục data/documents (Nếu chưa có thì tạo)
    if not os.path.exists(SOURCE_DIR):
        os.makedirs(SOURCE_DIR)
        logger.info(f"📂 Đã tạo thư mục '{SOURCE_DIR}'. Hãy bỏ file .md/.pdf/.docx vào đây (đặt tên trùng site_key, vd: hoang_thanh.pdf).")
        
    # Lấy danh sách file trong thư mục
    files = os.listdir(SOURCE_DIR)
    
    total_chunks = 0
    
    for filename in files:
        file_path = os.path.join(SOURCE_DIR, filename)
        if not os.path.isfile(file_path): continue
        
        # Xác định site_key qua tên file (vd: hoang_thanh_v2.pdf -> hoang_thanh)
        # Logic đơn giản: Lấy phần đầu tên file làm key. Cần khớp với config.json
        matched_key = None
        matched_culture_type = "di_tich"
        
        for key in config.keys():
            if key in filename:  # Logic linh hoạt: Chỉ cần tên file CHỨA key là được
                matched_key = key
                matched_culture_type = config[key].get("culture_type", "di_tich")
                break
        
        if not matched_key:
            logger.warning(f"⏩ File '{filename}' không khớp key nào trong monuments.json (VD: phải chứa 'hoang_thanh'). Bỏ qua.")
            continue

        # Get collection from config (default to 'culture' if not found)
        target_collection = config[matched_key].get("collection", COLLECTION_NAME)

        # Check trùng trong DB
        existing_count = v_db.count_documents(target_collection, {
            "metadata.site_key": matched_key, 
            "metadata.source": filename
        })
        if existing_count > 0:
            logger.info(f"🔄 File '{filename}' đã nạp. Xóa bản cũ để nạp bản mới...")
            v_db.collection.delete_many({
                "metadata.site_key": matched_key, 
                "metadata.source": filename
            })
            
        logger.info(f"📄 Đang xử lý file: {filename} (Site: {matched_key}) -> Collection: {target_collection}...")
        
        # Xử lý theo loại file
        ext = os.path.splitext(filename)[1].lower()
        processed_docs = []
        
        if ext == ".md":
            processed_docs = process_markdown(file_path)
        elif ext == ".pdf":
            if PyPDFLoader: processed_docs = process_file_generic(file_path, PyPDFLoader)
        elif ext == ".docx":
            if Docx2txtLoader: processed_docs = process_file_generic(file_path, Docx2txtLoader)
        else:
            continue
            
        if not processed_docs:
            logger.warning(f"⚠️ Không trích xuất được nội dung từ {filename}.")
            continue
            
        # 3. Embedding & Insert
        to_insert_list = []
        
        # Batch embedding để nhanh hơn
        embed_texts = [d["embedding_content"] for d in processed_docs]
        vectors = local_embedder.encode(embed_texts).tolist()
        
        # Determine the dynamic type field based on collection
        # Default to 'culture_type' if unknown
        type_field_map = {
            "culture": "culture_type",
            "heritage": "heritage_type",
            "history": "history_type"
        }
        dynamic_type_field = type_field_map.get(target_collection, "culture_type")
        
        for i, doc in enumerate(processed_docs):
            json_doc = {
                "content": doc["content"],
                "embedding": vectors[i],
                dynamic_type_field: matched_key, # Dynamic field: heritage_type='hoang_thanh'
                "metadata": {
                    "site_key": matched_key,
                    "source": filename,
                    "file_type": ext,
                    **doc["metadata"]
                }
            }
            to_insert_list.append(json_doc)
            
        if to_insert_list:
            v_db.insert_many(target_collection, to_insert_list)
            total_chunks += len(to_insert_list)
            logger.info(f"✅ Đã thêm {len(to_insert_list)} chunks từ {filename}.")

    # --- NGUỒN PHỤ: NẠP TỪ MONUMENTS.JSON DESCRIPTION (Nếu chưa có file chi tiết) ---
    logger.info("--- Kiểm tra mô tả ngắn trong monuments.json ---")
    for key, data in config.items():
        # Get target collection & type field
        target_col = data.get("collection", COLLECTION_NAME)
        
        # Determine dynamic type field
        type_field_map = {
            "culture": "culture_type",
            "heritage": "heritage_type",
            "history": "history_type"
        }
        dynamic_type_field = type_field_map.get(target_col, "culture_type")

        # Kiểm tra xem site này đã có data từ file document chưa
        doc_count = v_db.count_documents(target_col, {"metadata.site_key": key, "metadata.file_type": {"$in": [".pdf", ".md", ".docx"]}})
        
        if doc_count > 0:
            continue # Ưu tiên file document chi tiết hơn description ngắn
            
        # Check description existing
        desc_count = v_db.count_documents(target_col, {"metadata.site_key": key, "metadata.source": "monuments.json"})
        if desc_count > 0: continue
        
        desc = data.get("context_description", "")
        if desc:
            logger.info(f"📝 Nạp mô tả ngắn cho '{data['name']}' vào '{target_col}'...")
            # Embed description
            full_text = f"{data['name']}.\n{desc}"
            vec = local_embedder.encode([full_text]).tolist()[0]
            
            v_db.insert_many(target_col, [{
                "content": desc,
                "embedding": vec,
                dynamic_type_field: key,
                "metadata": {"site_key": key, "source": "monuments.json", "level": 0}
            }])
            total_chunks += 1

    logger.info(f"✨ Hoàn tất! Tổng cộng thêm {total_chunks} chunks mới.")

async def ingest_file(file_path: str, site_key: str):
    """
    API Helper: Ingest một file cụ thể cho di tích cụ thể.
    """
    v_db = VectorDatabase(db_name=DB_NAME)
    filename = os.path.basename(file_path)
    
    # Get config for this site
    config = get_heritage_config()
    site_config = config.get(site_key, {})
    target_collection = site_config.get("collection", COLLECTION_NAME)
    
    # Determine dynamic type field
    type_field_map = {
        "culture": "culture_type",
        "heritage": "heritage_type",
        "history": "history_type"
    }
    dynamic_type_field = type_field_map.get(target_collection, "culture_type")
    
    # 1. CƠ CHẾ OVERWRITE: Kiểm tra và xóa dữ liệu cũ
    existing_count = v_db.count_documents(target_collection, {
        "metadata.site_key": site_key, 
        "metadata.source": filename
    })
    
    if existing_count > 0:
        logger.info(f"🔄 File '{filename}' đã tồn tại trong '{target_collection}'. Đang xóa {existing_count} chunks cũ...")
        # Xóa chunks cũ (Using raw collection access or a new method if available, defaulting to raw)
        # Note: v_db wrapper usually handles one collection. We need to be careful if v_db is tied to one collection.
        # Looking at v_db init: `self.collection = db[collection_name]`. 
        # But we are calling methods with `collection_name` arg in `ingest()` loop?
        # Let's check `count_documents` signature. It takes `collection_name`.
        # So we should use `db[target_collection].delete_many`.
        v_db.db[target_collection].delete_many({
            "metadata.site_key": site_key, 
            "metadata.source": filename
        })
        logger.info("🗑️ Đã xóa dữ liệu cũ.")

    # Process
    ext = os.path.splitext(filename)[1].lower()
    processed_docs = []
    
    # Lazy Import Loaders
    try:
        # from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
        from langchain_community.document_loaders.word_document import Docx2txtLoader
        from langchain_community.document_loaders.pdf import PyPDFLoader
    except ImportError:
         return {"status": "error", "message": "Thiếu thư viện 'langchain-community'. Hãy cài đặt!"}

    if ext == ".md":
        processed_docs = process_markdown(file_path)
    elif ext == ".pdf":
        if PyPDFLoader: processed_docs = process_file_generic(file_path, PyPDFLoader)
    elif ext == ".docx":
        if Docx2txtLoader: processed_docs = process_file_generic(file_path, Docx2txtLoader)
    
    if not processed_docs:
        return {"status": "error", "message": f"Không đọc được nội dung file {filename}."}
        
    # Embed & Insert
    embed_texts = [d["embedding_content"] for d in processed_docs]
    vectors = local_embedder.encode(embed_texts).tolist()
    
    to_insert_list = []
    
    for i, doc in enumerate(processed_docs):
        json_doc = {
            "content": doc["content"],
            "embedding": vectors[i],
            dynamic_type_field: site_key, # Dynamic filter key
            "metadata": {
                "site_key": site_key,
                "source": filename,
                "file_type": ext,
                **doc["metadata"]
            }
        }
        to_insert_list.append(json_doc)
        
    if to_insert_list:
        v_db.insert_many(target_collection, to_insert_list)
        return {"status": "success", "chunks": len(to_insert_list)}
        
    return {"status": "error", "message": "Không có chunk nào được tạo."}

async def ingest_file_to_collection_advanced(
    file_path: str, 
    collection_name: str, 
    culture_type: str,
    culture_type_name: str,
    ingest_mode: str = "append" # "append" or "replace"
):
    print(" >>>>>>>>> DEBUG: Started Ingest Function <<<<<<<<< ") 
    """
    [ADVANCED] Ingest file vào collection tùy chọn với culture_type cụ thể.
    """
    # 0. Init DB
    v_db = VectorDatabase(db_name=DB_NAME)
    
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    
    logger.info(f"📥 [ADVANCED INGEST] File: {filename} → Collection: {collection_name}, Type: {culture_type}, Mode: {ingest_mode}")
    
    # 1. Loaders
    try:
        from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
    except ImportError:
         return {"status": "error", "message": "Thiếu thư viện 'langchain-community'. Hãy cài đặt!"}

    # 2. Parse document
    print(f"DEBUG: Parsing {ext} file...")
    processed_docs = []
    try:
        if ext == '.pdf':
            # Ưu tiên dùng Advanced PDF Processor (Layout-aware)
            try: 
                 processed_docs = process_pdf_advanced(file_path)
            except: pass
            
            # Fallback nếu advanced fail
            if not processed_docs:
                logger.warning("Falling back to standard PDF loader...")
                processed_docs = process_file_generic(file_path, PyPDFLoader)
                
        elif ext == '.docx':
            processed_docs = process_file_generic(file_path, Docx2txtLoader)
        elif ext == '.md':
            processed_docs = process_markdown(file_path)
        else:
            return {"status": "error", "message": f"Unsupported file type: {ext}"}
        
        logger.info(f"✅ Parsed {len(processed_docs)} docs from {filename}")

    except Exception as e:
         logger.error(f"❌ Parse Error: {e}")
         return {"status": "error", "message": f"Parse Error: {e}"}
    
    if not processed_docs:
        return {"status": "error", "message": "Không parse được nội dung từ file."}
    
    # Determine dynamic type field
    type_field_map = {
        "culture": "culture_type",
        "heritage": "heritage_type",
        "history": "history_type"
    }
    dynamic_type_field = type_field_map.get(collection_name, "culture_type")

    # DELETE EXISTING IF "REPLACE" MODE
    if ingest_mode == "replace":
        if hasattr(v_db, 'delete_many'):
             try:
                 deleted_count = v_db.delete_many(collection_name, {dynamic_type_field: culture_type})
                 logger.info(f"🗑️ Deleted {deleted_count} existing docs for {dynamic_type_field}={culture_type} in {collection_name}")
             except Exception as e:
                 logger.error(f"❌ Delete Error: {e}")
        else:
             logger.warning("Warning: v_db.delete_many not found. Skipping delete.")

    # Embed
    try:
        embed_texts = [doc["embedding_content"] for doc in processed_docs]
        vectors = local_embedder.encode(embed_texts).tolist()
        logger.info(f"✅ Created {len(vectors)} embeddings")
    except Exception as e:
        logger.error(f"❌ Embedding Error: {e}")
        return {"status": "error", "message": f"Embedding Error: {e}"}

    # Build documents
    to_insert = []
    for i, doc in enumerate(processed_docs):
        json_doc = {
            "content": doc["content"],
            "embedding": vectors[i],
            dynamic_type_field: culture_type,  
            "metadata": {
                "site_key": culture_type,  
                "source": filename,
                "file_type": ext,
                "ingest_time": os.getenv("INGEST_ID", "manual"),
                **doc["metadata"]
            }
        }
        to_insert.append(json_doc)
    
    # Insert vào collection (dynamic)
    inserted_count = 0
    if to_insert:
        logger.info(f"🚀 Inserting {len(to_insert)} chunks into MongoDB Collection '{collection_name}'...")
        try:
            inserted_count = v_db.insert_many(collection_name, to_insert)
            logger.info(f"✅ Inserted {inserted_count} docs into {collection_name}")
        except Exception as e:
            logger.error(f"❌ DB Insert Error: {e}")
            return {"status": "error", "message": f"DB Insert Error: {e}"}

    return {"status": "success", "chunks": inserted_count, "mode": ingest_mode}

if __name__ == "__main__":
    asyncio.run(ingest())