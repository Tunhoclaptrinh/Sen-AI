const BaseController = require('../utils/BaseController');
const timelineService = require('../services/timeline.service');

class TimelineController extends BaseController {
  constructor() {
    super(timelineService);
  }

  getByHeritageSite = async (req, res, next) => {
    try {
      const result = await this.service.findByHeritageSite(req.params.siteId, req.parsedQuery);

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
}
