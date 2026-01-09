const express = require('express');
const router = express.Router();
const { protect, authorize } = require('../../middleware/auth.middleware');
const chapterCMSController = require('../../controllers/chapter_cms.controller');

// Bảo vệ tất cả routes, chỉ Admin mới được truy cập
router.use(protect, authorize('admin'));

router.get('/', chapterCMSController.getAll);
router.get('/:id', chapterCMSController.getById);
router.post('/', chapterCMSController.create);
router.put('/:id', chapterCMSController.update);
router.delete('/:id', chapterCMSController.delete);

module.exports = router;