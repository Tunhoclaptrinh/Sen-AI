const db = require('../config/database');
const reviewService = require('../services/review.service');

class ReviewController {
  getByType = async (req, res, next) => {
    try {
      const { type } = req.params;
      if (!['heritage_site', 'artifact'].includes(type)) {
        return res.status(400).json({
          success: false,
          message: 'Invalid type'
        });
      }

      const reviews = await db.findMany('reviews', { type: type });
      res.json({
        success: true,
        count: reviews.length,
        data: reviews
      });
    } catch (error) {
      next(error);
    }
  };

  create = async (req, res, next) => {
    try {
      const review = await db.create('reviews', {
        ...req.body,
        user_id: req.user.id,
        createdAt: new Date().toISOString()
      });

      res.status(201).json({
        success: true,
        message: 'Review created',
        data: review
      });
    } catch (error) {
      next(error);
    }
  };

  update = async (req, res, next) => {
    try {
      const review = await db.findById('reviews', req.params.id);
      if (!review) {
        return res.status(404).json({
          success: false,
          message: 'Review not found'
        });
      }

      if (review.user_id !== req.user.id && req.user.role !== 'admin') {
        return res.status(403).json({
          success: false,
          message: 'Not authorized'
        });
      }

      const updated = await db.update('reviews', req.params.id, {
        ...req.body,
        updatedAt: new Date().toISOString()
      });

      res.json({
        success: true,
        message: 'Review updated',
        data: updated
      });
    } catch (error) {
      next(error);
    }
  };

  delete = async (req, res, next) => {
    try {
      const review = await db.findById('reviews', req.params.id);
      if (!review) {
        return res.status(404).json({
          success: false,
          message: 'Review not found'
        });
      }

      if (review.user_id !== req.user.id && req.user.role !== 'admin') {
        return res.status(403).json({
          success: false,
          message: 'Not authorized'
        });
      }

      await db.delete('reviews', req.params.id);
      res.json({
        success: true,
        message: 'Review deleted'
      });
    } catch (error) {
      next(error);
    }
  };

  getAll = async (req, res, next) => {
    try {
      const result = await db.findAllAdvanced('reviews', req.parsedQuery);
      res.json({
        success: true,
        count: result.data.length,
        data: result.data,
        pagination: result.pagination
      });
    } catch (error) {
      next(error);
    }
  };

  getById = async (req, res, next) => {
    try {
      const review = await db.findById('reviews', req.params.id);
      if (!review) {
        return res.status(404).json({
          success: false,
          message: 'Review not found'
        });
      }
      res.json({
        success: true,
        data: review
      });
    } catch (error) {
      next(error);
    }
  };

  search = async (req, res, next) => {
    try {
      const { q } = req.query;
      if (!q) {
        return res.status(400).json({
          success: false,
          message: 'Search query required'
        });
      }

      const result = await db.findAllAdvanced('reviews', {
        q: q,
        ...req.parsedQuery
      });

      res.json({
        success: true,
        count: result.data.length,
        data: result.data,
        pagination: result.pagination
      });
    } catch (error) {
      next(error);
    }
  };

  getStats = async (req, res, next) => {
    try {
      const result = await reviewService.getStats();
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new ReviewController();