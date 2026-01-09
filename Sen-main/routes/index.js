const express = require('express');
const router = express.Router();

// Auth
router.use('/auth', require('./auth.routes'));
router.use('/users', require('./user.routes'));

// Heritage & Education
router.use('/heritage-sites', require('./heritage_site.routes'));
router.use('/artifacts', require('./artifact.routes'));
router.use('/categories', require('./category.routes'));
router.use('/exhibitions', require('./exhibition.routes'));
router.use('/learning', require('./learning.routes'));

// User Content
router.use('/collections', require('./collection.routes'));
router.use('/reviews', require('./review.routes'));
router.use('/favorites', require('./favorite.routes'));

// Game System
router.use('/game', require('./game.routes'));
router.use('/ai', require('./ai.routes'));
router.use('/quests', require('./quest.routes'));

router.use('/upload', require('./upload.routes'));
router.use('/notifications', require('./notification.routes'));


module.exports = router;