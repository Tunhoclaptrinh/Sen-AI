const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');
const mongoose = require('mongoose');

const DB_FILE = path.join(__dirname, '../database/db.json');

// Password đã hash cho "123456"
const hashedPassword = bcrypt.hashSync('123456', 10);

// ==================== SEED DATA FOR SEN ====================
// const seedData = JSON.parse(fs.readFileSync(DB_FILE, 'utf-8'));
// console.log('📂 Loaded DATA from db.json');

// const _legacy_seedData = {
const seedData = {
  // ========== USERS ==========
  "users": [
    {
      "id": 1,
      "name": "Admin Sen",
      "email": "admin@sen.com",
      "password": hashedPassword,
      "phone": "0912345678",
      "role": "admin",
      "bio": "Quản trị viên hệ thống SEN",
      "avatar": "https://ui-avatars.com/api/?name=Admin+Sen&background=4F46E5&color=fff",
      "isActive": true,
      "createdAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "name": "Phạm Văn Tuấn",
      "email": "tuanpham@sen.com",
      "password": hashedPassword,
      "phone": "0987654321",
      "role": "researcher",
      "bio": "Nhà nghiên cứu lịch sử văn hóa",
      "avatar": "https://ui-avatars.com/api/?name=Tuan+Pham&background=F59E0B&color=fff",
      "isActive": true,
      "createdAt": "2024-02-20T14:20:00Z"
    },
    {
      "id": 3,
      "name": "Đỗ Thị Hương",
      "email": "huong.do@sen.com",
      "password": hashedPassword,
      "phone": "0901234567",
      "role": "customer",
      "bio": "Yêu thích lịch sử Việt Nam",
      "avatar": "https://ui-avatars.com/api/?name=Huong+Do&background=EF4444&color=fff",
      "isActive": true,
      "createdAt": "2024-03-10T09:15:00Z"
    },
    {
      "id": 4,
      "name": "Nguyễn Minh Anh",
      "email": "minhanh@sen.com",
      "password": hashedPassword,
      "phone": "0909123456",
      "role": "customer",
      "bio": "Học sinh THPT, đam mê văn hóa dân gian",
      "avatar": "https://ui-avatars.com/api/?name=Minh+Anh&background=8B5CF6&color=fff",
      "isActive": true,
      "createdAt": "2024-04-05T11:00:00Z"
    },
    {
      "id": 5,
      "name": "Lê Văn Nam",
      "email": "vannam@sen.com",
      "password": hashedPassword,
      "phone": "0908765432",
      "role": "customer",
      "bio": "Giáo viên lịch sử",
      "avatar": "https://ui-avatars.com/api/?name=Van+Nam&background=10B981&color=fff",
      "isActive": true,
      "createdAt": "2024-05-12T14:30:00Z"
    }
  ],

  // ========== CULTURAL CATEGORIES ==========
  "cultural_categories": [
    {
      "id": 1,
      "name": "Kiến trúc cổ",
      "icon": "🏯",
      "description": "Công trình kiến trúc lịch sử"
    },
    {
      "id": 2,
      "name": "Mỹ thuật",
      "icon": "🎨",
      "description": "Tranh vẽ, điêu khắc, tác phẩm mỹ thuật"
    },
    {
      "id": 3,
      "name": "Tư liệu lịch sử",
      "icon": "📚",
      "description": "Tài liệu, sách vở, bản thảo"
    },
    {
      "id": 4,
      "name": "Gốm sứ",
      "icon": "🏺",
      "description": "Gốm cổ, sứ, đồ gốm mỹ nghệ"
    },
    {
      "id": 5,
      "name": "Vàng bạc đá quý",
      "icon": "💎",
      "description": "Trang sức, đồ trang trí bằng vàng bạc"
    },
    {
      "id": 6,
      "name": "Dệt may truyền thống",
      "icon": "🧵",
      "description": "Lụa, vải thêu, trang phục truyền thống"
    },
    {
      "id": 7,
      "name": "Di sản phi vật thể",
      "icon": "🎭",
      "description": "Âm nhạc, múa, phong tục truyền thống"
    }
  ],

  // ========== HERITAGE SITES ==========
  "heritage_sites": [
    {
      "id": 1,
      "name": "Thành Phố Hội An",
      "type": "historic_building",
      "cultural_period": "Triều Nguyễn - Pháp thuộc",
      "region": "Quảng Nam",
      "latitude": 15.8801,
      "longitude": 108.3288,
      "address": "Thành phố Hội An, Quảng Nam",
      "year_established": 1624,
      "year_restored": 1999,
      "image": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=600",
      "description": "Hội An là một thành phố cảng cổ, nơi giao thoa văn hóa Đông Tây, được UNESCO công nhận là Di sản Văn hóa Thế giới năm 1999.",
      "rating": 4.9,
      "total_reviews": 523,
      "visit_hours": "8:00 - 17:00",
      "entrance_fee": 120000,
      "is_active": true,
      "unesco_listed": true,
      "significance": "international"
    },
    {
      "id": 2,
      "name": "Hoàng Thành Thăng Long",
      "type": "monument",
      "cultural_period": "Triều Lý",
      "region": "Hà Nội",
      "latitude": 21.0341,
      "longitude": 105.8372,
      "address": "19C Hoàng Diệu, Ba Đình, Hà Nội",
      "year_established": 1010,
      "image": "https://images.unsplash.com/photo-1555169062-013468b47731?w=600",
      "description": "Hoàng Thành Thăng Long là trung tâm quyền lực của Việt Nam trong hơn 13 thế kỷ, từ thế kỷ 11 đến thế kỷ 19.",
      "rating": 4.7,
      "total_reviews": 892,
      "visit_hours": "8:00 - 17:00",
      "entrance_fee": 30000,
      "is_active": true,
      "unesco_listed": true,
      "significance": "international"
    },
    {
      "id": 3,
      "name": "Bảo tàng Thành phố Hồ Chí Minh",
      "type": "museum",
      "cultural_period": "Hiện đại",
      "region": "TP. Hồ Chí Minh",
      "latitude": 10.7929,
      "longitude": 106.6955,
      "address": "65 Lý Tự Trọng, Q. 1, TP. Hồ Chí Minh",
      "year_established": 1956,
      "image": "https://images.unsplash.com/photo-1564399579883-451a5d44ec08?w=600",
      "description": "Bảo tàng lưu giữ nhiều hiện vật quý giá về lịch sử, văn hóa và cách mạng Việt Nam.",
      "rating": 4.5,
      "total_reviews": 234,
      "visit_hours": "8:00 - 17:00",
      "entrance_fee": 50000,
      "is_active": true,
      "unesco_listed": false,
      "significance": "national"
    },
    {
      "id": 4,
      "name": "Khu khảo cổ Óc Eo",
      "type": "archaeological_site",
      "cultural_period": "Thời kỳ Óc Eo",
      "region": "An Giang",
      "latitude": 10.1333,
      "longitude": 104.7667,
      "address": "Xã Tân Trung, huyện Tịnh Biên, An Giang",
      "year_established": 150,
      "year_restored": 2000,
      "image": "https://images.unsplash.com/photo-1553484771-ee0bdc25ef14?w=600",
      "description": "Óc Eo là một trong những trung tâm thương mại quốc tế quan trọng của nền văn minh Phù Nam thế kỷ 1-7.",
      "rating": 4.3,
      "total_reviews": 145,
      "visit_hours": "8:00 - 16:30",
      "entrance_fee": 30000,
      "is_active": true,
      "unesco_listed": false,
      "significance": "national"
    },
    {
      "id": 5,
      "name": "Chùa Một Cột",
      "type": "monument",
      "cultural_period": "Triều Lý",
      "region": "Hà Nội",
      "latitude": 21.0356,
      "longitude": 105.8336,
      "address": "Chùa Một Cột, Ba Đình, Hà Nội",
      "year_established": 1049,
      "image": "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=600",
      "description": "Chùa Một Cột được xây dựng dưới thời vua Lý Thái Tông, là biểu tượng kiến trúc độc đáo của Hà Nội.",
      "rating": 4.6,
      "total_reviews": 312,
      "visit_hours": "7:00 - 18:00",
      "entrance_fee": 0,
      "is_active": true,
      "unesco_listed": false,
      "significance": "national"
    },
    {
      "id": 6,
      "name": "Văn Miếu - Quốc Tử Giám",
      "type": "historic_building",
      "cultural_period": "Triều Lý",
      "region": "Hà Nội",
      "latitude": 21.0277,
      "longitude": 105.8355,
      "address": "58 Quốc Tử Giám, Đống Đa, Hà Nội",
      "year_established": 1070,
      "image": "https://images.unsplash.com/photo-1528127269322-539801943592?w=600",
      "description": "Văn Miếu - Quốc Tử Giám là trường đại học đầu tiên của Việt Nam, nơi thờ Khổng Tử và các bậc hiền tài.",
      "rating": 4.8,
      "total_reviews": 756,
      "visit_hours": "8:00 - 17:00",
      "entrance_fee": 30000,
      "is_active": true,
      "unesco_listed": false,
      "significance": "national"
    },
    {
      "id": 7,
      "name": "Cố đô Huế",
      "type": "historic_building",
      "cultural_period": "Triều Nguyễn",
      "region": "Thừa Thiên Huế",
      "latitude": 16.4637,
      "longitude": 107.5909,
      "address": "Thành phố Huế, Thừa Thiên Huế",
      "year_established": 1802,
      "year_restored": 1993,
      "image": "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=600",
      "description": "Cố đô Huế là kinh đô của triều Nguyễn, nơi lưu giữ nhiều di tích kiến trúc cung đình đặc sắc.",
      "rating": 4.9,
      "total_reviews": 1024,
      "visit_hours": "7:00 - 17:30",
      "entrance_fee": 200000,
      "is_active": true,
      "unesco_listed": true,
      "significance": "international"
    }
  ],

  // ========== ARTIFACTS ==========
  "artifacts": [
    {
      "id": 1,
      "name": "Bức tranh sơn dầu 'Phố cổ Hội An'",
      "description": "Tranh sơn dầu thế kỷ 20 mô tả quang cảnh phố cổ Hội An với những dãy nhà cổ kính, đèn lồng rực rỡ.",
      "heritage_site_id": 1,
      "category_id": 2,
      "artifact_type": "painting",
      "year_created": 1985,
      "creator": "Nguyễn Tường",
      "material": "Sơn dầu trên vải",
      "dimensions": "100 x 80 cm",
      "weight": 5,
      "condition": "excellent",
      "image": "https://images.unsplash.com/photo-1578321272176-b7899d21b5d5?w=600",
      "is_on_display": true,
      "location_in_site": "Phòng tranh 1, Tầng 1"
    },
    {
      "id": 2,
      "name": "Bộ đồ gốm Thương Tín",
      "description": "Bộ gốm sứ thương mại từ thế kỷ 15-16, thời kỳ Hội An là cảng thương mại sầm uất.",
      "heritage_site_id": 1,
      "category_id": 4,
      "artifact_type": "pottery",
      "year_created": 1500,
      "material": "Gốm sứ xanh",
      "dimensions": "Cao 30cm",
      "condition": "good",
      "image": "https://images.unsplash.com/photo-1578500494198-246f612d03b3?w=600",
      "is_on_display": true,
      "location_in_site": "Phòng gốm, Tầng 2"
    },
    {
      "id": 3,
      "name": "Trống đồng Đông Sơn",
      "description": "Trống đồng văn hóa Đông Sơn, biểu tượng của nền văn minh cổ Việt Nam.",
      "heritage_site_id": 4,
      "category_id": 4,
      "artifact_type": "bronze",
      "year_created": -500,
      "material": "Đồng",
      "dimensions": "Đường kính 63cm",
      "condition": "good",
      "image": "https://images.unsplash.com/photo-1582555172866-f73bb12a2ab3?w=600",
      "is_on_display": true,
      "location_in_site": "Khu vực chính"
    },
    {
      "id": 4,
      "name": "Bia Tiến sĩ đá xanh",
      "description": "Bia đá khắc tên các tiến sĩ đỗ đại khoa thi Nho học thời phong kiến.",
      "heritage_site_id": 6,
      "category_id": 3,
      "artifact_type": "stone",
      "year_created": 1442,
      "material": "Đá xanh",
      "dimensions": "Cao 1.2m",
      "condition": "good",
      "image": "https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=600",
      "is_on_display": true,
      "location_in_site": "Sân chính"
    },
    {
      "id": 5,
      "name": "Áo dài truyền thống",
      "description": "Áo dài lụa thêu tay thế kỷ 19, mẫu áo dài cung đình triều Nguyễn.",
      "heritage_site_id": 7,
      "category_id": 6,
      "artifact_type": "textile",
      "year_created": 1850,
      "material": "Lụa thêu",
      "dimensions": "150 x 60 cm",
      "condition": "fair",
      "image": "https://images.unsplash.com/photo-1617127365659-c47fa864d8bc?w=600",
      "is_on_display": true,
      "location_in_site": "Phòng trang phục"
    }
  ],

  // ========== TIMELINES ==========
  "timelines": [
    {
      "id": 1,
      "title": "Thành lập Hội An",
      "description": "Hội An được thành lập như một cảng thương mại quan trọng, thu hút thương nhân từ nhiều quốc gia.",
      "year": 1624,
      "heritage_site_id": 1,
      "category": "founded",
      "image": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=600"
    },
    {
      "id": 2,
      "title": "Tu bổ Phố cổ",
      "description": "Bắt đầu công trình tu bổ toàn diện phố cổ Hội An để bảo tồn di sản.",
      "year": 1999,
      "heritage_site_id": 1,
      "category": "restored",
      "image": "https://images.unsplash.com/photo-1578107982254-eb158fc3a0e7?w=600"
    },
    {
      "id": 3,
      "title": "UNESCO công nhận",
      "description": "Phố cổ Hội An được UNESCO công nhận là Di sản Văn hóa Thế giới.",
      "year": 1999,
      "heritage_site_id": 1,
      "category": "recognition",
      "image": "https://images.unsplash.com/photo-1579722821273-8a36ae95db51?w=600"
    },
    {
      "id": 4,
      "title": "Xây dựng Hoàng Thành",
      "description": "Vua Lý Thái Tổ dời đô về Thăng Long và xây dựng Hoàng Thành.",
      "year": 1010,
      "heritage_site_id": 2,
      "category": "founded",
      "image": "https://images.unsplash.com/photo-1555169062-013468b47731?w=600"
    },
    {
      "id": 5,
      "title": "UNESCO công nhận Hoàng Thành",
      "description": "Hoàng Thành Thăng Long được UNESCO công nhận là Di sản Văn hóa Thế giới.",
      "year": 2010,
      "heritage_site_id": 2,
      "category": "recognition",
      "image": "https://images.unsplash.com/photo-1555169062-013468b47731?w=600"
    }
  ],

  // ========== EXHIBITIONS ==========
  "exhibitions": [
    {
      "id": 1,
      "name": "Hành trình Hội An qua 400 năm",
      "description": "Triển lãm lịch sử toàn diện về Hội An từ thế kỷ 17 đến nay, với hơn 200 hiện vật quý giá.",
      "heritage_site_id": 1,
      "theme": "Lịch sử & Văn hóa Hội An",
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2026-12-31T23:59:59Z",
      "curator": "ThS. Trần Văn An",
      "image": "https://images.unsplash.com/photo-1564399579883-451a5d44ec08?w=600",
      "artifact_ids": [1, 2],
      "is_active": true
    },
    {
      "id": 2,
      "name": "Văn minh Óc Eo bí ẩn",
      "description": "Khám phá nền văn minh Óc Eo cổ đại với các hiện vật khảo cổ độc đáo.",
      "heritage_site_id": 4,
      "theme": "Khảo cổ học",
      "start_date": "2024-03-01T00:00:00Z",
      "end_date": "2026-08-31T23:59:59Z",
      "curator": "GS. Lê Văn Minh",
      "image": "https://images.unsplash.com/photo-1553484771-ee0bdc25ef14?w=600",
      "artifact_ids": [3],
      "is_active": true
    }
  ],

  // ========== FAVORITES ==========
  "favorites": [
    {
      "id": 1,
      "user_id": 3,
      "type": "heritage_site",
      "reference_id": 1,
      "created_at": "2024-10-15T10:00:00Z"
    },
    {
      "id": 2,
      "user_id": 3,
      "type": "artifact",
      "reference_id": 1,
      "created_at": "2024-10-22T11:45:00Z"
    },
    {
      "id": 3,
      "user_id": 4,
      "type": "heritage_site",
      "reference_id": 2,
      "created_at": "2024-11-05T14:20:00Z"
    }
  ],

  // ========== REVIEWS ==========
  "reviews": [
    {
      "id": 1,
      "user_id": 3,
      "type": "heritage_site",
      "heritage_site_id": 1,
      "rating": 5,
      "comment": "Hội An thật tuyệt vời! Di sản văn hóa được bảo tồn rất tốt. Rất đáng ghé thăm!",
      "created_at": "2024-10-20T14:00:00Z"
    },
    {
      "id": 2,
      "user_id": 4,
      "type": "heritage_site",
      "heritage_site_id": 2,
      "rating": 5,
      "comment": "Hoàng Thành Thăng Long mang đậm dấu ấn lịch sử ngàn năm văn hiến!",
      "created_at": "2024-11-06T10:15:00Z"
    }
  ],

  // ========== COLLECTIONS ==========
  "collections": [
    {
      "id": 1,
      "user_id": 3,
      "name": "Bộ sưu tập Di sản Hà Nội",
      "description": "Các di tích lịch sử ở Hà Nội mà tôi đã ghé thăm",
      "artifact_ids": [4],
      "heritage_site_ids": [2, 5, 6],
      "exhibition_ids": [],
      "total_items": 4,
      "is_public": true,
      "created_at": "2024-11-01T10:00:00Z"
    },
    {
      "id": 2,
      "user_id": 1,
      "name": "Cổ vật thời Lý",
      "description": "Bộ sưu tập các cổ vật đặc sắc thời Lý",
      "artifact_ids": [3],
      "heritage_site_ids": [2, 5],
      "exhibition_ids": [],
      "total_items": 3,
      "is_public": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],

  // ========== GAME DATA ==========
  "game_chapters": [
    {
      "id": 1,
      "name": "Lớp Cánh 1: Cội Nguồn",
      "description": "Những câu chuyện khởi nguồn của văn hóa Bắc Bộ.",
      "theme": "Văn hóa Đại Việt",
      "layer_index": 1,
      "order": 1,
      "petal_state": "blooming",
      "required_petals": 0,
      "thumbnail": "https://images.unsplash.com/photo-1555169062-013468b47731?w=400",
      "color": "#D35400",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "Lớp Cánh 2: Giao Thoa",
      "description": "Sự giao thoa văn hóa thế kỷ 18-19.",
      "theme": "Thương cảng quốc tế",
      "layer_index": 2,
      "order": 2,
      "petal_state": "locked",
      "required_petals": 5,
      "thumbnail": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=400",
      "color": "#E67E22",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],

  "game_characters": [
    {
      "id": 1,
      "name": "Chú Tễu",
      "description": "Nhân vật rối nước vui tính, thông minh",
      "persona": "Bạn là Chú Tễu, một nhân vật rối nước vui tính từ múa rối Bắc Bộ.",
      "speaking_style": "Vui vẻ, hài hước, sử dụng từ ngữ dân dã",
      "avatar": "https://ui-avatars.com/api/?name=Teu&background=D35400&color=fff",
      "avatar_locked": "https://ui-avatars.com/api/?name=Teu&background=333&color=888",
      "avatar_unlocked": "https://ui-avatars.com/api/?name=Teu&background=D35400&color=fff",
      "persona_amnesia": "Chú...chú là ai nhỉ? Chú không nhớ rõ lắm...",
      "persona_restored": "Ha ha! Chú nhớ ra rồi! Chú là Chú Tễu, người dẫn chuyện trong múa rối nước!",
      "rarity": "rare",
      "origin": "Múa rối nước",
      "is_collectible": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],

  "game_levels": [
    {
      "id": 1,
      "chapter_id": 1,
      "name": "Dòng thời gian lịch sử",
      "type": "timeline",
      "difficulty": "easy",
      "order": 1,
      "screens": [
        {
          "id": "screen1",
          "type": "DIALOGUE",
          "content": [
            { "speaker": "AI", "text": "Hãy sắp xếp các sự kiện theo đúng thứ tự!" }
          ],
          "next_screen_id": "screen2"
        },
        {
          "id": "screen2",
          "type": "TIMELINE",
          "events": [
            { "id": "evt1", "name": "1802", "content": "Nguyễn Ánh lên ngôi", "year": 1802 },
            { "id": "evt2", "name": "1858", "content": "Pháp tấn công Đà Nẵng", "year": 1858 },
            { "id": "evt3", "name": "1945", "content": "Cách mạng Tháng Tám", "year": 1945 }
          ]
        }
      ],
      "rewards": { "petals": 1, "coins": 50 },
      "passing_score": 70
    }
  ],

  // ========== EXPANDED DATA ==========

  "game_badges": [
    {
      "id": 1,
      "name": "Nhà Thám Hiểm",
      "description": "Ghé thăm 5 di tích lịch sử khác nhau",
      "icon": "🧭",
      "condition": "visit_5_sites",
      "type": "exploration"
    },
    {
      "id": 2,
      "name": "Học Giả Uyên Bác",
      "description": "Hoàn thành Chương 1 đạt điểm tối đa",
      "icon": "📜",
      "condition": "perfect_chapter_1",
      "type": "knowledge"
    },
    {
      "id": 3,
      "name": "Nhà Sưu Tầm",
      "description": "Sở hữu 10 cổ vật trong bộ sưu tập",
      "icon": "🏺",
      "condition": "collect_10_artifacts",
      "type": "collection"
    }
  ],

  "game_achievements": [
    {
      "id": 1,
      "name": "Bước Chân Đầu Tiên",
      "description": "Đăng nhập lần đầu vào SEN",
      "points": 10,
      "target": 1,
      "type": "first_login",
      "icon": "👣"
    },
    {
      "id": 2,
      "name": "Triệu Phú Xu",
      "description": "Tích lũy 1000 xu",
      "points": 50,
      "target": 1000,
      "type": "accumulate_coins",
      "icon": "💰"
    }
  ],

  "scan_objects": [
    {
      "id": 1,
      "code": "HOIAN001",
      "name": "Chùa Cầu Hội An",
      "object_id": 1,
      "object_type": "heritage_site",
      "reward_coins": 200,
      "reward_petals": 2,
      "latitude": 15.8795,
      "longitude": 108.3274
    },
    {
      "id": 2,
      "code": "ARTIFACT001",
      "name": "Bức tranh Hội An",
      "object_id": 1,
      "object_type": "artifact",
      "reward_coins": 150,
      "reward_petals": 1,
      "latitude": 15.8801,
      "longitude": 108.3288
    },
    {
      "id": 3,
      "code": "HANOI001",
      "name": "Hoàng Thành Thăng Long",
      "object_id": 2,
      "object_type": "heritage_site",
      "reward_coins": 180,
      "reward_petals": 2,
      "latitude": 21.0341,
      "longitude": 105.8372
    },
    {
      "id": 4,
      "code": "OCEO001",
      "name": "Khu khảo cổ Óc Eo",
      "object_id": 4,
      "object_type": "heritage_site",
      "reward_coins": 250,
      "reward_petals": 3,
      "latitude": 10.1333,
      "longitude": 104.7667
    }
  ],

  "shop_items": [
    {
      "id": 1,
      "name": "Gợi ý",
      "description": "Hiện đáp án đúng cho 1 câu hỏi",
      "type": "consumable",
      "cost": 100,
      "effect": "reveal_hint",
      "icon": "💡"
    },
    {
      "id": 2,
      "name": "Vé x2 Xu",
      "description": "Nhân đôi xu nhận được trong 1 màn chơi",
      "type": "buff",
      "cost": 200,
      "effect": "double_coins",
      "icon": "🎫"
    },
    {
      "id": 3,
      "name": "Khung Avatar Vàng",
      "description": "Khung avatar sang trọng",
      "type": "cosmetic",
      "cost": 500,
      "effect": "avatar_frame_gold",
      "icon": "🖼️"
    }
  ],

  "game_progress": [
    {
      "id": 1,
      "user_id": 3,
      "level": 5,
      "current_chapter": 1,
      "total_sen_petals": 3,
      "coins": 250,
      "unlocked_chapters": [1],
      "completed_levels": [1],
      "collected_characters": [1],
      "badges": [1],
      "achievements": [1],
      "streak_days": 2,
      "last_login": "2024-05-20T10:00:00Z",
      "museum_open": true,
      "museum_income": 10
    }
  ],

  "game_sessions": [],
  "learning_modules": [],
  "game_quests": [],
  "user_inventory": [],
  "ai_chat_history": [],
  "scan_history": [],
  "notifications": []
};

// ==================== SEEDING FUNCTIONS ====================

function seedJSON() {
  try {
    const dbDir = path.join(__dirname, '../database');
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
    }

    fs.writeFileSync(DB_FILE, JSON.stringify(seedData, null, 2));
    console.log('✅ SEN Database seeded successfully!');
    return true;
  } catch (error) {
    console.error('❌ Error seeding database:', error);
    throw error;
  }
}

async function seedMongoDB() {
  try {
    // 1. Connect to MongoDB
    console.log('🔌 Connecting to MongoDB...');
    await mongoose.connect(process.env.DATABASE_URL);
    console.log('✅ Connected.');

    // 2. Clear & Seed each collection
    for (const [collectionName, items] of Object.entries(seedData)) {
      if (items.length === 0) continue;

      // Access collection directly
      const collection = mongoose.connection.collection(collectionName);

      // Drop if exists (optional, or just deleteMany)
      try {
        // We use deleteMany instead of drop to keep indexes if any
        await collection.deleteMany({});
      } catch (e) { }

      // Transform items to have _id matches id if needed, or just insert
      // MongoDB allows custom _id. To preserve relations (user_id: 1), we MUST use _id: 1
      const itemsWithId = items.map(item => {
        // If item has 'id', use it as '_id' to preserve relations
        if (item.id) {
          return { _id: item.id, ...item };
        }
        return item;
      });

      await collection.insertMany(itemsWithId);
      console.log(`🌱 Seeded ${items.length} items into '${collectionName}'`);
    }

    // 3. Create Indexes (Optional but good)
    // await mongoose.connection.collection('users').createIndex({ email: 1 }, { unique: true });

    return true;

  } catch (error) {
    console.error('❌ MongoDB Seeding Error:', error);
    return false;
  }
}

async function seedSQL() {
  console.log('⚠️ SQL Seeding not implemented yet.');
  return false;
}

async function seedDatabase() {
  try {
    const dbType = process.env.DB_CONNECTION || 'json';

    console.log('\n╔════════════════════════════════════════════════════════╗');
    console.log('║   🌸 SEN Database Seeder - Cultural Heritage Game     ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');
    console.log(`📊 Database Type: ${dbType.toUpperCase()}\n`);

    let success = false;

    switch (dbType.toLowerCase()) {
      case 'json':
        success = seedJSON();
        break;

      case 'mongodb':
        success = await seedMongoDB();
        setTimeout(() => process.exit(0), 1000);
        break;

      case 'mysql':
      case 'postgresql':
        success = await seedSQL();
        setTimeout(() => process.exit(0), 1000);
        break;

      default:
        console.error(`❌ Unknown database type: ${dbType}`);
        process.exit(1);
    }

    if (success) {
      console.log('\n📊 Seeded data summary:');
      console.log(`   - Users: ${seedData.users.length}`);
      console.log(`   - Heritage Sites: ${seedData.heritage_sites.length}`);
      console.log(`   - Artifacts: ${seedData.artifacts.length}`);
      console.log(`   - Game Levels: ${seedData.game_levels.length}`);
      console.log(`   - Shop Items: ${seedData.shop_items.length}`);

      console.log('\n🔑 Test accounts (Password: 123456):');
      console.log(`   Admin:      admin@sen.com`);
      console.log(`   Researcher: tuanpham@sen.com`);
      console.log(`   Customer:   huong.do@sen.com`);

      console.log('\n✨ Seeding completed successfully!\n');
    }

  } catch (error) {
    console.error('\n❌ Fatal error during seeding:', error);
    process.exit(1);
  }
}

// ==================== CLI EXECUTION ====================

if (require.main === module) {
  require('dotenv').config();

  seedDatabase().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

module.exports = { seedDatabase, seedData };