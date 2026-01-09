
// ===== schemas/collection.schema.js =====
module.exports = {
  name: {
    type: 'string',
    required: true,
    minLength: 3,
    maxLength: 150,
    description: 'Tên bộ sưu tập'
  },
  description: {
    type: 'string',
    required: false,
    maxLength: 1000,
    description: 'Mô tả bộ sưu tập'
  },
  user_id: {
    type: 'number',
    required: true,
    foreignKey: 'users',
    description: 'Người tạo bộ sưu tập'
  },
  artifact_ids: {
    type: 'array',
    required: false,
    description: 'Danh sách cổ vật trong bộ sưu tập'
  },
  is_public: {
    type: 'boolean',
    required: false,
    default: false,
    description: 'Công khai bộ sưu tập'
  }
};