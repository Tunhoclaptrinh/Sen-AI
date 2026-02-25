"""
build_graph.py — Script chạy 1 lần để build Knowledge Graph
từ toàn bộ chunks đã có trong MongoDB.

Cách dùng:
    python build_graph.py
    python build_graph.py --site hoang_thanh   # Chỉ build cho 1 di tích
    python build_graph.py --dry-run             # Chỉ xem kết quả, không lưu
"""

import os
import json
import asyncio
import logging
import argparse
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────
BATCH_SIZE = 5          # Số chunks xử lý mỗi lần gọi GPT
MAX_TRIPLES_PER_CHUNK = 10
COLLECTIONS_TO_SCAN = ["heritage", "culture", "history"]


# ─── GPT Extraction ───────────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích văn bản lịch sử và văn hóa Việt Nam.
Nhiệm vụ: Trích xuất các quan hệ có ý nghĩa từ đoạn văn bản được cung cấp.

QUY TẮC:
1. Chỉ trích xuất quan hệ RÕ RÀNG có trong văn bản, KHÔNG suy diễn thêm
2. Subject và Object phải là danh từ/tên riêng cụ thể (địa danh, nhân vật, triều đại, sự kiện)
3. Relation phải là động từ/quan hệ ngắn gọn bằng TIẾNG VIỆT IN HOA với dấu gạch dưới

CÁC LOẠI RELATION HỢP LỆ:
- XÂY_BỞI, ĐƯỢC_XÂY_DỰNG_NĂM, THUỘC_TRIỀU_ĐẠI
- CÓ_NHÂN_VẬT, LÀ_VUA, LÀ_TƯỚNG, LÀ_NHÀ_THƠ
- NẰM_TẠI, THUỘC_DI_TÍCH, CÓ_CÔNG_TRÌNH
- ĐƯỢC_UNESCO_CÔNG_NHẬN_NĂM, LÀ_DI_SẢN
- CHIẾN_THẮNG, THẤT_BẠI_TRƯỚC, ĐỒNG_MINH_CỦA
- LIÊN_QUAN_ĐẾN, KẾ_THỪA_TỪ, THAY_THẾ_BỞI
- RA_ĐỜI_NĂM, KẾT_THÚC_NĂM, DIỄN_RA_NĂM

VÍ DỤ OUTPUT (JSON array):
[
  {"s": "Hoàng Thành Thăng Long", "r": "XÂY_BỞI", "o": "Lý Thái Tổ", "confidence": 0.95},
  {"s": "Lý Thái Tổ", "r": "THUỘC_TRIỀU_ĐẠI", "o": "Nhà Lý", "confidence": 0.98},
  {"s": "Nhà Lý", "r": "RA_ĐỜI_NĂM", "o": "1009", "confidence": 0.9}
]

Trả về JSON array THUẦN TÚY, không markdown, không giải thích."""


async def extract_triples_from_chunk(
    chunk_text: str,
    openai_client: AsyncOpenAI,
    site_key: str = ""
) -> list:
    """
    Dùng GPT extract quan hệ từ 1 đoạn văn bản.
    Returns: [{"s": ..., "r": ..., "o": ..., "confidence": ...}]
    """
    if not chunk_text or len(chunk_text.strip()) < 30:
        return []

    user_prompt = f"""Di tích/Chủ đề: {site_key}

Văn bản:
{chunk_text[:2000]}

Trích xuất tối đa {MAX_TRIPLES_PER_CHUNK} quan hệ quan trọng nhất."""

    try:
        res = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=800
        )

        raw = res.choices[0].message.content.strip()

        # Clean markdown code blocks nếu có
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        triples = json.loads(raw)
        if isinstance(triples, list):
            return triples
        return []

    except json.JSONDecodeError as e:
        logger.warning(f"   ⚠️ JSON parse error: {e} | Raw: {raw[:100]}")
        return []
    except Exception as e:
        logger.error(f"   ❌ GPT extraction error: {e}")
        return []


async def extract_triples_batch(
    chunks: list,
    openai_client: AsyncOpenAI,
    site_key: str
) -> list:
    """Xử lý nhiều chunks song song."""
    tasks = [
        extract_triples_from_chunk(c["content"], openai_client, site_key)
        for c in chunks
        if c.get("content")
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_triples = []
    for r in results:
        if isinstance(r, list):
            all_triples.extend(r)
    return all_triples


# ─── Main Build Logic ─────────────────────────────────────────────────────────

async def build_graph(target_site: str = None, dry_run: bool = False):
    """
    Đọc toàn bộ chunks từ MongoDB → extract triples → lưu vào knowledge_graph.
    """
    from app.core.vector_db import VectorDatabase
    from app.core.graph_store import GraphStore
    from app.core.config_loader import get_heritage_config

    logger.info("=" * 60)
    logger.info("🕸️  BUILD KNOWLEDGE GRAPH — Hybrid RAG")
    logger.info("=" * 60)

    # Init
    v_db = VectorDatabase(db_name="vector_db")
    graph = GraphStore(v_db.db)
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    config = get_heritage_config()

    # Filter sites
    if target_site:
        sites = {target_site: config.get(target_site, {})}
        logger.info(f"🎯 Target site: {target_site}")
    else:
        sites = config
        logger.info(f"🌐 Processing all {len(sites)} sites")

    total_triples = 0

    for site_key, site_data in sites.items():
        collection = site_data.get("collection", "culture")
        site_name = site_data.get("name", site_key)

        logger.info(f"\n{'─'*50}")
        logger.info(f"📍 Site: {site_name} ({site_key}) → Collection: {collection}")

        # Xác định filter field
        filter_map = {
            "heritage": "heritage_type",
            "culture": "culture_type",
            "history": "history_type"
        }
        type_field = filter_map.get(collection, "culture_type")

        # Đọc chunks từ MongoDB
        if v_db.db is None:
            logger.error("❌ MongoDB không kết nối được!")
            continue

        chunks = list(
            v_db.db[collection].find(
                {type_field: site_key},
                {"_id": 0, "content": 1, "metadata": 1}
            )
        )

        if not chunks:
            logger.warning(f"   ⚠️ Không có chunks nào cho {site_key} trong '{collection}'")
            continue

        logger.info(f"   📄 Tìm thấy {len(chunks)} chunks → Extract triples...")

        # Xóa triples cũ của site này (để rebuild)
        if not dry_run:
            old_count = graph.count(site_key)
            if old_count > 0:
                v_db.db["knowledge_graph"].delete_many({"site_key": site_key})
                logger.info(f"   🗑️  Đã xóa {old_count} triples cũ")

        # Extract theo batch
        site_triples = []
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

            logger.info(f"   🤖 Batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
            triples = await extract_triples_batch(batch, openai_client, site_name)
            site_triples.extend(triples)

            # Rate limit
            await asyncio.sleep(0.5)

        logger.info(f"   ✅ Extracted {len(site_triples)} triples")

        if dry_run:
            logger.info(f"   [DRY RUN] Sample triples:")
            for t in site_triples[:5]:
                logger.info(f"      {t.get('s')} [{t.get('r')}] {t.get('o')}")
        else:
            # Lưu vào MongoDB
            source_name = f"build_graph:{site_key}"
            saved = graph.insert_triples(site_triples, site_key, source_name)
            total_triples += saved
            logger.info(f"   💾 Saved {saved} triples to 'knowledge_graph' collection")

    logger.info(f"\n{'='*60}")
    if dry_run:
        logger.info(f"✨ [DRY RUN] Done! (No data written)")
    else:
        logger.info(f"✨ Done! Total triples saved: {total_triples}")
    logger.info(f"{'='*60}\n")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build Knowledge Graph từ MongoDB chunks"
    )
    parser.add_argument(
        "--site",
        type=str,
        default=None,
        help="Chỉ build cho 1 site cụ thể (vd: hoang_thanh)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview kết quả, không lưu vào DB"
    )
    args = parser.parse_args()

    asyncio.run(build_graph(target_site=args.site, dry_run=args.dry_run))
