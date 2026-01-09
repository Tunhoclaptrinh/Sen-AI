const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const { checkPermission } = require('../middleware/rbac.middleware');
const heritageSiteController = require('../controllers/heritage_site.controller');

// Public Routes
router.get('/', heritageSiteController.getAll);
router.get('/search', heritageSiteController.search);
router.get('/nearby', heritageSiteController.getNearby);
router.get('/stats/summary', heritageSiteController.getStats);
router.get('/:id', heritageSiteController.getById);
router.get('/:id/artifacts', heritageSiteController.getArtifacts);
router.get('/:id/timeline', heritageSiteController.getTimeline);

// Protected Routes (Researcher/Admin)
router.post('/',
  protect,
  checkPermission('heritage_sites', 'create'),
  heritageSiteController.create
);

router.put('/:id',
  protect,
  checkPermission('heritage_sites', 'update'),
  heritageSiteController.update
);

// Chỉ Admin được xóa
router.delete('/:id',
  protect,
  checkPermission('heritage_sites', 'delete'),
  heritageSiteController.delete
);

module.exports = router;