const uploadService = require('../services/upload.service');
const db = require('../config/database');

class UploadController {
  /**
   * Get upload middleware based on type
   */
  getUploadMiddleware(type) {
    return (req, res, next) => {
      const middleware = uploadService.getSingleUpload('image', type);
      middleware(req, res, (err) => {
        if (err) {
          return res.status(400).json({
            success: false,
            message: err.message
          });
        }
        next();
      });
    };
  }

  /**
   * Upload avatar
   * POST /api/upload/avatar
   */
  uploadAvatar = async (req, res, next) => {
    try {
      if (!req.file) {
        return res.status(400).json({
          success: false,
          message: 'No file uploaded'
        });
      }

      const result = await uploadService.uploadAvatar(req.file, req.user.id);

      if (!result.success) {
        return res.status(400).json({
          success: false,
          message: result.error
        });
      }

      // Update user avatar in database
      const updatedUser = await db.update('users', req.user.id, {
        avatar: result.url,
        updatedAt: new Date().toISOString()
      });

      res.json({
        success: true,
        message: 'Avatar uploaded successfully',
        data: {
          url: result.url,
          filename: result.filename,
          user: {
            id: updatedUser.id,
            name: updatedUser.name,
            avatar: updatedUser.avatar
          }
        }
      });
    } catch (error) {
      next(error);
    }
  };





  /**
   * Upload category image
   * POST /api/upload/category/:categoryId
   */
  uploadCategoryImage = async (req, res, next) => {
    try {
      if (!req.file) {
        return res.status(400).json({
          success: false,
          message: 'No file uploaded'
        });
      }

      const { categoryId } = req.params;

      // Check category exists
      const category = await db.findById('categories', categoryId);
      if (!category) {
        return res.status(404).json({
          success: false,
          message: 'Category not found'
        });
      }

      const result = await uploadService.uploadCategoryImage(req.file, categoryId);

      if (!result.success) {
        return res.status(400).json({
          success: false,
          message: result.error
        });
      }

      // Update category image in database
      const updatedCategory = await db.update('categories', categoryId, {
        image: result.url,
        updatedAt: new Date().toISOString()
      });

      res.json({
        success: true,
        message: 'Category image uploaded successfully',
        data: {
          url: result.url,
          filename: result.filename,
          category: {
            id: updatedCategory.id,
            name: updatedCategory.name,
            image: updatedCategory.image
          }
        }
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Upload heritage site image
   */
  uploadHeritageSiteImage = async (req, res, next) => {
    try {
      if (!req.file) {
        return res.status(400).json({ success: false, message: 'Please upload a file' });
      }

      const result = await uploadService.uploadHeritageSiteImage(req.file, req.params.id);

      // Optional: Update database record
      // const db = require('../config/database');
      // db.update('heritage_sites', req.params.id, { image: result.url });

      res.status(200).json({
        success: true,
        data: result
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Upload artifact image
   */
  uploadArtifactImage = async (req, res, next) => {
    try {
      if (!req.file) {
        return res.status(400).json({ success: false, message: 'Please upload a file' });
      }

      const result = await uploadService.uploadArtifactImage(req.file, req.params.id);

      res.status(200).json({
        success: true,
        data: result
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Upload exhibition image
   */
  uploadExhibitionImage = async (req, res, next) => {
    try {
      if (!req.file) {
        return res.status(400).json({ success: false, message: 'Please upload a file' });
      }

      const result = await uploadService.uploadExhibitionImage(req.file, req.params.id);

      res.status(200).json({
        success: true,
        data: result
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Upload game asset
   */
  uploadGameAsset = async (req, res, next) => {
    try {
      if (!req.file) {
        return res.status(400).json({ success: false, message: 'Please upload a file' });
      }

      const { type, id } = req.params;
      const result = await uploadService.uploadGameAsset(req.file, type, id);

      res.status(200).json({
        success: true,
        data: result
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Delete file
   * DELETE /api/upload/file?url=/uploads/avatars/file.jpg
   */
  deleteFile = async (req, res, next) => {
    try {
      const { url } = req.query;

      if (!url) {
        return res.status(400).json({
          success: false,
          message: 'URL parameter is required'
        });
      }

      const result = await uploadService.deleteFile(url);

      if (!result.success) {
        return res.status(404).json({
          success: false,
          message: result.message
        });
      }

      res.json({
        success: true,
        message: 'File deleted successfully'
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Get file info
   * GET /api/upload/file/info?url=/uploads/avatars/file.jpg
   */
  getFileInfo = async (req, res, next) => {
    try {
      const { url } = req.query;

      if (!url) {
        return res.status(400).json({
          success: false,
          message: 'URL parameter is required'
        });
      }

      const result = await uploadService.getFileInfo(url);

      if (!result.success) {
        return res.status(404).json({
          success: false,
          message: result.message
        });
      }

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Get storage statistics
   * GET /api/upload/stats
   */
  getStorageStats = async (req, res, next) => {
    try {
      const result = await uploadService.getStorageStats();

      res.json({
        success: true,
        data: result.data
      });
    } catch (error) {
      next(error);
    }
  };

  /**
   * Cleanup old files
   * POST /api/upload/cleanup
   */
  cleanupOldFiles = async (req, res, next) => {
    try {
      const { days = 30 } = req.body;

      const result = await uploadService.cleanupOldFiles(days);

      res.json({
        success: true,
        message: result.message,
        data: {
          deletedCount: result.deletedCount
        }
      });
    } catch (error) {
      next(error);
    }
  };
}

module.exports = new UploadController();