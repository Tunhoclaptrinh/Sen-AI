const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class CategoryService extends BaseService {
  constructor() {
    super('cultural_categories');
  }

  async validateDelete(id) {
    const artifacts = await db.findMany('artifacts', { category_id: parseInt(id) });

    if (artifacts.length > 0) {
      return {
        success: false,
        message: 'Cannot delete category in use',
        statusCode: 400,
        details: {
          artifacts_count: artifacts.length
        }
      };
    }

    return { success: true };
  }

  /**
   * Lấy tất cả vật phẩm/di sản thuộc category này
   */
  async getItemsByCategory(categoryId, queryOptions = {}) {
    // Hiện tại chủ yếu là artifacts có category_id
    // Có thể mở rộng thêm cho heritage_sites nếu sau này bổ sung schema

    const options = {
      ...queryOptions,
      filter: {
        ...(queryOptions.filter || {}),
        category_id: parseInt(categoryId)
      }
    };

    const result = await db.findAllAdvanced('artifacts', options);

    return {
      success: true,
      count: result.data.length,
      data: result.data,
      pagination: result.pagination
    };
  }
}

module.exports = new CategoryService();