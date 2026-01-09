/**
 * AI Controller - Xử lý chat với AI trong game
 * AI đóng vai NPC hướng dẫn người chơi
 */


const aiService = require('../services/ai.service');

class AIController {
  /**
   * POST /api/ai/chat
   * Chat với AI character
   */
  chat = async (req, res, next) => {
    try {
      const { message, context } = req.body;

      if (!message) {
        return res.status(400).json({
          success: false,
          message: 'Message is required'
        });
      }

      const result = await aiService.chat(
        req.user.id,
        message,
        context
      );

      if (!result.success) {
        return res.status(result.statusCode || 500).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  /**
   * GET /api/ai/history
   * Lấy lịch sử chat
   */
  getHistory = async (req, res, next) => {
    try {
      const { levelId, limit = 20 } = req.query;

      const result = await aiService.getHistory(
        req.user.id,
        levelId ? parseInt(levelId) : null,
        parseInt(limit)
      );

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  /**
   * POST /api/ai/ask-hint
   * Xin gợi ý từ AI
   */
  askHint = async (req, res, next) => {
    try {
      const { levelId, clueId } = req.body;

      if (!levelId) {
        return res.status(400).json({
          success: false,
          message: 'Level ID is required'
        });
      }

      const result = await aiService.provideHint(
        req.user.id,
        levelId,
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

  /**
   * POST /api/ai/explain
   * Giải thích về artifact/heritage site
   */
  explain = async (req, res, next) => {
    try {
      const { type, id } = req.body;

      if (!type || !id) {
        return res.status(400).json({
          success: false,
          message: 'Type and ID are required'
        });
      }

      const result = await aiService.explainArtifact(
        req.user.id,
        type,
        id
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

  /**
   * POST /api/ai/quiz
   * Tạo quiz từ AI
   */
  generateQuiz = async (req, res, next) => {
    try {
      const { topicId, difficulty = 'medium' } = req.body;

      if (!topicId) {
        return res.status(400).json({
          success: false,
          message: 'Topic ID is required'
        });
      }

      const result = await aiService.generateQuiz(
        topicId,
        difficulty
      );

      if (!result.success) {
        return res.status(result.statusCode || 500).json({
          success: false,
          message: result.message
        });
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  /**
   * DELETE /api/ai/history
   * Xóa lịch sử chat
   */
  clearHistory = async (req, res, next) => {
    try {
      const result = await aiService.clearHistory(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new AIController();