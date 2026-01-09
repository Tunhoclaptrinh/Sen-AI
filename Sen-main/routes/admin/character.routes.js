const express = require('express');
const router = express.Router();
const { protect, authorize } = require('../../middleware/auth.middleware');
const characterCMSController = require('../../controllers/character_cms.controller');

// Bảo vệ route, chỉ Admin được truy cập
router.use(protect, authorize('admin'));

router.get('/', characterCMSController.getAll);
router.get('/:id', characterCMSController.getById);
router.post('/', characterCMSController.create);
router.put('/:id', characterCMSController.update);
router.delete('/:id', characterCMSController.delete);

module.exports = router;