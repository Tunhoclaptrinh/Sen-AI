import requests
from bs4 import BeautifulSoup
import time
import re

# Cấu hình danh mục
categories = {
    "Di tích": "https://hoangthanhthanglong.vn/hoang-thanh-thang-long/di-tich/",
    "Di vật": "https://hoangthanhthanglong.vn/hoang-thanh-thang-long/di-vat/",
    "Kiến trúc": "https://hoangthanhthanglong.vn/hoang-thanh-thang-long/kien-truc/",
    "Nghiên cứu khoa học": "https://hoangthanhthanglong.vn/hoang-thanh-thang-long/nghien-cuu-khoa-hoc/",
    "Nhân vật": "https://hoangthanhthanglong.vn/hoang-thanh-thang-long/nhan-vat/",
    "Thời kỳ": "http://hoangthanhthanglong.vn/hoang-thanh-thang-long/thoi-ky/",
    "Hoàng thành về đêm": "https://hoangthanhthanglong.vn/ngam-nhin-hoang-thanh-thang-long-ve-dem/"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_noise_text(text):
    """Xóa trích dẫn [1], ghi chú ảnh 'Ảnh 1:', và các nguồn tham khảo nhiễu"""
    
    # 1. Xóa trích dẫn số dạng [1], [2], [123]
    text = re.sub(r'\[\d+\]', '', text)
    
    # 2. Xóa các URL trần
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # 3. Tách dòng để xử lý từng dòng một
    lines = text.split('\n')
    clean_lines = []
    
    # Các mẫu nhận diện ghi chú ảnh và nguồn nhiễu
    # Xử lý: Ảnh 1, Hình 1, Đồ họa 1, (Ảnh: ...), v.v.
    photo_note_pattern = re.compile(r'^(Ảnh|Hình|Đồ họa|Sơ đồ)\s*\d+\s*[:.-].*', re.IGNORECASE)
    
    noise_keywords = [
        "kí hiệu:", "Trung tâm bảo tồn", "Xem bài", "Hồng Đức bản đồ", 
        "Đông Dương văn khố", "nguồn:", "tác giả:", "ảnh:", "tư liệu"
    ]
    
    for line in lines:
        line_strip = line.strip()
        
        # Bỏ qua dòng trống
        if not line_strip:
            continue
            
        # Bỏ qua dòng là ghi chú ảnh (ví dụ: "Ảnh 1: Toàn cảnh Đoan Môn")
        if photo_note_pattern.match(line_strip):
            continue
            
        # Bỏ qua dòng chứa từ khóa nhiễu và có độ dài ngắn (thường là ghi chú hoặc nguồn)
        if any(key.lower() in line_strip.lower() for key in noise_keywords) and len(line_strip) < 120:
            continue
            
        clean_lines.append(line_strip)
        
    return "\n\n".join(clean_lines)

def table_to_linearized_text(table_tag):
    """Chuyển bảng thành văn bản cộng dồn tiêu đề"""
    rows = table_tag.find_all('tr')
    if not rows: return ""
    header_cells = rows[0].find_all(['th', 'td'])
    headers = [cell.get_text(strip=True) for cell in header_cells]
    
    linearized_output = []
    for row in rows[1:]:
        cells = row.find_all(['td'])
        if len(cells) == len(headers):
            row_data = [f"{headers[i]}: {cells[i].get_text(strip=True)}" for i in range(len(headers)) if cells[i].get_text(strip=True)]
            if row_data:
                linearized_output.append(". ".join(row_data) + ".")
    return "\n\n" + "\n\n".join(linearized_output) + "\n\n"

def get_full_content(url):
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        content_div = soup.select_one('.entry-content')
        
        if content_div:
            # Xóa các thành phần HTML rác
            for garbage in content_div.find_all(['img', 'figure', 'figcaption', 'script', 'style', 'iframe']):
                garbage.decompose()
            
            # Xử lý bảng
            for table in content_div.find_all('table'):
                table.replace_with(table_to_linearized_text(table))
            
            # Lấy text thô với separator để dễ tách dòng
            raw_text = content_div.get_text(separator="\n", strip=True)
            
            # Làm sạch sâu văn bản
            return clean_noise_text(raw_text)
    except:
        return ""
    return ""

def scrape_category(cat_name, start_url, f):
    current_url = start_url
    page_num = 1
    f.write(f"## DANH MỤC: {cat_name.upper()}\n\n")
    
    while current_url:
        print(f"--- Đang quét {cat_name}: Trang {page_num} ---")
        try:
            response = requests.get(current_url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('li.post-item')
            
            if not articles: break
            
            for art in articles:
                title_tag = art.select_one('.post-title a')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    link = title_tag['href']
                    print(f"  > Đang xử lý: {title}")
                    
                    content = get_full_content(link)
                    if content:
                        f.write(f"### {title}\n")
                        f.write(f"**Link:** {link}\n\n")
                        f.write(content + "\n\n")
                        f.write("---\n\n")
                    
                    time.sleep(0.5)
            
            next_page_tag = soup.select_one('li.the-next-page a')
            if next_page_tag and next_page_tag.has_attr('href'):
                current_url = next_page_tag['href']
                page_num += 1
            else: current_url = None
        except: break

def main():
    print("Bắt đầu crawl dữ liệu cực sạch (Không ảnh, Không ghi chú ảnh, Không trích dẫn)...")
    with open("hoang_thanh.md", "w", encoding="utf-8") as f:
        f.write("# DỮ LIỆU HOÀNG THÀNH THĂNG LONG - SẠCH TUYỆT ĐỐI\n\n")
        for name, url in categories.items():
            scrape_category(name, url, f)
    print("\n✅ HOÀN THÀNH! File 'hoang_thanh.md' đã sẵn sàng cho Chunking RAG.")

if __name__ == "__main__":
    main()