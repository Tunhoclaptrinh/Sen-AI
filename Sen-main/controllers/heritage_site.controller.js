const BaseController = require('../utils/BaseController');
const heritageSiteService = require('../services/heritage_site.service');

class HeritageSiteController extends BaseController {
  constructor() {
    super(heritageSiteService);
  }

  getNearby = async (req, res, next) => {
    try {
      const { latitude, longitude, radius = 5 } = req.query;

      if (!latitude || !longitude) {
        return res.status(400).json({
          success: false,
          message: 'Latitude and longitude required'
        });
      }

      const result = await this.service.findNearby(
        parseFloat(latitude),
        parseFloat(longitude),
        parseFloat(radius)
      );

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getArtifacts = async (req, res, next) => {
    try {
      const result = await this.service.getArtifacts(req.params.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getTimeline = async (req, res, next) => {
    try {
      const result = await this.service.getTimeline(req.params.id);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  getStats = async (req, res, next) => {
    try {
      const result = await this.service.getStats();
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new HeritageSiteController();