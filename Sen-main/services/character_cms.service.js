const BaseService = require('../utils/BaseService');

class CharacterCMSService extends BaseService {
  constructor() {
    super('game_characters');
  }
}

module.exports = new CharacterCMSService();