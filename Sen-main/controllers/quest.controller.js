const BaseController = require('../utils/BaseController');
const questService = require('../services/quest.service');

class QuestController extends BaseController {
  constructor() {
    super(questService);
  }

  getAvailable = async (req, res, next) => {
    try {
      const result = await this.service.getAvailableQuests(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  complete = async (req, res, next) => {
    try {
      const { score } = req.body;
      if (score === undefined) {
        return res.status(400).json({
          success: false,
          message: 'Score is required'
        });
      }

      const result = await this.service.completeQuest(req.params.id, req.user.id, score);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getLeaderboard = async (req, res, next) => {
    try {
      const result = await this.service.getLeaderboard(10);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new QuestController();