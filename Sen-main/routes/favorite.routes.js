// routes/favorite.routes.js - UPDATED: Unified routes
const express = require('express');
const router = express.Router();
const favoriteController = require('../controllers/favorite.controller');
const { protect } = require('../middleware/auth.middleware');
const { validateSchema, validateFields } = require('../middleware/validation.middleware');

router.use(protect); // All routes need auth

// 1. Static/Specific Routes FIRST
router.get('/', favoriteController.getFavorites);
router.get('/stats/summary', favoriteController.getFavoriteStats);
router.delete('/', favoriteController.clearAll);

// 2. Complex Specific Routes
router.get('/trending/:type', favoriteController.getTrendingFavorites);

// 3. Dynamic Routes (/:type can capture 'stats' if not careful, so it goes last)
router.get('/:type', favoriteController.getFavoritesByType);
router.get('/:type/ids', favoriteController.getFavoriteIds);
router.get('/:type/:id/check', favoriteController.checkFavorite);

router.post('/:type/:id/toggle',
  // validateFields('favorite', ['type']), // Optional: re-enable if needed
  favoriteController.toggleFavorite
);

router.post('/:type/:id',
  // validateFields('favorite', ['type']),
  favoriteController.addFavorite
);

router.delete('/:type/:id', favoriteController.removeFavorite);
router.delete('/:type', favoriteController.clearByType);

module.exports = router;