const db = require('../config/database');
const artifactService = require('../services/artifact.service');

class ArtifactController {
  getAll = async (req, res, next) => {
    try {
      const result = await db.findAllAdvanced('artifacts', req.parsedQuery);
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
      const artifact = await db.findById('artifacts', req.params.id);
      if (!artifact) {
        return res.status(404).json({
          success: false,
          message: 'Artifact not found'
        });
      }
      res.json({
        success: true,
        data: artifact
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

      const result = await db.findAllAdvanced('artifacts', {
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

  getRelated = async (req, res, next) => {
    try {
      const artifact = await db.findById('artifacts', req.params.id);
      if (!artifact) {
        return res.status(404).json({
          success: false,
          message: 'Artifact not found'
        });
      }

      const allArtifacts = await db.findAll('artifacts');
      const related = allArtifacts
        .filter(a =>
          a.id !== parseInt(req.params.id) &&
          (a.heritage_site_id === artifact.heritage_site_id ||
            a.cultural_category_id === artifact.cultural_category_id)
        )
        .slice(0, 5);

      res.json({
        success: true,
        data: related,
        count: related.length
      });
    } catch (error) {
      next(error);
    }
  };

  create = async (req, res, next) => {
    try {
      const artifact = await db.create('artifacts', {
        ...req.body,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      });
      res.status(201).json({
        success: true,
        message: 'Artifact created',
        data: artifact
      });
    } catch (error) {
      next(error);
    }
  };

  update = async (req, res, next) => {
    try {
      const artifact = await db.findById('artifacts', req.params.id);
      if (!artifact) {
        return res.status(404).json({
          success: false,
          message: 'Artifact not found'
        });
      }

      const updated = await db.update('artifacts', req.params.id, {
        ...req.body,
        updatedAt: new Date().toISOString()
      });

      res.json({
        success: true,
        message: 'Artifact updated',
        data: updated
      });
    } catch (error) {
      next(error);
    }
  };

  delete = async (req, res, next) => {
    try {
      const artifact = await db.findById('artifacts', req.params.id);
      if (!artifact) {
        return res.status(404).json({
          success: false,
          message: 'Artifact not found'
        });
      }

      await db.delete('artifacts', req.params.id);
      res.json({
        success: true,
        message: 'Artifact deleted'
      });
    } catch (error) {
      next(error);
    }
  };

  getStats = async (req, res, next) => {
    try {
      const result = await artifactService.getStats();
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new ArtifactController();
