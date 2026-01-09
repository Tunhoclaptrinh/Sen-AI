/**
 * Game Controller - Xử lý game logic cho SEN
 * Sử dụng unified game.service.js
 */

const gameService = require('../services/game.service');

class GameController {

  // ==================== PROGRESS ====================

  getProgress = async (req, res, next) => {
    try {
      const result = await gameService.getProgress(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // ==================== CHAPTERS ====================

  getChapters = async (req, res, next) => {
    try {
      const result = await gameService.getChapters(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getChapterDetail = async (req, res, next) => {
    try {
      const result = await gameService.getChapterDetail(
        req.params.id,
        req.user.id
      );

      if (!result.success) {
        return res.status(result.statusCode || 404).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  unlockChapter = async (req, res, next) => {
    try {
      const result = await gameService.unlockChapter(
        req.params.id,
        req.user.id
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // ==================== LEVELS ====================

  getLevels = async (req, res, next) => {
    try {
      const result = await gameService.getLevels(
        req.params.chapterId,
        req.user.id
      );
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getLevelDetail = async (req, res, next) => {
    try {
      const result = await gameService.getLevelDetail(
        req.params.id,
        req.user.id
      );

      if (!result.success) {
        return res.status(result.statusCode || 404).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  startLevel = async (req, res, next) => {
    try {
      const result = await gameService.startLevel(
        req.params.id,
        req.user.id
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  collectClue = async (req, res, next) => {
    try {
      const { clueId } = req.body;

      if (!clueId) {
        return res.status(400).json({
          success: false,
          message: 'Clue ID is required'
        });
      }

      const result = await gameService.collectClue(
        req.params.id,
        req.user.id,
        clueId
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  completeLevel = async (req, res, next) => {
    try {
      const { score, timeSpent } = req.body;

      const result = await gameService.completeLevel(
        req.params.id,
        req.user.id,
        { score, timeSpent }
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // ==================== SCREEN NAVIGATION (NEW) ====================

  /**
   * POST /api/game/sessions/:id/next-screen
   * Navigate to next screen in level
   */
  navigateToNextScreen = async (req, res, next) => {
    try {
      const result = await gameService.navigateToNextScreen(
        req.params.id,
        req.user.id
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message,
          data: result.data
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  /**
   * POST /api/game/sessions/:id/submit-answer
   * Submit answer for QUIZ screen
   */
  submitAnswer = async (req, res, next) => {
    try {
      const { answerId } = req.body;

      if (!answerId) {
        return res.status(400).json({
          success: false,
          message: 'Answer ID is required'
        });
      }

      const result = await gameService.submitAnswer(
        req.params.id,
        req.user.id,
        answerId
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  async submitTimelineOrder(req, res, next) {
    try {
      const { sessionId } = req.params;
      const { eventOrder } = req.body;

      // VALIDATION
      if (!eventOrder || !Array.isArray(eventOrder) || eventOrder.length === 0) {
        return res.status(400).json({
          success: false,
          message: 'eventOrder must be a non-empty array'
        });
      }

      const result = await gameService.submitTimelineOrder(
        sessionId,
        req.user.id,
        eventOrder
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json(result);
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  }

  // ==================== MUSEUM ====================

  getMuseum = async (req, res, next) => {
    try {
      const result = await gameService.getMuseum(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  toggleMuseum = async (req, res, next) => {
    try {
      const { isOpen } = req.body;

      const result = await gameService.toggleMuseum(
        req.user.id,
        isOpen
      );

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // Collect Income Endpoint
  collectMuseumIncome = async (req, res, next) => {
    try {
      const result = await gameService.collectMuseumIncome(req.user.id);

      if (!result.success) {
        return res.status(result.statusCode || 400).json(result);
      }
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // ==================== BADGES & ACHIEVEMENTS ====================

  getBadges = async (req, res, next) => {
    try {
      const result = await gameService.getBadges(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getAchievements = async (req, res, next) => {
    try {
      const result = await gameService.getAchievements(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // ==================== SCAN ====================

  scanObject = async (req, res, next) => {
    try {
      const { code, latitude, longitude } = req.body;

      if (!code) {
        return res.status(400).json({
          success: false,
          message: 'Scan code is required'
        });
      }

      const result = await gameService.scanObject(
        req.user.id,
        code,
        { latitude, longitude }
      );

      if (!result.success) {
        return res.status(result.statusCode || 404).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // ==================== LEADERBOARD ====================

  getLeaderboard = async (req, res, next) => {
    try {
      const { type = 'global', limit = 20 } = req.query;

      const result = await gameService.getLeaderboard(
        type,
        parseInt(limit)
      );

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getDailyReward = async (req, res, next) => {
    try {
      const result = await gameService.getDailyReward(req.user.id);

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // ==================== SHOP & INVENTORY ====================

  purchaseItem = async (req, res, next) => {
    try {
      const { itemId, quantity = 1 } = req.body;

      if (!itemId) {
        return res.status(400).json({
          success: false,
          message: 'Item ID is required'
        });
      }

      const result = await gameService.purchaseItem(
        req.user.id,
        itemId,
        quantity
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getInventory = async (req, res, next) => {
    try {
      const result = await gameService.getInventory(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  useItem = async (req, res, next) => {
    try {
      const { itemId, targetId } = req.body;

      if (!itemId) {
        return res.status(400).json({
          success: false,
          message: 'Item ID is required'
        });
      }

      const result = await gameService.useItem(
        req.user.id,
        itemId,
        targetId
      );

      if (!result.success) {
        return res.status(result.statusCode || 400).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new GameController();