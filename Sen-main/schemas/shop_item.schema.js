module.exports = {
  name: {
    type: 'string',
    required: true,
    description: 'Tên item'
  },
  description: {
    type: 'string',
    required: false,
    description: 'Mô tả'
  },
  type: {
    type: 'enum',
    enum: ['hint', 'boost', 'decoration', 'character_skin'],
    required: true,
    description: 'Loại item'
  },
  price: {
    type: 'number',
    required: true,
    min: 0,
    description: 'Giá (coins)'
  },
  icon: {
    type: 'string',
    required: false,
    description: 'Icon item'
  },
  effect: {
    type: 'string',
    required: false,
    description: 'Hiệu ứng khi dùng'
  },
  is_consumable: {
    type: 'boolean',
    required: false,
    default: true,
    description: 'Có tiêu hao không'
  },
  max_stack: {
    type: 'number',
    required: false,
    default: 99,
    description: 'Số lượng tối đa trong inventory'
  },
  is_available: {
    type: 'boolean',
    required: false,
    default: true,
    description: 'Có bán không'
  }
};