const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class FavoriteService extends BaseService {
  constructor() {
    super('favorites');
  }

  async getFavorites(userId, options = {}) {
    const result = await db.findAllAdvanced('favorites', {
      ...options,
      filter: {
        ...options.filter,
        user_id: userId
      }
    });

    const enriched = (await Promise.all(result.data.map(async (fav) => {
      let item = null;
      if (fav.type === 'heritage_site') {
        item = await db.findById('heritage_sites', fav.reference_id);
      } else if (fav.type === 'artifact') {
        item = await db.findById('artifacts', fav.reference_id);
      } else if (fav.type === 'exhibition') {
        item = await db.findById('exhibitions', fav.reference_id);
      }

      return {
        ...fav,
        item: item || null
      };
    }))).filter(f => f.item !== null);

    return {
      success: true,
      data: enriched,
      count: enriched.length
    };
  }

  async addFavorite(userId, type, referenceId) {
    if (!['heritage_site', 'artifact', 'exhibition'].includes(type)) {
      return {
        success: false,
        message: 'Invalid type',
        statusCode: 400
      };
    }

    const existing = await db.findOne('favorites', {
      user_id: userId,
      type,
      reference_id: parseInt(referenceId)
    });

    if (existing) {
      return {
        success: false,
        message: 'Already favorited',
        statusCode: 400
      };
    }

    const favorite = await db.create('favorites', {
      user_id: userId,
      type,
      reference_id: parseInt(referenceId),
      created_at: new Date().toISOString()
    });

    return {
      success: true,
      message: 'Added to favorites',
      data: favorite
    };
  }

  async removeFavorite(userId, type, referenceId) {
    const favorite = await db.findOne('favorites', {
      user_id: userId,
      type,
      reference_id: parseInt(referenceId)
    });

    if (!favorite) {
      return {
        success: false,
        message: 'Favorite not found',
        statusCode: 404
      };
    }

    await db.delete('favorites', favorite.id);

    return {
      success: true,
      message: 'Removed from favorites'
    };
  }

  // --- NEW METHODS ---

  async checkFavorite(userId, type, referenceId) {
    const favorite = await db.findOne('favorites', {
      user_id: userId,
      type,
      reference_id: parseInt(referenceId)
    });

    return {
      success: true,
      data: {
        isFavorited: !!favorite,
        favoriteId: favorite ? favorite.id : null
      }
    };
  }

  async toggleFavorite(userId, type, referenceId) {
    const check = await this.checkFavorite(userId, type, referenceId);

    if (check.data.isFavorited) {
      await this.removeFavorite(userId, type, referenceId);
      return {
        success: true,
        message: 'Removed from favorites',
        data: { isFavorited: false }
      };
    } else {
      await this.addFavorite(userId, type, referenceId);
      return {
        success: true,
        message: 'Added to favorites',
        data: { isFavorited: true }
      };
    }
  }

  async clearFavorites(userId, type = null) {
    const query = { user_id: userId };
    if (type) query.type = type;

    const favorites = await db.findMany('favorites', query);

    let count = 0;
    for (const fav of favorites) {
      await db.delete('favorites', fav.id);
      count++;
    }

    return {
      success: true,
      message: `Cleared ${count} favorites`,
      data: { count }
    };
  }

  async getFavoriteStats(userId) {
    const favorites = await db.findMany('favorites', { user_id: userId });

    const stats = {
      total: favorites.length,
      byType: {
        heritage_site: favorites.filter(f => f.type === 'heritage_site').length,
        artifact: favorites.filter(f => f.type === 'artifact').length,
        exhibition: favorites.filter(f => f.type === 'exhibition').length
      }
    };

    return {
      success: true,
      data: stats
    };
  }
}

module.exports = new FavoriteService();