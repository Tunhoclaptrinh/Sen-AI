const BaseService = require('../utils/BaseService');

class AssetCMSService extends BaseService {
  constructor() {
    super('scan_objects'); // Quản lý các vật phẩm quét QR
  }
}

module.exports = new AssetCMSService();