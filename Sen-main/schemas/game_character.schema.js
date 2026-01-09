module.exports = {
  name: {
    type: 'string',
    required: true,
    minLength: 2,
    maxLength: 100,
    description: 'Tên nhân vật'
  },
  description: {
    type: 'string',
    required: false,
    maxLength: 1000,
    description: 'Mô tả nhân vật'
  },
  persona: {
    type: 'string',
    required: true,
    description: 'Tính cách, vai trò của AI'
  },
  speaking_style: {
    type: 'string',
    required: true,
    description: 'Phong cách nói chuyện'
  },
  avatar: {
    type: 'string',
    required: false,
    description: 'Avatar của character'
  },
  avatar_uncolored: {
    type: 'string',
    required: false,
    description: 'Avatar chưa tô màu'
  },
  rarity: {
    type: 'enum',
    enum: ['common', 'rare', 'epic', 'legendary'],
    required: false,
    default: 'common',
    description: 'Độ hiếm'
  },
  origin: {
    type: 'string',
    required: false,
    description: 'Nguồn gốc (VD: Múa rối nước)'
  },
  is_collectible: {
    type: 'boolean',
    required: false,
    default: true,
    description: 'Có thể thu thập'
  },
  // Avatar: 2 trạng thái
  avatar_locked: {
    type: 'string',
    description: 'Ảnh đen trắng/mờ khi chưa mở khóa'
  },
  avatar_unlocked: {
    type: 'string',
    description: 'Ảnh có màu khi đã hoàn thành level'
  },

  // AI Persona: 2 trạng thái tâm lý
  persona_amnesia: {
    type: 'string',
    description: 'Prompt khi nhân vật đang mất trí nhớ (Ngơ ngác, hỏi người chơi là ai)'
  },
  persona_restored: {
    type: 'string',
    description: 'Prompt khi nhân vật đã nhớ lại (Vui vẻ, kể chuyện lịch sử)'
  },

  // Cho tính năng Bảo tàng sống
  museum_interaction: {
    type: 'string',
    description: 'Hành động khi click vào trong bảo tàng (VD: "Hát một đoạn chèo")'
  }
};
