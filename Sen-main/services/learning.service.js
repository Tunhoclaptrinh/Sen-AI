const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class LearningService extends BaseService {
  constructor() {
    super('learning_modules');
  }

  async completeModule(moduleId, userId, score) {
    const module = await db.findById('learning_modules', moduleId);
    if (!module) {
      return { success: false, message: 'Module not found', statusCode: 404 };
    }

    let userProgress = await db.findOne('user_progress', { user_id: userId });
    if (!userProgress) {
      userProgress = await db.create('user_progress', {
        user_id: userId,
        completed_modules: [],
        completed_quests: [],
        total_points: 0,
        level: 1,
        badges: [],
        achievements: [],
        streak: 0,
        total_learning_time: 0,
        bookmarked_artifacts: [],
        bookmarked_sites: []
      });
    }

    const completedModule = {
      module_id: moduleId,
      completed_date: new Date().toISOString(),
      score: score,
      time_spent: 0
    };

    const passingScore = module.quiz?.passing_score || 70;
    const points = score >= passingScore ? 50 : 0;

    // Level calculation: Every 200 points = 1 level
    const newTotalPoints = (userProgress.total_points || 0) + points;
    const newLevel = Math.floor(newTotalPoints / 200) + 1;

    // Badge logic
    let newBadges = [...(userProgress.badges || [])];
    const completedCount = (userProgress.completed_modules || []).length + 1;

    if (completedCount === 1 && !newBadges.includes('newbie')) {
      newBadges.push('newbie'); // Badge: Người Mới Bắt Đầu
    }
    if (score === 100 && !newBadges.includes('perfect_score')) {
      newBadges.push('perfect_score'); // Badge: Điểm Tuyệt Đối
    }
    if (newLevel > (userProgress.level || 1)) {
      // Logic for level up badge could go here
    }

    const updated = await db.update('user_progress', userProgress.id, {
      completed_modules: [...(userProgress.completed_modules || []), completedModule],
      total_points: newTotalPoints,
      level: newLevel,
      badges: newBadges
    });

    return {
      success: true,
      message: 'Module completed',
      data: {
        module_title: module.title,
        score: score,
        points_earned: points,
        passed: score >= passingScore
      }
    };
  }

  async getLearningPath(userId) {
    const userProgress = await db.findOne('user_progress', { user_id: userId });
    const allModules = (await db.findAll('learning_modules'))
      .sort((a, b) => a.order - b.order);

    const completedModuleIds = userProgress?.completed_modules?.map(m => m.module_id) || [];

    const path = allModules.map(module => {
      const completedData = userProgress?.completed_modules?.find(m => m.module_id === module.id);

      return {
        id: module.id,
        title: module.title,
        difficulty: module.difficulty,
        estimated_duration: module.estimated_duration,
        is_completed: completedModuleIds.includes(module.id),
        score: completedData?.score
      };
    });

    return {
      success: true,
      data: path,
      progress: {
        completed: completedModuleIds.length,
        total: allModules.length,
        percentage: Math.round((completedModuleIds.length / allModules.length) * 100)
      }
    };
  }
}

module.exports = new LearningService();