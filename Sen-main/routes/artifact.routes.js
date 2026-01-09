const express = require('express');
const router = express.Router();
const { protect, authorize } = require('../middleware/auth.middleware');
const artifactController = require('../controllers/artifact.controller');

router.get('/', artifactController.getAll);
router.get('/search', artifactController.search);
router.get('/stats/summary', artifactController.getStats);
router.get('/:id', artifactController.getById);
router.get('/:id/related', artifactController.getRelated);

router.post('/', protect, authorize('admin'), artifactController.create);
router.put('/:id', protect, authorize('admin'), artifactController.update);
router.delete('/:id', protect, authorize('admin'), artifactController.delete);

module.exports = router;
