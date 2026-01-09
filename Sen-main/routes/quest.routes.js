const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const questController = require('../controllers/quest.controller');

router.get('/', questController.getAll);
router.get('/available', protect, questController.getAvailable);
router.get('/leaderboard', questController.getLeaderboard);
router.get('/:id', questController.getById);

router.post('/', protect, questController.create);
router.post('/:id/complete', protect, questController.complete);
router.put('/:id', protect, questController.update);
router.delete('/:id', protect, questController.delete);

module.exports = router;
