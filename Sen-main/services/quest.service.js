const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class QuestService extends BaseService {
  constructor() {
    super('game_quests');
  }

  async getAvailableQuests(userId) {
    const quests = (await db.findAll('game_quests')).filter(q => q.is_active);
    const userProgress = await db.findOne('user_progress', { user_id: userId });
    const completedQuestIds = userProgress?.completed_quests?.map(q => q.quest_id) || [];

    const available = quests.filter(q => !completedQuestIds.includes(q.id))
      .sort((a, b) => a.level - b.level);

    return {
      success: true,
      data: available,
      completed_count: completedQuestIds.length,
      available_count: available.length
    };
  }

  async completeQuest(questId, userId, score) {
    const quest = await db.findById('game_quests', questId);
    if (!quest) {
      return { success: false, message: 'Quest not found', statusCode: 404 };
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
        streak: 1,
        total_learning_time: 0,
        bookmarked_artifacts: [],
        bookmarked_sites: []
      });
    }

    const completedQuest = {
      quest_id: questId,
      completed_date: new Date().toISOString(),
      score: score,
      points_earned: quest.points,
      badges_earned: quest.badges || []
    };

    const newPoints = (userProgress.total_points || 0) + quest.points;
    const newLevel = Math.floor(newPoints / 500) + 1;

    const updated = await db.update('user_progress', userProgress.id, {
      completed_quests: [...(userProgress.completed_quests || []), completedQuest],
      total_points: newPoints,
      level: newLevel,
      badges: [...new Set([...(userProgress.badges || []), ...completedQuest.badges_earned])],
      streak: (userProgress.streak || 0) + 1
    });

    return {
      success: true,
      message: 'Quest completed successfully',
      data: {
        quest_title: quest.title,
        points_earned: quest.points,
        badges_earned: completedQuest.badges_earned,
        new_level: newLevel,
        total_points: newPoints
      }
    };
  }
  async getLeaderboard(limit = 10) {
    const allProgress = (await db.findAll('user_progress'))
      .sort((a, b) => (b.total_points || 0) - (a.total_points || 0))
      .slice(0, limit);

    const leaderboard = await Promise.all(allProgress.map(async (progress, index) => {
      const user = await db.findById('users', progress.user_id);
      return {
        rank: index + 1,
        user_name: user?.name || 'Unknown',
        user_avatar: user?.avatar,
        total_points: progress.total_points || 0,
        level: progress.level || 1,
        badges_count: progress.badges?.length || 0,
        completed_quests: progress.completed_quests?.length || 0
      };
    }));

    return {
      success: true,
      data: leaderboard
    };
  }
}

module.exports = new QuestService();
