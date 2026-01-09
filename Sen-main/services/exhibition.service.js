const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class ExhibitionService extends BaseService {
  constructor() {
    super('exhibitions');
  }

  async getActiveExhibitions(options = {}) {
    const now = new Date();
    const allExhibitions = await db.findAll('exhibitions');

    const activeExhibitions = allExhibitions.filter(ex => {
      const start = new Date(ex.start_date);
      const end = new Date(ex.end_date);
      return start <= now && now <= end && ex.is_active;
    });

    const pagination = this.applyPagination(activeExhibitions, options.page, options.limit);

    return {
      success: true,
      data: pagination.data,
      pagination: pagination
    };
  }
}

module.exports = new ExhibitionService();