const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const { checkPermission } = require('../middleware/rbac.middleware');
const categoryController = require('../controllers/category.controller');
const { validateSchema } = require('../middleware/validation.middleware');

// Public
router.get('/', categoryController.getAll);
router.get('/:id', categoryController.getById);
router.get('/:id/items', categoryController.getItems);

// Protected (Admin & Researcher có thể tạo category mới nếu cần)
router.post('/',
  protect,
  checkPermission('categories', 'create'),
  validateSchema('cultural_category'),
  categoryController.create
);

router.put('/:id',
  protect,
  checkPermission('categories', 'update'),
  validateSchema('cultural_category'),
  categoryController.update
);

// Chỉ Admin được xóa danh mục (tránh vỡ data)
router.delete('/:id',
  protect,
  checkPermission('categories', 'delete'),
  categoryController.delete
);

module.exports = router;