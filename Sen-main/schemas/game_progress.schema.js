module.exports = {
  user_id: {
    type: 'number',
    required: true,
    unique: true,
    foreignKey: 'users',
    description: 'User ID'
  },
  current_chapter: {
    type: 'number',
    required: false,
    default: 1,
    description: 'Chapter đang chơi'
  },
  total_sen_petals: {
    type: 'number',
    required: false,
    default: 0,
    description: 'Tổng số cánh hoa sen'
  },
  total_points: {
    type: 'number',
    required: false,
    default: 0,
    description: 'Tổng điểm'
  },
  level: {
    type: 'number',
    required: false,
    default: 1,
    description: 'Level của player'
  },
  coins: {
    type: 'number',
    required: false,
    default: 1000,
    description: 'Tiền game'
  },
  unlocked_chapters: {
    type: 'array',
    required: false,
    description: 'Chapters đã mở'
  },
  completed_levels: {
    type: 'array',
    required: false,
    description: 'Levels đã hoàn thành'
  },
  collected_characters: {
    type: 'array',
    required: false,
    description: 'Characters đã thu thập'
  },
  badges: {
    type: 'array',
    required: false,
    description: 'Badges'
  },
  achievements: {
    type: 'array',
    required: false,
    description: 'Achievements'
  },
  museum_open: {
    type: 'boolean',
    required: false,
    default: false,
    description: 'Bảo tàng có mở không'
  },
  museum_income: {
    type: 'number',
    required: false,
    default: 0,
    description: 'Thu nhập bảo tàng'
  },
  streak_days: {
    type: 'number',
    required: false,
    default: 0,
    description: 'Số ngày chơi liên tiếp'
  },
  last_login: {
    type: 'date',
    required: false,
    description: 'Lần login cuối'
  }
};
