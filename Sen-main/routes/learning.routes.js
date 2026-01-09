const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const learningController = require('../controllers/learning.controller');

router.get('/', learningController.getAll);
router.get('/path', protect, learningController.getLearningPath);
router.get('/:id', learningController.getById);

router.post('/', protect, learningController.create);
router.post('/:id/complete', protect, learningController.complete);
router.put('/:id', protect, learningController.update);
router.delete('/:id', protect, learningController.delete);

module.exports = router;