const BaseController = require('../utils/BaseController');
const chapterCMSService = require('../services/chapter_cms.service');

class ChapterCMSController extends BaseController {
  constructor() {
    super(chapterCMSService);
  }
}

module.exports = new ChapterCMSController();