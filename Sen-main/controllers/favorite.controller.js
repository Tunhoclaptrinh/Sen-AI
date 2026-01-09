const BaseController = require('../utils/BaseController');
const favoriteService = require('../services/favorite.service');

class FavoriteController extends BaseController {
  constructor() {
    super(favoriteService);
  }

  getFavorites = async (req, res, next) => {
    try {
      const result = await this.service.getFavorites(req.user.id, req.parsedQuery);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getFavoritesByType = async (req, res, next) => {
    try {
      const { type } = req.params;
      // Inject type into filter
      const options = {
        ...req.parsedQuery,
        filter: { ...req.parsedQuery.filter, type }
      };

      const result = await this.service.getFavorites(req.user.id, options);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  addFavorite = async (req, res, next) => {
    try {
      const { type, id } = req.params;
      const result = await this.service.addFavorite(req.user.id, type, id);

      if (!result.success) {
        return res.status(result.statusCode || 400).json(result);
      }

      res.status(201).json(result);
    } catch (error) {
      next(error);
    }
  };

  removeFavorite = async (req, res, next) => {
    try {
      const { type, id } = req.params;
      const result = await this.service.removeFavorite(req.user.id, type, id);

      if (!result.success) {
        return res.status(result.statusCode || 400).json(result);
      }

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // --- NEW IMPLEMENTATIONS ---

  checkFavorite = async (req, res, next) => {
    try {
      const { type, id } = req.params;
      const result = await this.service.checkFavorite(req.user.id, type, id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  toggleFavorite = async (req, res, next) => {
    try {
      const { type, id } = req.params;
      const result = await this.service.toggleFavorite(req.user.id, type, id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getFavoriteStats = async (req, res, next) => {
    try {
      const result = await this.service.getFavoriteStats(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  clearByType = async (req, res, next) => {
    try {
      const { type } = req.params;
      const result = await this.service.clearFavorites(req.user.id, type);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  clearAll = async (req, res, next) => {
    try {
      const result = await this.service.clearFavorites(req.user.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  // Stubs for currently unimplemented features to prevent crash
  getFavoriteIds = async (req, res, next) => {
    try {
      const { type } = req.params;
      const result = await this.service.getFavorites(req.user.id, { filter: { type } });
      const ids = result.data.map(f => f.reference_id);
      res.json({ success: true, data: ids });
    } catch (error) {
      next(error);
    }
  };

  getTrendingFavorites = async (req, res, next) => {
    res.json({ success: true, data: [] }); // Not yet implemented logic
  };
}

module.exports = new FavoriteController();