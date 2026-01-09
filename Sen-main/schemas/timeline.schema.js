module.exports = {
  title: {
    type: 'string',
    required: true,
    minLength: 5,
    maxLength: 200,
    description: 'Tiêu đề sự kiện'
  },
  description: {
    type: 'string',
    required: true,
    minLength: 20,
    maxLength: 2000,
    description: 'Mô tả'
  },
  year: {
    type: 'number',
    required: true,
    description: 'Năm'
  },
  heritage_site_id: {
    type: 'number',
    required: true,
    foreignKey: 'heritage_sites',
    description: 'Di sản liên quan'
  },
  image: {
    type: 'string',
    required: false,
    description: 'Hình ảnh'
  },
  category: {
    type: 'enum',
    enum: ['founded', 'damaged', 'restored', 'discovery', 'event', 'recognition'],
    required: false,
    description: 'Loại sự kiện'
  }
};
