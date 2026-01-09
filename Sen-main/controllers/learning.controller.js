const BaseController = require('../utils/BaseController');
const learningService = require('../services/learning.service');

class LearningController extends BaseController {
  constructor() {
    super(learningService);
  }

  complete = async (req, res, next) => {
    try {
      const { score } = req.body;
      if (score === undefined) {
        return res.status(400).json({
          success: false,
          message: 'Score is required'
        });
      }

      const result = await this.service.completeModule(req.params.id, req.user.id, score);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getLearningPath = async (req, res, next) => {
    try {
      const result = await this.service.getLearningPath(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new LearningController();
