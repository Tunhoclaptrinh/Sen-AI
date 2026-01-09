const express = require('express');
const router = express.Router();
const { protect, authorize } = require('../../middleware/auth.middleware');
const assetCMSController = require('../../controllers/asset_cms.controller');

router.use(protect, authorize('admin'));

router.get('/', assetCMSController.getAll);
router.get('/:id', assetCMSController.getById);
router.post('/', assetCMSController.create);
router.put('/:id', assetCMSController.update);
router.delete('/:id', assetCMSController.delete);

module.exports = router;