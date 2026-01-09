const db = require('../config/database');

class CollectionController {
  getAll = async (req, res, next) => {
    try {
      const collections = await db.findMany('collections', { user_id: req.user.id });
      res.json({
        success: true,
        count: collections.length,
        data: collections
      });
    } catch (error) {
      next(error);
    }
  };

  getById = async (req, res, next) => {
    try {
      const collection = await db.findById('collections', req.params.id);
      if (!collection) {
        return res.status(404).json({
          success: false,
          message: 'Collection not found'
        });
      }

      if (collection.user_id !== req.user.id && req.user.role !== 'admin') {
        return res.status(403).json({
          success: false,
          message: 'Not authorized'
        });
      }

      res.json({
        success: true,
        data: collection
      });
    } catch (error) {
      next(error);
    }
  };

  create = async (req, res, next) => {
    try {
      const collection = await db.create('collections', {
        ...req.body,
        user_id: req.user.id,
        artifact_ids: req.body.artifact_ids || [],
        heritage_site_ids: req.body.heritage_site_ids || [],
        exhibition_ids: req.body.exhibition_ids || [],
        total_items: (req.body.artifact_ids || []).length,
        createdAt: new Date().toISOString()
      });

      res.status(201).json({
        success: true,
        message: 'Collection created',
        data: collection
      });
    } catch (error) {
      next(error);
    }
  };

  update = async (req, res, next) => {
    try {
      const collection = await db.findById('collections', req.params.id);
      if (!collection) {
        return res.status(404).json({
          success: false,
          message: 'Collection not found'
        });
      }

      if (collection.user_id !== req.user.id && req.user.role !== 'admin') {
        return res.status(403).json({
          success: false,
          message: 'Not authorized'
        });
      }

      const updated = await db.update('collections', req.params.id, {
        ...req.body,
        updatedAt: new Date().toISOString()
      });

      res.json({
        success: true,
        message: 'Collection updated',
        data: updated
      });
    } catch (error) {
      next(error);
    }
  };

  delete = async (req, res, next) => {
    try {
      const collection = await db.findById('collections', req.params.id);
      if (!collection) {
        return res.status(404).json({
          success: false,
          message: 'Collection not found'
        });
      }

      if (collection.user_id !== req.user.id && req.user.role !== 'admin') {
        return res.status(403).json({
          success: false,
          message: 'Not authorized'
        });
      }

      await db.delete('collections', req.params.id);
      res.json({
        success: true,
        message: 'Collection deleted'
      });
    } catch (error) {
      next(error);
    }
  };

  addArtifact = async (req, res, next) => {
    try {
      const collection = await db.findById('collections', req.params.id);
      if (!collection) {
        return res.status(404).json({
          success: false,
          message: 'Collection not found'
        });
      }

      if (collection.user_id !== req.user.id) {
        return res.status(403).json({
          success: false,
          message: 'Not authorized'
        });
      }

      if (collection.artifact_ids.includes(parseInt(req.params.artifactId))) {
        return res.status(400).json({
          success: false,
          message: 'Artifact already in collection'
        });
      }

      const updated = await db.update('collections', req.params.id, {
        artifact_ids: [...collection.artifact_ids, parseInt(req.params.artifactId)],
        total_items: (collection.artifact_ids.length || 0) + 1
      });

      res.json({
        success: true,
        message: 'Artifact added to collection',
        data: updated
      });
    } catch (error) {
      next(error);
    }
  };

  removeArtifact = async (req, res, next) => {
    try {
      const collection = await db.findById('collections', req.params.id);
      if (!collection) {
        return res.status(404).json({
          success: false,
          message: 'Collection not found'
        });
      }

      if (collection.user_id !== req.user.id) {
        return res.status(403).json({
          success: false,
          message: 'Not authorized'
        });
      }

      const updated = await db.update('collections', req.params.id, {
        artifact_ids: collection.artifact_ids.filter(id => id !== parseInt(req.params.artifactId)),
        total_items: (collection.artifact_ids.length || 1) - 1
      });

      res.json({
        success: true,
        message: 'Artifact removed from collection',
        data: updated
      });
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new CollectionController();
