const BaseService = require('../utils/BaseService');
const db = require('../config/database');
const { sanitizeUser, hashPassword } = require('../utils/helpers');
const userSchema = require('../schemas/user.schema');

class UserService extends BaseService {
  constructor() {
    super('users');
  }

  /**
   * Get schema for import/export
   */
  getSchema() {
    return userSchema;
  }

  /**
   * Transform import data - hash password
   */
  async transformImportData(data) {
    const transformed = await super.transformImportData(data);

    // Hash password if provided
    if (transformed.password) {
      transformed.password = await hashPassword(transformed.password);
    }

    // Generate avatar if not provided
    if (!transformed.avatar && transformed.name) {
      transformed.avatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(transformed.name)}&background=random`;
    }

    return transformed;
  }

  async beforeCreate(data) {
    if (data.password) {
      data.password = await hashPassword(data.password);
    }

    // Generate avatar if not provided
    if (!data.avatar && data.name) {
      data.avatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(data.name)}&background=random`;
    }

    return {
      ...data,
      isActive: data.isActive !== undefined ? data.isActive : true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  }

  async beforeUpdate(id, data) {
    if (data.newPassword) {
      data.password = await hashPassword(data.newPassword);
      delete data.newPassword;
    }

    // Hash password if provided directly (for admin updates)
    if (data.password) {
      data.password = await hashPassword(data.password);
    }

    return {
      ...data,
      updatedAt: new Date().toISOString()
    };
  }

  async getUserStats() {
    const users = await db.findAll('users');
    const progress = await db.findAll('game_progress');

    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);

    const stats = {
      total: users.length,
      active: users.filter(u => u.isActive).length,
      inactive: users.filter(u => !u.isActive).length,
      byRole: {
        customer: users.filter(u => u.role === 'customer').length,
        admin: users.filter(u => u.role === 'admin').length,
        researcher: users.filter(u => u.role === 'researcher').length
      },
      activePlayers: progress.filter(p => {
        const lastLogin = new Date(p.last_login);
        return lastLogin >= weekAgo;
      }).length,
      recentSignups: users.filter(u => {
        const createdAt = new Date(u.createdAt);
        return createdAt >= weekAgo;
      }).length
    };

    return {
      success: true,
      data: stats
    };
  }

  async getUserActivity(userId) {
    const user = await db.findById('users', userId);

    if (!user) {
      return {
        success: false,
        message: 'User not found',
        statusCode: 404
      };
    }

    const progress = await db.findOne('game_progress', { user_id: userId });
    const sessions = await db.findMany('game_sessions', { user_id: userId });
    const scans = await db.findMany('scan_history', { user_id: userId });
    const favorites = await db.findMany('favorites', { user_id: userId });

    const activity = {
      user: sanitizeUser(user),
      gameStats: progress ? {
        level: progress.level,
        coins: progress.coins,
        petals: progress.total_sen_petals,
        characters: progress.collected_characters?.length || 0,
        badges: progress.badges?.length || 0,
        streak: progress.streak_days,
        lastLogin: progress.last_login
      } : null,
      recentSessions: sessions
        .sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
        .slice(0, 5),
      recentScans: scans
        .sort((a, b) => new Date(b.scanned_at) - new Date(a.scanned_at))
        .slice(0, 5),
      totalFavorites: favorites.length
    };

    return {
      success: true,
      data: activity
    };
  }

  async toggleUserStatus(userId) {
    const user = await db.findById('users', userId);

    if (!user) {
      return {
        success: false,
        message: 'User not found',
        statusCode: 404
      };
    }

    const updated = await db.update('users', userId, {
      isActive: !user.isActive,
      updatedAt: new Date().toISOString()
    });

    return {
      success: true,
      message: `User ${updated.isActive ? 'activated' : 'deactivated'} successfully`,
      data: sanitizeUser(updated)
    };
  }

  async permanentDeleteUser(userId) {
    const user = await db.findById('users', userId);

    if (!user) {
      return {
        success: false,
        message: 'User not found',
        statusCode: 404
      };
    }

    const deleted = {
      user: 1,
      game_progress: 0,
      game_sessions: 0,
      user_inventory: 0,
      scan_history: 0,
      favorites: 0,
      collections: 0,
      notifications: 0
    };

    // Helper to delete many
    const deleteRelated = async (collection, filter) => {
      const items = await db.findMany(collection, filter);
      for (const item of items) {
        await db.delete(collection, item.id);
        if (deleted[collection] !== undefined) deleted[collection]++;
      }
    };

    // Delete all related data
    await deleteRelated('game_progress', { user_id: userId });
    await deleteRelated('game_sessions', { user_id: userId });
    await deleteRelated('user_inventory', { user_id: userId });
    await deleteRelated('scan_history', { user_id: userId });
    await deleteRelated('favorites', { user_id: userId });
    await deleteRelated('collections', { user_id: userId });
    await deleteRelated('notifications', { user_id: userId });

    // Finally delete user
    await db.delete('users', userId);

    return {
      success: true,
      message: 'User and all related data permanently deleted',
      deleted
    };
  }
}

module.exports = new UserService();