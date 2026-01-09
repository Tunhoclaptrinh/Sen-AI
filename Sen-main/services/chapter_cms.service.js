const BaseService = require('../utils/BaseService');

class ChapterCMSService extends BaseService {
  constructor() {
    super('game_chapters'); // Tên collection trong db.json
  }
}

module.exports = new ChapterCMSService();