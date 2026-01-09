/**
 * routes/admin/index.js
 * Mount all admin routes
 */

const express = require('express');
const router = express.Router();
const { protect } = require('../../middleware/auth.middleware');
const { checkPermission } = require('../../middleware/rbac.middleware');

// 🔒 CRITICAL: Protect all admin routes - require authentication and admin permissions
router.use(protect);
router.use(checkPermission('game_content', 'read'));

router.use('/levels', require('./level.routes'));
router.use('/chapters', require('./chapter.routes'));
router.use('/characters', require('./character.routes'));
router.use('/assets', require('./asset.routes'));

module.exports = router;