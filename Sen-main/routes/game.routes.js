const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/auth.middleware');
const { checkPermission } = require('../middleware/rbac.middleware');
const gameController = require('../controllers/game.controller');

router.use(protect); // Bắt buộc đăng nhập

// Áp dụng quyền 'game_play' cho các action chơi game
const requireGamePlay = checkPermission('game_play', 'play');

router.get('/progress', requireGamePlay, gameController.getProgress);
router.get('/leaderboard', requireGamePlay, gameController.getLeaderboard);
router.get('/daily-reward', checkPermission('game_play', 'earn_rewards'), gameController.getDailyReward);

// ==================== CHAPTERS (SEN FLOWERS) ====================
router.get('/chapters', gameController.getChapters);
router.get('/chapters/:id', gameController.getChapterDetail);
router.post('/chapters/:id/unlock', gameController.unlockChapter);

// ==================== LEVELS (MÀN CHƠI) ====================
router.get('/levels/:chapterId', gameController.getLevels);
router.get('/levels/:id/detail', gameController.getLevelDetail);

// Level Session Management
router.post('/levels/:id/start', requireGamePlay, gameController.startLevel);
router.post('/levels/:id/collect-clue', requireGamePlay, gameController.collectClue);
router.post('/levels/:id/complete', requireGamePlay, gameController.completeLevel);

// ==================== SCREEN NAVIGATION (NEW) ====================
router.post('/sessions/:id/next-screen', requireGamePlay, gameController.navigateToNextScreen);
router.post('/sessions/:id/submit-answer', requireGamePlay, gameController.submitAnswer);
router.post('/sessions/:sessionId/submit-timeline',
  requireGamePlay,
  gameController.submitTimelineOrder
);

// ==================== MUSEUM ====================
router.get('/museum', requireGamePlay, gameController.getMuseum);
router.post('/museum/toggle', requireGamePlay, gameController.toggleMuseum);
router.post('/museum/collect', checkPermission('game_play', 'earn_rewards'), gameController.collectMuseumIncome);

// ==================== BADGES & ACHIEVEMENTS ====================
router.get('/badges', gameController.getBadges);
router.get('/achievements', gameController.getAchievements);

// ==================== SCAN TO PLAY ====================
router.post('/scan', checkPermission('game_play', 'scan_qr'), gameController.scanObject);

// ==================== SHOP & INVENTORY ====================
router.post('/shop/purchase', checkPermission('shop', 'purchase'), gameController.purchaseItem);
router.get('/inventory', requireGamePlay, gameController.getInventory);
router.post('/inventory/use', checkPermission('shop', 'use_item'), gameController.useItem);

module.exports = router;