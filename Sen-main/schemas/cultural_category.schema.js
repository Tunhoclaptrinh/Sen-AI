module.exports = {
  name: {
    type: 'string',
    required: true,
    unique: true,
    minLength: 3,
    maxLength: 100,
    description: 'Tên thể loại'
  },
  icon: {
    type: 'string',
    required: false,
    default: '🏛️',
    description: 'Icon emoji'
  },
  image: {
    type: 'string',
    required: false,
    description: 'Hình ảnh'
  },
  description: {
    type: 'string',
    required: false,
    maxLength: 500,
    description: 'Mô tả'
  }
};