const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const aiController = require('../controllers/ai.controller');

// All AI routes require authentication
router.use(protect);

router.post('/chat', aiController.chat);
router.get('/history', aiController.getHistory);
router.post('/ask-hint', aiController.askHint);
router.post('/explain', aiController.explain);
router.post('/quiz', aiController.generateQuiz);
router.delete('/history', aiController.clearHistory);

module.exports = router;