module.exports = {
  name: {
    type: 'string',
    required: true,
    unique: true,
    minLength: 5,
    maxLength: 200,
    description: 'Tên di sản văn hóa'
  },
  description: {
    type: 'string',
    required: true,
    minLength: 10,
    maxLength: 5000,
    description: 'Mô tả chi tiết về di sản'
  },
  type: {
    type: 'enum',
    enum: ['monument', 'temple', 'museum', 'archaeological_site', 'historic_building', 'natural_heritage', 'intangible_heritage'],
    required: false,
    default: 'monument',
    description: 'Loại di sản'
  },
  cultural_period: {
    type: 'string',
    required: false,
    description: 'Thời kỳ văn hóa (VD: Triều Nguyễn, Thời Lý, ...)'
  },
  region: {
    type: 'string',
    required: false,
    description: 'Vùng miền (Bắc, Trung, Nam)'
  },
  latitude: {
    type: 'number',
    required: false,
    min: -90,
    max: 90,
    description: 'GPS latitude'
  },
  longitude: {
    type: 'number',
    required: false,
    min: -180,
    max: 180,
    description: 'GPS longitude'
  },
  address: {
    type: 'string',
    required: true,
    minLength: 10,
    maxLength: 300,
    description: 'Địa chỉ cụ thể'
  },
  year_established: {
    type: 'number',
    required: false,
    description: 'Năm thành lập/xây dựng'
  },
  year_restored: {
    type: 'number',
    required: false,
    description: 'Năm tu bổ gần nhất'
  },
  image: {
    type: 'string',
    required: false,
    description: 'URL hình ảnh chính'
  },
  gallery: {
    type: 'array',
    required: false,
    description: 'Bộ sưu tập hình ảnh'
  },
  rating: {
    type: 'number',
    required: false,
    min: 0,
    max: 5,
    default: 0,
    description: 'Đánh giá trung bình'
  },
  total_reviews: {
    type: 'number',
    required: false,
    default: 0,
    description: 'Tổng số đánh giá'
  },
  visit_hours: {
    type: 'string',
    required: false,
    description: 'Giờ mở cửa (VD: 8:00 - 17:00)'
  },
  entrance_fee: {
    type: 'number',
    required: false,
    default: 0,
    description: 'Phí vào cửa (VNĐ)'
  },
  is_active: {
    type: 'boolean',
    required: false,
    default: true,
    description: 'Đang hoạt động'
  },
  unesco_listed: {
    type: 'boolean',
    required: false,
    default: false,
    description: 'Được UNESCO công nhận'
  },
  significance: {
    type: 'enum',
    enum: ['local', 'national', 'international'],
    required: false,
    default: 'local',
    description: 'Tầm quan trọng'
  },
  historical_events: {
    type: 'array',
    required: false,
    description: 'Các sự kiện lịch sử liên quan'
  },
  legends: {
    type: 'array',
    required: false,
    description: 'Các câu chuyện dã sử, truyền thuyết'
  },
  visit_count: {
    type: 'number',
    required: false,
    default: 0,
    description: 'Số lượt khám phá (gamification)'
  }
};