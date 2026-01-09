const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const { checkPermission } = require('../middleware/rbac.middleware');
const exhibitionController = require('../controllers/exhibition.controller');

// Public
router.get('/', exhibitionController.getAll);
router.get('/active', exhibitionController.getActive);
router.get('/:id', exhibitionController.getById);

// Protected
router.post('/',
  protect,
  checkPermission('exhibitions', 'create'),
  exhibitionController.create
);

router.put('/:id',
  protect,
  checkPermission('exhibitions', 'update'),
  exhibitionController.update
);

router.delete('/:id',
  protect,
  checkPermission('exhibitions', 'delete'),
  exhibitionController.delete
);

module.exports = router;