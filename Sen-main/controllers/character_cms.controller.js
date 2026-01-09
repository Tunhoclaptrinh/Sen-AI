const BaseController = require('../utils/BaseController');
const characterCMSService = require('../services/character_cms.service');

class CharacterCMSController extends BaseController {
  constructor() {
    super(characterCMSService);
  }
}

module.exports = new CharacterCMSController();