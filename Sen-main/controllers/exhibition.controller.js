const db = require('../config/database');

class ExhibitionController {
  getAll = async (req, res, next) => {
    try {
      const result = await db.findAllAdvanced('exhibitions', req.parsedQuery);
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
      const exhibition = await db.findById('exhibitions', req.params.id);
      if (!exhibition) {
        return res.status(404).json({
          success: false,
          message: 'Exhibition not found'
        });
      }
      res.json({
        success: true,
        data: exhibition
      });
    } catch (error) {
      next(error);
    }
  };

  getActive = async (req, res, next) => {
    try {
      const now = new Date();
      const allExhibitions = await db.findAll('exhibitions');
      const active = allExhibitions.filter(e => e.is_active);

      res.json({
        success: true,
        count: active.length,
        data: active
      });
    } catch (error) {
      next(error);
    }
  };

  create = async (req, res, next) => {
    try {
      const exhibition = await db.create('exhibitions', {
        ...req.body,
        visitor_count: 0,
        createdAt: new Date().toISOString()
      });
      res.status(201).json({
        success: true,
        message: 'Exhibition created',
        data: exhibition
      });
    } catch (error) {
      next(error);
    }
  };

  update = async (req, res, next) => {
    try {
      const exhibition = await db.findById('exhibitions', req.params.id);
      if (!exhibition) {
        return res.status(404).json({
          success: false,
          message: 'Exhibition not found'
        });
      }

      const updated = await db.update('exhibitions', req.params.id, req.body);
      res.json({
        success: true,
        message: 'Exhibition updated',
        data: updated
      });
    } catch (error) {
      next(error);
    }
  };

  delete = async (req, res, next) => {
    try {
      const exhibition = await db.findById('exhibitions', req.params.id);
      if (!exhibition) {
        return res.status(404).json({
          success: false,
          message: 'Exhibition not found'
        });
      }

      await db.delete('exhibitions', req.params.id);
      res.json({
        success: true,
        message: 'Exhibition deleted'
      });
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new ExhibitionController();