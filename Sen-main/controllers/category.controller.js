const BaseController = require('../utils/BaseController');
const categoryService = require('../services/category.service');

class CategoryController extends BaseController {
  constructor() {
    super(categoryService);
  }

  getItems = async (req, res, next) => {
    try {
      const result = await this.service.getItemsByCategory(req.params.id, req.query);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new CategoryController();