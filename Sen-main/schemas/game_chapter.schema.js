module.exports = {
  name: {
    type: 'string',
    required: true,
    minLength: 3,
    maxLength: 150,
    description: 'Tên chapter (lớp cánh hoa sen)'
  },
  description: {
    type: 'string',
    required: true,
    minLength: 20,
    maxLength: 1000,
    description: 'Mô tả chapter'
  },
  theme: {
    type: 'string',
    required: true,
    description: 'Chủ đề (VD: 18xx-19xx, Văn hóa Bắc Bộ)'
  },
  order: {
    type: 'number',
    required: true,
    min: 1,
    description: 'Thứ tự chapter'
  },
  required_petals: {
    type: 'number',
    required: false,
    default: 0,
    description: 'Số cánh hoa sen cần để mở'
  },
  thumbnail: {
    type: 'string',
    required: false,
    description: 'Hình ảnh thumbnail'
  },
  color: {
    type: 'string',
    required: false,
    default: '#D35400',
    description: 'Màu sắc đại diện'
  },
  is_active: {
    type: 'boolean',
    required: false,
    default: true,
    description: 'Có active không'
  },
  layer_index: {
    type: 'number',
    required: true,
    description: 'Vị trí lớp cánh hoa (1: Trong cùng, 2: Giữa, 3: Ngoài)'
  },
  petal_image_closed: {
    type: 'string',
    description: 'Ảnh cánh sen khi chưa nở (nụ)'
  },
  petal_image_bloom: {
    type: 'string',
    description: 'Ảnh cánh sen khi đã nở rộ'
  },
};
