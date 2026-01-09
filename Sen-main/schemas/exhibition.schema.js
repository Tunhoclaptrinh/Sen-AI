module.exports = {
  name: {
    type: 'string',
    required: true,
    minLength: 5,
    maxLength: 200,
    description: 'Tên triển lãm'
  },
  description: {
    type: 'string',
    required: true,
    minLength: 20,
    maxLength: 2000,
    description: 'Mô tả triển lãm'
  },
  heritage_site_id: {
    type: 'number',
    required: true,
    foreignKey: 'heritage_sites',
    description: 'Địa điểm tổ chức'
  },
  theme: {
    type: 'string',
    required: true,
    maxLength: 200,
    description: 'Chủ đề'
  },
  start_date: {
    type: 'date',
    required: true,
    description: 'Ngày khai mạc'
  },
  end_date: {
    type: 'date',
    required: true,
    description: 'Ngày đóng'
  },
  curator: {
    type: 'string',
    required: false,
    maxLength: 200,
    description: 'Người quản lý'
  },
  image: {
    type: 'string',
    required: false,
    description: 'Poster'
  },
  is_active: {
    type: 'boolean',
    required: false,
    default: true,
    description: 'Đang diễn ra'
  }
};