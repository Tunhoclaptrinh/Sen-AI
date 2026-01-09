module.exports = {
  name: {
    type: 'string',
    required: true,
    minLength: 3,
    maxLength: 150,
    description: 'Tên tư liệu/cổ vật'
  },
  description: {
    type: 'string',
    required: true,
    minLength: 20,
    maxLength: 3000,
    description: 'Mô tả chi tiết'
  },
  heritage_site_id: {
    type: 'number',
    required: true,
    foreignKey: 'heritage_sites',
    description: 'Thuộc di sản nào'
  },
  category_id: {
    type: 'number',
    required: true,
    foreignKey: 'cultural_categories',
    description: 'Phân loại'
  },
  artifact_type: {
    type: 'enum',
    enum: ['sculpture', 'painting', 'document', 'pottery', 'textile', 'tool', 'weapon', 'jewelry', 'manuscript', 'photograph', 'other'],
    required: true,
    description: 'Loại cổ vật'
  },
  year_created: {
    type: 'number',
    required: false,
    description: 'Năm tạo tác'
  },
  year_discovered: {
    type: 'number',
    required: false,
    description: 'Năm phát hiện'
  },
  creator: {
    type: 'string',
    required: false,
    maxLength: 200,
    description: 'Tác giả'
  },
  material: {
    type: 'string',
    required: false,
    maxLength: 200,
    description: 'Chất liệu'
  },
  dimensions: {
    type: 'string',
    required: false,
    maxLength: 100,
    description: 'Kích thước'
  },
  weight: {
    type: 'number',
    required: false,
    description: 'Trọng lượng (kg)'
  },
  condition: {
    type: 'enum',
    enum: ['excellent', 'good', 'fair', 'poor'],
    required: false,
    default: 'fair',
    description: 'Tình trạng'
  },
  image: {
    type: 'string',
    required: false,
    description: 'Hình ảnh'
  },
  is_on_display: {
    type: 'boolean',
    required: false,
    default: true,
    description: 'Đang trưng bày'
  }
};
