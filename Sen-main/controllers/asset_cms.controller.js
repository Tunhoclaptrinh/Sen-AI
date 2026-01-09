const BaseController = require('../utils/BaseController');
const assetCMSService = require('../services/asset_cms.service');

class AssetCMSController extends BaseController {
  constructor() {
    super(assetCMSService);
  }
}

module.exports = new AssetCMSController();