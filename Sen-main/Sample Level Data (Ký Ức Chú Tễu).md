/\*\*

- Sample Level Data - Ký ức chú Tễu
- Theo đúng format từ SystemDesign.docx
  \*/

const sampleLevel = {
level_id: "lvl_bacbo_muaroi_01",
title: "Ký ức chú Tễu",
chapter_id: 2, // Văn hóa Bắc Bộ
order: 1,
type: "mixed", // Có nhiều loại screens
difficulty: "medium",
theme_color: "#D35400",
background_music: "assets/audio/bg_cheo_instrumental.mp3",

// === AI CHARACTER CONFIG ===
ai_config: {
persona_name: "Chú Tễu",
avatar_url: "assets/char/teu_uncolored.png",
system_prompt: "Bạn là Chú Tễu, một nhân vật rối nước vui tính. Bạn đang bị mất trí nhớ và mất màu sơn. Hãy nói giọng hài hước, dân dã, sử dụng từ ngữ cổ. Chỉ trả lời dựa trên thông tin trong 'knowledge_base'.",
knowledge_base: "Múa rối nước ra đời từ thời Lý (thế kỷ 11-12). Chú Tễu là nhân vật kể chuyện, tượng trưng cho nông dân Bắc Bộ. Tễu có thân hình to béo, cởi trần đóng khố...",
intro_message: "Hỡi ôi... Ta là ai? Đây là đâu? Sao người ta nhạt nhòa không chút sắc màu thế này?"
},

// === SCREENS CONFIGURATION ===
screens: [
// Màn hình 1: Hội thoại mở đầu
{
id: "screen_01_intro",
type: "DIALOGUE",
background_image: "assets/bg/thuy_dinh_lang_chua.jpg",
background_music: "assets/audio/ambient_water.mp3",
content: [
{
speaker: "AI",
text: "Chào người anh em! Ta thấy quen quen mà không nhớ ra tên mình. Người có thấy cái gì rơi rớt quanh đây không?",
avatar: "assets/char/teu_uncolored.png",
emotion: "confused"
}
],
next_screen_id: "screen_02_gameplay",
skip_allowed: true,
auto_advance: false
},

    // Màn hình 2: Game tìm đồ vật (Hidden Object)
    {
      id: "screen_02_gameplay",
      type: "HIDDEN_OBJECT",
      background_image: "assets/bg/san_khau_roi_nuoc.jpg",
      background_music: "assets/audio/bg_cheo_instrumental.mp3",
      guide_text: "Tìm 3 vật phẩm giúp Tễu nhớ lại: Cờ hội, Cái quạt, Con trâu.",
      transition_effect: "FADE_OUT", // Hiệu ứng chuyển cảnh
      ,

completion_condition: {
"type": "COLLECT_ALL",
"count": 3
}
items: [
{
id: "item_fan",
name: "Cái quạt mo",
coordinates: { x: 15, y: 45, width: 10, height: 10 },
fact_popup: "Cái quạt của chú Tễu dùng để phe phẩy, dẫn chuyện.",
on_collect_effect: "play_sound_fan_open",
points: 15,
hint: "Hãy tìm ở góc trái màn hình, gần con rối"
},
{
id: "item_flag",
name: "Cờ hội",
coordinates: { x: 80, y: 20, width: 5, height: 15 },
fact_popup: "Cờ hội thường được cắm quanh thủy đình trong dịp lễ.",
on_collect_effect: "play_sound_flag",
points: 15,
hint: "Nhìn lên cao, nơi có gió"
},
{
id: "item_buffalo",
name: "Con trâu",
coordinates: { x: 50, y: 60, width: 15, height: 12 },
fact_popup: "Trâu là biểu tượng của nông nghiệp Việt Nam.",
on_collect_effect: "play_sound_buffalo",
points: 20,
hint: "Ở giữa sân khấu, gần mặt nước"
}
],
required_items: 3,
next_screen_id: "screen_03_quiz",
ai_hints_enabled: true,
hint_cost: 10 // coins
},

    // Màn hình 3: Trắc nghiệm để phục hồi trí nhớ
    {
      id: "screen_03_quiz",
      type: "QUIZ",
      background_image: "assets/bg/san_khau_roi_nuoc.jpg",
      question: "Dựa vào vật phẩm vừa tìm được, đố bạn biết Múa rối nước thường diễn ra ở đâu?",
      options: [
        {
          text: "Trên sân đình",
          is_correct: false,
          explanation: "Không đúng. Múa rối nước biểu diễn trên mặt nước."
        },
        {
          text: "Trên mặt nước (Thủy đình)",
          is_correct: true,
          explanation: "Chính xác! Múa rối nước được biểu diễn trên mặt nước, gọi là thủy đình."
        },
        {
          text: "Trong nhà hát",
          is_correct: false,
          explanation: "Không đúng. Đây là nghệ thuật biểu diễn ngoài trời."
        }
      ],
      time_limit: 60,
      show_hint_after: 30,
      reward: {
        points: 50,
        coins: 30,
        item_unlock: "assets/collection/teu_full_color.png"
      },
      next_screen_id: "screen_04_completion",
      ai_can_explain: true
    },

    // Màn hình 4: Hoàn thành - Chú Tễu được phục hồi
    {
      id: "screen_04_completion",
      type: "DIALOGUE",
      background_image: "assets/bg/san_khau_roi_nuoc.jpg",
      background_music: "assets/audio/victory_theme.mp3",
      content: [
        {
          speaker: "AI",
          text: "Ồ! Ta nhớ ra rồi! Ta là Chú Tễu, người dẫn chuyện trong múa rối nước! Cảm ơn người đã giúp ta tìm lại ký ức!",
          avatar: "assets/char/teu_full_color.png",
          emotion: "happy"
        },
        {
          speaker: "AI",
          text: "Người đã nhận được nhân vật Chú Tễu vào bộ sưu tập! Hãy ghé thăm Bảo tàng để xem nhé!",
          avatar: "assets/char/teu_full_color.png",
          emotion: "excited"
        }
      ],
      skip_allowed: false,
      show_reward_popup: true
    }

],

// === COMPLETION & REWARDS ===
rewards: {
petals: 2,
coins: 100,
character: "teu_full_color",
badges: ["water_puppet_master"]
},

time_limit: 600, // 10 minutes
passing_score: 80,

// === METADATA ===
thumbnail: "assets/thumbs/level_teu.jpg",
artifact_ids: [2], // Bộ đồ gốm Thương Tín
heritage_site_id: 1, // Hội An
is_active: true,
created_at: "2024-01-01T00:00:00Z",
updated_at: "2024-01-01T00:00:00Z"
};

/\*\*

- Example: Màn chơi Timeline (Lịch sử)
  \*/
  const timelineLevel = {
  level_id: "lvl_history_timeline_01",
  title: "Dòng thời gian lịch sử",
  chapter_id: 1, // Lịch sử 18xx-19xx
  type: "timeline",
  difficulty: "easy",

screens: [
{
id: "intro",
type: "DIALOGUE",
content: [
{
speaker: "AI",
text: "Hãy sắp xếp các sự kiện theo đúng thứ tự thời gian!"
}
],
next_screen_id: "timeline_game"
},
{
id: "timeline_game",
type: "TIMELINE",
instructions: "Kéo thả các sự kiện vào đúng vị trí trên dòng thời gian",
events: [
{
id: "evt1",
year: 1802,
title: "Nguyễn Ánh lên ngôi",
description: "Lập triều Nguyễn",
image: "assets/history/nguyen_anh.jpg"
},
{
id: "evt2",
year: 1858,
title: "Pháp tấn công Đà Nẵng",
description: "Bắt đầu xâm lược",
image: "assets/history/danang_1858.jpg"
},
{
id: "evt3",
year: 1945,
title: "Cách mạng Tháng Tám",
description: "Độc lập dân tộc",
image: "assets/history/august_revolution.jpg"
}
],
shuffle_on_start: true,
time_limit: 180,
points_per_correct: 20
}
],

rewards: {
petals: 1,
coins: 50
}
};

/\*\*

- Export examples
  \*/
  module.exports = {
  sampleLevel,
  timelineLevel,

// Template for quick level creation
getEmptyLevelTemplate: () => ({
level*id: `lvl*${Date.now()}`,
title: "New Level",
chapter_id: 1,
type: "mixed",
difficulty: "medium",
screens: [
{
id: "screen_01",
type: "DIALOGUE",
content: [
{ speaker: "AI", text: "Welcome to the level!" }
]
}
],
rewards: {
petals: 1,
coins: 50
}
})
};
