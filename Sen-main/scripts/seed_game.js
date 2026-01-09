
const fs = require('fs');
const path = require('path');

const dbPath = path.join(__dirname, '../database/db.json');

// --- NEW DATA ---

const newChapters = [
    {
        "id": 1,
        "name": "Sen Hồng - Cội Nguồn",
        "description": "Những câu chuyện khởi nguồn của văn hóa Bắc Bộ.",
        "layer_index": 1,
        "petal_state": "blooming",
        "required_petals": 0,
        "is_active": true
    },
    {
        "id": 2,
        "name": "Sen Vàng - Giao Thoa",
        "description": "Sự giao thoa văn hóa thế kỷ 18-19.",
        "layer_index": 2,
        "petal_state": "locked",
        "required_petals": 5,
        "is_active": true
    },
    {
        "id": 3,
        "name": "Sen Trắng - Di Sản",
        "description": "Thời kỳ phồn vinh của các triều đại phong kiến.",
        "layer_index": 3,
        "petal_state": "locked",
        "required_petals": 10,
        "is_active": true
    }
];

const newCharacters = [
    {
        "id": 1,
        "name": "Chú Tễu",
        "description": "Nhân vật rối nước vui tính, thông minh",
        "persona": "Bạn là Chú Tễu. Ở trạng thái mất trí nhớ, bạn ngơ ngác và hay hỏi lại. Khi hồi phục, bạn vui vẻ, hay cười 'hi hi' và kể chuyện tiếu lâm.",
        "speaking_style": "Vui vẻ, dân dã, dùng từ địa phương Bắc Bộ",
        "avatar": "https://api.dicebear.com/7.x/fun-emoji/svg?seed=Teu",
        "avatar_uncolored": "https://api.dicebear.com/7.x/fun-emoji/svg?seed=Teu&backgroundColor=b6b6b6",
        "rarity": "rare",
        "origin": "Múa rối nước",
        "is_collectible": true,
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": 2,
        "name": "Thị Kính",
        "description": "Quan Âm Thị Kính - Biểu tượng của sự nhẫn nhịn",
        "persona": "Bạn là Thị Kính. Bạn nhẹ nhàng, từ tốn và luôn khuyên răn người khác làm việc thiện.",
        "speaking_style": "Nhẹ nhàng, từ bi, bác học",
        "avatar": "https://api.dicebear.com/7.x/adventurer/svg?seed=Kinh",
        "rarity": "epic",
        "origin": "Truyền thuyết dân gian",
        "is_collectible": true,
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": 3,
        "name": "Thánh Gióng",
        "description": "Vị thánh chống giặc ngoại xâm",
        "persona": "Bạn là Thánh Gióng. Bạn ít nói, hành động dứt khoát, giọng nói vang rền như sấm.",
        "speaking_style": "Mạnh mẽ, ngắn gọn, uy lực",
        "avatar": "https://api.dicebear.com/7.x/adventurer/svg?seed=Giong",
        "rarity": "legendary",
        "origin": "Truyền thuyết Thánh Gióng",
        "is_collectible": true,
        "created_at": "2024-01-01T00:00:00Z"
    }
];

const newLevels = [
    {
        "id": 1,
        "chapter_id": 1,
        "name": "Màn 1: Khởi Đầu",
        "description": "Gặp gỡ Chú Tễu và bắt đầu hành trình tìm lại ký ức.",
        "type": "story",
        "difficulty": "easy",
        "order": 1,
        "required_level": null,
        "background_image": "https://images.unsplash.com/photo-1555169062-013468b47731?w=800",
        "screens": [
            {
                "id": "screen1",
                "type": "DIALOGUE",
                "background_image": "https://images.unsplash.com/photo-1555169062-013468b47731?w=800",
                "content": [
                    {
                        "speaker": "AI",
                        "text": "Oa... Đây là đâu? Ta là ai?",
                        "avatar": "https://api.dicebear.com/7.x/fun-emoji/svg?seed=Teu&backgroundColor=b6b6b6",
                        "emotion": "confused"
                    },
                    {
                        "speaker": "USER",
                        "text": "Bạn là Chú Tễu, ngôi sao sáng của sân khấu múa rối nước mà! Bạn không nhớ sao?"
                    },
                    {
                        "speaker": "AI",
                        "text": "Chú Tễu? Cái tên nghe quen quá... Nhưng đầu óc ta trống rỗng. Bạn giúp ta tìm lại ký ức nhé?",
                        "avatar": "https://api.dicebear.com/7.x/fun-emoji/svg?seed=Teu&backgroundColor=b6b6b6",
                        "emotion": "sad"
                    }
                ]
            },
            {
                "id": "screen2",
                "type": "QUIZ",
                "background_image": "https://images.unsplash.com/photo-1555169062-013468b47731?w=800",
                "question": "Chú Tễu thường xuất hiện trong loại hình nghệ thuật nào?",
                "options": [
                    { "text": "Hát Quan Họ", "is_correct": false },
                    { "text": "Múa Rối Nước", "is_correct": true },
                    { "text": "Cải Lương", "is_correct": false }
                ],
                "points": 100
            }
        ],
        "rewards": {
            "coins": 50,
            "petals": 1
        }
    },
    {
        "id": 2,
        "chapter_id": 1,
        "name": "Màn 2: Ký Ức Rối Nước",
        "description": "Giúp Chú Tễu tìm lại sân khấu của mình.",
        "type": "mixed",
        "difficulty": "medium",
        "order": 2,
        "required_level": 1,
        "background_image": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800",
        "screens": [
            {
                "id": "screen1",
                "type": "DIALOGUE",
                "content": [
                    {
                        "speaker": "AI",
                        "text": "Ta nhớ mang máng... ta sống ở một nơi có rất nhiều nước, và âm nhạc rộn ràng!",
                        "avatar": "https://api.dicebear.com/7.x/fun-emoji/svg?seed=Teu&backgroundColor=b6b6b6"
                    }
                ]
            },
            {
                "id": "screen2",
                "type": "HIDDEN_OBJECT",
                "background_image": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800",
                "items": [
                    { "id": "fan", "name": "Cái Quạt", "x": 20, "y": 60, "fact_popup": "Đây là chiếc quạt mo của Chú Tễu!" },
                    { "id": "flag", "name": "Cờ Hội", "x": 70, "y": 30, "fact_popup": "Cờ hội báo hiệu buổi diễn bắt đầu." }
                ],
                "required_items": 2
            },
            {
                "id": "screen3",
                "type": "QUIZ",
                "question": "Sân khấu của múa rối nước gọi là gì?",
                "options": [
                    { "text": "Thủy Đình", "is_correct": true },
                    { "text": "Đình Làng", "is_correct": false }
                ],
                "points": 150
            }
        ],
        "rewards": {
            "coins": 100,
            "petals": 2,
            "character": "teu_full_color"
        }
    },
    {
        "id": 3,
        "chapter_id": 1,
        "name": "Màn 3: Dòng Chảy Lịch Sử",
        "description": "Sắp xếp lại dòng thời gian lịch sử Việt Nam.",
        "type": "story",
        "difficulty": "hard",
        "order": 3,
        "required_level": 2,
        "background_image": "https://images.unsplash.com/photo-1528127269322-539801943592?w=800",
        "screens": [
            {
                "id": "screen1",
                "type": "TIMELINE",
                "events": [
                    { "id": "e1", "year": 1010, "title": "Dời đô về Thăng Long", "description": "Vua Lý Thái Tổ dời đô." },
                    { "id": "e2", "year": 1428, "title": "Khởi nghĩa Lam Sơn", "description": "Lê Lợi chiến thắng quân Minh." },
                    { "id": "e3", "year": 1945, "title": "Cách mạng Tháng Tám", "description": "Việt Nam giành độc lập." }
                ],
                "correct_order": ["e1", "e2", "e3"]
            },
            {
                "id": "screen2",
                "type": "IMAGE_VIEWER",
                "image": "https://images.unsplash.com/photo-1528127269322-539801943592?w=800",
                "caption": "Khuê Văn Các",
                "description": "Biểu tượng của thủ đô Hà Nội, nằm trong Văn Miếu - Quốc Tử Giám."
            }
        ],
        "rewards": {
            "coins": 200,
            "petals": 3
        }
    }
];

// --- MAIN LOGIC ---

try {
    console.log('Reading database...');
    const data = JSON.parse(fs.readFileSync(dbPath, 'utf8'));

    console.log('Updating Game Data...');
    data.game_chapters = newChapters;
    data.game_characters = newCharacters;
    data.game_levels = newLevels;

    console.log('Writing database...');
    fs.writeFileSync(dbPath, JSON.stringify(data, null, 2), 'utf8');

    console.log('✅ Success! Game data populated.');
} catch (error) {
    console.error('❌ Error seeding data:', error);
}
