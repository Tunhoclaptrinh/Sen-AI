
/**
 * routes/admin/level.routes.js
 * Admin routes để quản lý levels (CMS)
 */

const express = require('express');
const router = express.Router();
const { protect } = require('../../middleware/auth.middleware');
const { checkPermission } = require('../../middleware/rbac.middleware');
const levelCMSController = require('../../controllers/level_cms.controller');

// Yêu cầu đăng nhập và quyền 'game_content'
router.use(protect, checkPermission('game_content', 'read'));

// Templates & Stats
router.get('/templates', levelCMSController.getTemplates);
router.get('/stats', levelCMSController.getStats);
router.post('/validate', checkPermission('game_content', 'create'), levelCMSController.validateLevel);

// ==================== CRUD ====================
router.get('/', levelCMSController.getAllLevels);
router.get('/:id', levelCMSController.getLevelDetail);
router.get('/:id/preview', levelCMSController.previewLevel);

router.post('/', checkPermission('game_content', 'create'), levelCMSController.createLevel);
router.put('/:id', checkPermission('game_content', 'update'), levelCMSController.updateLevel);
router.delete('/:id', checkPermission('game_content', 'delete'), levelCMSController.deleteLevel);

// ==================== ADVANCED OPERATIONS ====================
router.post('/:id/clone', checkPermission('game_content', 'create'), levelCMSController.cloneLevel);
router.post('/bulk/import', checkPermission('game_content', 'import'), levelCMSController.bulkImport);
router.put('/chapters/:chapterId/reorder', checkPermission('game_content', 'update'), levelCMSController.reorderLevels);

module.exports = router;