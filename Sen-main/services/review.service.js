const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class ReviewService extends BaseService {
  constructor() {
    super('reviews');
  }

  async findByType(type, options = {}) {
    if (!['heritage_site', 'artifact'].includes(type)) {
      return {
        success: false,
        message: 'Invalid type',
        statusCode: 400
      };
    }

    const result = await db.findAllAdvanced('reviews', {
      ...options,
      filter: {
        ...options.filter,
        type
      },
      sort: 'created_at',
      order: 'desc'
    });

    return result;
  }

  async getStats() {
    const allReviews = await db.findAll('reviews');

    const totalRating = allReviews.reduce((sum, r) => sum + (r.rating || 0), 0);
    const avgRating = allReviews.length > 0 ? (totalRating / allReviews.length).toFixed(1) : "0.0";

    const stats = {
      total: allReviews.length,
      avgRating: parseFloat(avgRating),
      types: {
        heritage_site: allReviews.filter(r => r.type === 'heritage_site').length,
        artifact: allReviews.filter(r => r.type === 'artifact').length
      },
      ratings: {
        5: allReviews.filter(r => r.rating === 5).length,
        4: allReviews.filter(r => r.rating === 4).length,
        3: allReviews.filter(r => r.rating === 3).length,
        2: allReviews.filter(r => r.rating === 2).length,
        1: allReviews.filter(r => r.rating === 1).length
      }
    };

    return {
      success: true,
      data: stats
    };
  }
}

module.exports = new ReviewService();