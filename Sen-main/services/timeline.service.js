const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class TimelineService extends BaseService {
  constructor() {
    super('timelines');
  }

  async findByHeritageSite(siteId, options = {}) {
    const result = await db.findAllAdvanced('timelines', {
      ...options,
      filter: {
        ...options.filter,
        heritage_site_id: parseInt(siteId)
      },
      sort: 'year',
      order: 'asc'
    });

    return result;
  }
}

module.exports = new TimelineService();
