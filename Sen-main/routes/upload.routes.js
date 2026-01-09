const express = require('express');
const router = express.Router();
const uploadController = require('../controllers/upload.controller');
const { protect, authorize } = require('../middleware/auth.middleware');

// Avatar upload (Customer only)
router.post('/avatar',
  protect,
  uploadController.getUploadMiddleware('avatar'),
  uploadController.uploadAvatar
);



// Category image (Admin only)
router.post('/category/:categoryId',
  protect,
  authorize('admin'),
  uploadController.getUploadMiddleware('category'),
  uploadController.uploadCategoryImage
);

// Heritage Site image (Admin/Researcher)
router.post('/heritage-site/:id',
  protect,
  authorize('admin', 'researcher'),
  uploadController.getUploadMiddleware('heritage_sites'),
  uploadController.uploadHeritageSiteImage
);

// Artifact image (Admin/Researcher)
router.post('/artifact/:id',
  protect,
  authorize('admin', 'researcher'),
  uploadController.getUploadMiddleware('artifacts'),
  uploadController.uploadArtifactImage
);

// Exhibition image (Admin)
router.post('/exhibition/:id',
  protect,
  authorize('admin'),
  uploadController.getUploadMiddleware('exhibitions'),
  uploadController.uploadExhibitionImage
);

// Game Asset (Admin) - type: character, badge, level_thumb
router.post('/game/:type/:id',
  protect,
  authorize('admin'),
  uploadController.getUploadMiddleware('game_assets'),
  uploadController.uploadGameAsset
);

// Delete file (Admin only)
router.delete('/file',
  protect,
  authorize('admin'),
  uploadController.deleteFile
);

// Get file info
router.get('/file/info',
  protect,
  uploadController.getFileInfo
);

// Storage stats (Admin only)
router.get('/stats',
  protect,
  authorize('admin'),
  uploadController.getStorageStats
);

// Cleanup old files (Admin only)
router.post('/cleanup',
  protect,
  authorize('admin'),
  uploadController.cleanupOldFiles
);

module.exports = router;