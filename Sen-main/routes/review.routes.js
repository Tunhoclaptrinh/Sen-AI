const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const { checkPermission } = require('../middleware/rbac.middleware');
const reviewController = require('../controllers/review.controller');

// Public
router.get('/', reviewController.getAll);
router.get('/stats/summary', reviewController.getStats);
router.get('/type/:type', reviewController.getByType);

// User Actions
router.post('/',
  protect,
  checkPermission('reviews', 'create'),
  reviewController.create
);

router.put('/:id',
  protect,
  checkPermission('reviews', 'update_own'),
  reviewController.update
);

// User xóa review của mình, Admin xóa review vi phạm
// Controller cần handle logic: if (admin) delete; else if (owner) delete; else 403
router.delete('/:id',
  protect,
  reviewController.delete
);

module.exports = router;