const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class CollectionService extends BaseService {
    constructor() {
        super('collections');
    }
}

module.exports = new CollectionService();
