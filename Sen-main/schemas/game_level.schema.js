// schemas/game_level.schema.js - ENHANCED VERSION
module.exports = {
  chapter_id: {
    type: 'number',
    required: true,
    foreignKey: 'game_chapters',
    description: 'Thuộc chapter nào'
  },
  name: {
    type: 'string',
    required: true,
    minLength: 3,
    maxLength: 150,
    description: 'Tên màn chơi'
  },
  description: {
    type: 'string',
    required: true,
    minLength: 20,
    maxLength: 2000,
    description: 'Mô tả màn chơi'
  },
  type: {
    type: 'enum',
    enum: ['story', 'hidden_object', 'timeline', 'quiz', 'memory', 'puzzle', 'mixed'],
    required: true,
    description: 'Loại gameplay chính (mixed = nhiều loại)'
  },
  difficulty: {
    type: 'enum',
    enum: ['easy', 'medium', 'hard'],
    required: false,
    default: 'medium',
    description: 'Độ khó'
  },
  order: {
    type: 'number',
    required: true,
    min: 1,
    description: 'Thứ tự trong chapter'
  },
  required_level: {
    type: 'number',
    required: false,
    foreignKey: 'game_levels',
    description: 'Level trước cần hoàn thành'
  },

  // === AI CHARACTER CONFIG ===
  ai_character_id: {
    type: 'number',
    required: false,
    foreignKey: 'game_characters',
    description: 'AI character hướng dẫn'
  },
  knowledge_base: {
    type: 'string',
    required: false,
    description: 'Kiến thức cho AI (plain text hoặc markdown)'
  },

  // === SCREENS CONFIGURATION (CORE FEATURE) ===
  screens: {
    type: 'array',
    required: true,
    description: 'Danh sách các màn hình trong level (JSON Array)',
    example: [
      {
        id: 'screen_01',
        type: 'DIALOGUE',
        background_image: 'url',
        background_music: 'url',
        content: [
          { speaker: 'AI', text: 'Chào bạn!', avatar: 'url' }
        ],
        next_screen_id: 'screen_02',
        skip_allowed: true
      },
      {
        id: 'screen_02',
        type: 'HIDDEN_OBJECT',
        background_image: 'url',
        guide_text: 'Tìm 3 vật phẩm...',
        items: [
          {
            id: 'item1',
            name: 'Cái quạt',
            coordinates: { x: 15, y: 45, width: 10, height: 10 },
            fact_popup: 'Đây là cái quạt mo',
            on_collect_effect: 'play_sound_fan',
            points: 10
          }
        ],
        required_items: 3,
        next_screen_id: 'screen_03',
        ai_hints_enabled: true
      },
      {
        id: 'screen_03',
        type: 'QUIZ',
        question: 'Câu hỏi về vật phẩm vừa tìm?',
        options: [
          { text: 'Đáp án A', is_correct: false },
          { text: 'Đáp án B', is_correct: true }
        ],
        time_limit: 60,
        next_screen_id: 'screen_04',
        reward: {
          points: 50,
          coins: 20
        }
      }
    ],
    custom: (value) => {
      if (!Array.isArray(value)) return 'screens must be an array';

      const errors = [];
      const screenIds = new Set();

      value.forEach((screen, idx) => {
        // Check required fields
        if (!screen.id) errors.push(`Screen ${idx}: Missing id`);
        if (!screen.type) errors.push(`Screen ${idx}: Missing type`);

        // Check duplicate IDs
        if (screen.id && screenIds.has(screen.id)) {
          errors.push(`Screen ${idx}: Duplicate id '${screen.id}'`);
        }
        screenIds.add(screen.id);

        // Type-specific validation
        if (screen.type === 'QUIZ' && !screen.options) {
          errors.push(`Screen ${idx}: QUIZ requires options`);
        }
        if (screen.type === 'HIDDEN_OBJECT' && !screen.items) {
          errors.push(`Screen ${idx}: HIDDEN_OBJECT requires items`);
        }
        if (screen.type === 'TIMELINE' && !screen.events) {
          errors.push(`Screen ${idx}: TIMELINE requires events`);
        }
      });

      return errors.length > 0 ? errors.join('; ') : null;
    }
  },

  // === COMPLETION & REWARDS ===
  rewards: {
    type: 'object',
    required: false,
    description: 'Phần thưởng khi hoàn thành (JSON)',
    example: {
      petals: 2,
      coins: 100,
      character: 'teu_full_color',
      badges: ['badge_01']
    }
  },
  time_limit: {
    type: 'number',
    required: false,
    description: 'Giới hạn thời gian toàn bộ level (giây)'
  },
  passing_score: {
    type: 'number',
    required: false,
    default: 70,
    description: 'Điểm tối thiểu để pass'
  },

  // === METADATA ===
  thumbnail: {
    type: 'string',
    required: false,
    description: 'Thumbnail cho level'
  },
  background_image: {
    type: 'string',
    required: false,
    description: 'Background mặc định (nếu screens không có)'
  },
  background_music: {
    type: 'string',
    required: false,
    description: 'Nhạc nền mặc định'
  },
  artifact_ids: {
    type: 'array',
    required: false,
    description: 'Artifacts liên quan'
  },
  heritage_site_id: {
    type: 'number',
    required: false,
    foreignKey: 'heritage_sites',
    description: 'Di sản liên quan'
  },
  is_active: {
    type: 'boolean',
    required: false,
    default: true,
    description: 'Active'
  },
  created_by: {
    type: 'number',
    required: false,
    foreignKey: 'users',
    description: 'Admin/Creator ID'
  }
};