/**
 * Unified Game Service - FIXED VERSION
 * Sửa lỗi duplicate methods, thêm missing implementations
 */

const db = require('../config/database');
const { calculateDistance } = require('../utils/helpers');

class GameService {
  constructor() {
    // Khởi tạo Set để track sessions đang được xử lý
    this.activeLocks = new Set();

    // Bắt đầu background cleanup job
    this.startSessionCleanup();
  }

  // ==================== INITIALIZATION ====================

  /**
   * Khởi tạo game progress cho user mới
   */
  async initializeProgress(userId) {
    const existing = await db.findOne('game_progress', { user_id: userId });
    if (existing) return existing;

    return await db.create('game_progress', {
      user_id: userId,
      current_chapter: 1,
      total_sen_petals: 0,
      total_points: 0,
      level: 1,
      coins: 1000,
      unlocked_chapters: [1],
      completed_levels: [],
      collected_characters: [],
      badges: [],
      achievements: [],
      museum_open: false,
      museum_income: 0,
      streak_days: 0,
      last_login: new Date().toISOString(),
      created_at: new Date().toISOString()
    });
  }

  // ==================== SESSION TIMEOUT CLEANUP ====================

  /**
   * Bắt đầu background job để cleanup sessions timeout
   */
  startSessionCleanup() {
    const SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 hours
    const CLEANUP_INTERVAL = 60 * 60 * 1000; // Run every 1 hour

    console.log('🧹 Session cleanup job started (runs every hour)');

    // Run ngay lần đầu
    this.cleanupExpiredSessions(SESSION_TIMEOUT).catch(err =>
      console.error('❌ Initial session cleanup error:', err)
    );

    // Sau đó chạy định kỳ
    setInterval(() => {
      this.cleanupExpiredSessions(SESSION_TIMEOUT).catch(err =>
        console.error('❌ Scheduled session cleanup error:', err)
      );
    }, CLEANUP_INTERVAL);
  }

  /**
   * Cleanup các sessions đã expired
   */
  async cleanupExpiredSessions(timeout) {
    try {
      const now = Date.now();
      const allSessions = await db.findAll('game_sessions');

      let expiredCount = 0;

      for (const session of allSessions) {
        // Chỉ cleanup sessions đang in_progress
        if (session.status !== 'in_progress') continue;

        const startTime = new Date(session.started_at).getTime();
        const lastActivity = session.last_activity
          ? new Date(session.last_activity).getTime()
          : startTime;

        // Check theo last_activity (quan trọng hơn started_at)
        if (now - lastActivity > timeout) {
          await db.update('game_sessions', session.id, {
            status: 'expired',
            expired_at: new Date().toISOString(),
            expired_reason: 'Session timeout (24 hours inactive)'
          });
          expiredCount++;
        }
      }

      if (expiredCount > 0) {
        console.log(`🧹 Cleaned up ${expiredCount} expired sessions`);
      }
    } catch (error) {
      console.error('❌ Session cleanup error:', error);
    }
  }

  /**
   * Get active session với timeout check
   */
  async getActiveSession(levelId, userId) {
    const session = await db.findOne('game_sessions', {
      level_id: levelId,
      user_id: userId,
      status: 'in_progress'
    });

    if (!session) return null;

    // Check timeout
    const SESSION_TIMEOUT = 24 * 60 * 60 * 1000;
    const lastActivity = new Date(session.last_activity || session.started_at).getTime();
    const now = Date.now();

    if (now - lastActivity > SESSION_TIMEOUT) {
      // Auto-expire
      await db.update('game_sessions', session.id, {
        status: 'expired',
        expired_at: new Date().toISOString(),
        expired_reason: 'Session timeout'
      });
      return null;
    }

    return session;
  }



  // ==================== PROGRESS & STATS ====================

  /**
 * Lấy tiến độ game của user
 */
  async getProgress(userId) {
    let progress = await db.findOne('game_progress', { user_id: userId });
    if (!progress) {
      progress = await this.initializeProgress(userId);
    }

    // Tính toán thống kê - using countDocuments via findMany/findAll if direct count not available
    // Optimization: In MongoAdapter, findAll returns expected array but efficiently countDocuments is better.
    // However, keeping consistent with db interface
    const allChapters = await db.findAll('game_chapters');
    const totalChapters = allChapters.length;

    const allLevels = await db.findAll('game_levels');
    const totalLevels = allLevels.length;

    return {
      success: true,
      data: {
        ...progress,
        stats: {
          completion_rate: totalLevels > 0 ? Math.round((progress.completed_levels.length / totalLevels) * 100) : 0,
          chapters_unlocked: progress.unlocked_chapters.length,
          total_chapters: totalChapters,
          characters_collected: progress.collected_characters.length,
          total_badges: progress.badges.length
        }
      }
    };
  }

  // ==================== CHAPTERS ====================

  /**
 * Lấy danh sách chapters (cánh hoa sen)
 */
  /**
   * Lấy danh sách chapters (cánh hoa sen)
   */
  async getChapters(userId) {
    const progress = await this.getProgress(userId);
    const chaptersData = await db.findAll('game_chapters');
    const chapters = chaptersData.sort((a, b) => a.order - b.order);

    const enriched = await Promise.all(chapters.map(async (chapter) => {
      const isUnlocked = progress.data.unlocked_chapters.includes(chapter.id);
      const levels = await db.findMany('game_levels', { chapter_id: chapter.id });
      const completedCount = levels.filter(l =>
        progress.data.completed_levels.includes(l.id)
      ).length;

      return {
        ...chapter,
        is_unlocked: isUnlocked,
        total_levels: levels.length,
        completed_levels: completedCount,
        completion_rate: levels.length > 0
          ? Math.round((completedCount / levels.length) * 100)
          : 0,
        can_unlock: this.canUnlockChapter(chapter, progress.data)
      };
    }));

    return { success: true, data: enriched };
  }

  /**
   * Kiểm tra có thể mở khóa chapter không (Sync logic, no DB calls)
   */
  canUnlockChapter(chapter, progress) {
    if (chapter.required_petals === 0) return true;
    return progress.total_sen_petals >= chapter.required_petals;
  }

  /**
   * Chi tiết một chapter
   */
  async getChapterDetail(chapterId, userId) {
    const chapter = await db.findById('game_chapters', chapterId);
    if (!chapter) {
      return { success: false, message: 'Chapter not found', statusCode: 404 };
    }

    const progress = await this.getProgress(userId);
    const levels = await db.findMany('game_levels', { chapter_id: parseInt(chapterId) });
    // Sort levels
    levels.sort((a, b) => a.order - b.order);

    const enrichedLevels = await Promise.all(levels.map(async (level) => ({
      ...level,
      is_completed: progress.data.completed_levels.includes(level.id),
      is_locked: !this.canPlayLevel(level, progress.data),
      player_best_score: await this.getBestScore(level.id, userId)
    })));

    return {
      success: true,
      data: {
        ...chapter,
        levels: enrichedLevels,
        is_unlocked: progress.data.unlocked_chapters.includes(chapter.id)
      }
    };
  }

  /**
   * Mở khóa chapter
   */
  async unlockChapter(chapterId, userId) {
    const chapter = await db.findById('game_chapters', chapterId);
    if (!chapter) {
      return { success: false, message: 'Chapter not found', statusCode: 404 };
    }

    const progress = await db.findOne('game_progress', { user_id: userId });

    if (progress.unlocked_chapters.includes(parseInt(chapterId))) {
      return { success: false, message: 'Chapter already unlocked', statusCode: 400 };
    }

    if (!this.canUnlockChapter(chapter, progress)) {
      return {
        success: false,
        message: `Need ${chapter.required_petals} sen petals to unlock`,
        statusCode: 400
      };
    }

    // Mở khóa chapter
    await db.update('game_progress', progress.id, {
      unlocked_chapters: [...progress.unlocked_chapters, parseInt(chapterId)],
      current_chapter: parseInt(chapterId)
    });

    return {
      success: true,
      message: 'Chapter unlocked successfully',
      data: { chapter_id: parseInt(chapterId), chapter_name: chapter.name }
    };
  }

  // ==================== LEVELS ====================

  /**
 * Lấy danh sách levels trong chapter
 */
  async getLevels(chapterId, userId) {
    const progress = await this.getProgress(userId);
    const levels = await db.findMany('game_levels', { chapter_id: parseInt(chapterId) });
    // Sort levels
    levels.sort((a, b) => a.order - b.order);

    const enriched = levels.map(level => ({
      id: level.id,
      name: level.name,
      type: level.type,
      difficulty: level.difficulty,
      order: level.order,
      thumbnail: level.thumbnail,
      is_completed: progress.data.completed_levels.includes(level.id),
      is_locked: !this.canPlayLevel(level, progress.data),
      rewards: level.rewards,
      required_level: level.required_level
    }));

    return { success: true, data: enriched };
  }

  /**
   * Kiểm tra có thể chơi level không
   */
  canPlayLevel(level, progress) {
    // Level đầu luôn chơi được
    if (level.order === 1) return true;
    if (level.required_level) {
      return progress.completed_levels.includes(level.required_level);
    }

    return true;
  }

  /**
   * Lấy best score của level
   */
  async getBestScore(levelId, userId) {
    const sessions = await db.findMany('game_sessions', {
      level_id: levelId,
      user_id: userId,
      status: 'completed'
    });

    if (sessions.length === 0) return null;

    return Math.max(...sessions.map(s => s.score || 0));
  }

  /**
   * Chi tiết level (màn chơi)
   */
  async getLevelDetail(levelId, userId) {
    const level = await db.findById('game_levels', levelId);
    if (!level) {
      return { success: false, message: 'Level not found', statusCode: 404 };
    }

    const progress = await this.getProgress(userId);

    if (!this.canPlayLevel(level, progress.data)) {
      return { success: false, message: 'Level is locked', statusCode: 403 };
    }

    const playCountData = await db.findMany('game_sessions', {
      level_id: level.id,
      user_id: userId
    });

    return {
      success: true,
      data: {
        ...level,
        is_completed: progress.data.completed_levels.includes(level.id),
        best_score: await this.getBestScore(level.id, userId),
        play_count: playCountData.length
      }
    };
  }

  // ==================== SCREEN-BASED GAMEPLAY ====================

  /**
 * Bắt đầu chơi level
 */
  async startLevel(levelId, userId) {

    // MISSING: Check for existing expired sessions
    const existingSessions = await db.findMany('game_sessions', {
      level_id: levelId,
      user_id: userId,
      status: 'in_progress'
    });

    // CRITICAL: Expire old sessions before creating new
    for (const session of existingSessions) {
      const lastActivity = new Date(session.last_activity || session.started_at).getTime();
      const now = Date.now();
      if (now - lastActivity > 24 * 60 * 60 * 1000) {
        await db.update('game_sessions', session.id, {
          status: 'expired',
          expired_at: new Date().toISOString(),
          expired_reason: 'Auto-expired before new session'
        });
      }
    }

    const level = await db.findById('game_levels', levelId);
    if (!level) {
      return { success: false, message: 'Level not found', statusCode: 404 };
    }

    const progress = await db.findOne('game_progress', { user_id: userId });
    if (!this.canPlayLevel(level, progress)) {
      return { success: false, message: 'Level is locked', statusCode: 403 };
    }

    // Validate screens structure
    if (!level.screens || level.screens.length === 0) {
      return { success: false, message: 'Level has no screens configured', statusCode: 500 };
    }

    const validation = this.validateScreensStructure(level.screens);
    if (!validation.success) {
      return validation;
    }

    const session = await db.create('game_sessions', {
      user_id: userId,
      level_id: levelId,
      status: 'in_progress',
      current_screen_id: level.screens[0].id,
      current_screen_index: 0,
      collected_items: [],
      answered_questions: [],
      timeline_order: [],
      score: 0,
      total_screens: level.screens.length,
      completed_screens: [],
      screen_states: {},
      time_spent: 0,
      hints_used: 0,
      started_at: new Date().toISOString(),
      last_activity: new Date().toISOString()
    });

    const firstScreen = this.enrichScreen(level.screens[0], session, 0, level.screens.length);

    // Fetch AI character if exists
    let aiCharacter = null;
    if (level.ai_character_id) {
      aiCharacter = await db.findById('game_characters', level.ai_character_id);
    }

    return {
      success: true,
      message: 'Level started',
      data: {
        session_id: session.id,
        level: {
          id: level.id,
          name: level.name,
          description: level.description,
          total_screens: level.screens.length,
          ai_character: aiCharacter
        },
        current_screen: firstScreen
      }
    };
  }

  /**
 * Thu thập manh mối
 */
  async collectClue(levelId, userId, clueId) {
    const session = await this.getActiveSession(levelId, userId);

    if (!session) {
      return { success: false, message: 'No active session or session expired', statusCode: 404 };
    }

    const level = await db.findById('game_levels', levelId);
    const currentScreen = level.screens[session.current_screen_index];

    if (currentScreen.type !== 'HIDDEN_OBJECT') {
      return { success: false, message: 'Not a hidden object screen', statusCode: 400 };
    }

    const item = currentScreen.items?.find(i => i.id === clueId);
    if (!item) {
      return { success: false, message: 'Item not found', statusCode: 404 };
    }

    if (session.collected_items.includes(clueId)) {
      return { success: false, message: 'Item already collected', statusCode: 400 };
    }

    const updatedSession = await db.update('game_sessions', session.id, {
      collected_items: [...session.collected_items, clueId],
      score: session.score + (item.points || 10),
      last_activity: new Date().toISOString() // UPDATE LAST ACTIVITY
    });

    const requiredItems = currentScreen.required_items || currentScreen.items.length;
    const allCollected = updatedSession.collected_items.length >= requiredItems;

    return {
      success: true,
      message: 'Item collected',
      data: {
        item,
        points_earned: item.points || 10,
        total_score: updatedSession.score,
        progress: {
          collected: updatedSession.collected_items.length,
          required: requiredItems,
          all_collected: allCollected
        }
      }
    };
  }

  /**
   * Submit answer for QUIZ screen
   */
  async submitAnswer(sessionId, userId, answerId) {
    const session = await db.findOne('game_sessions', {
      id: parseInt(sessionId),
      user_id: userId,
      status: 'in_progress'
    });

    if (!session) {
      return { success: false, message: 'Session not found', statusCode: 404 };
    }

    // Check timeout
    const SESSION_TIMEOUT = 24 * 60 * 60 * 1000;
    const lastActivity = new Date(session.last_activity || session.started_at).getTime();
    if (Date.now() - lastActivity > SESSION_TIMEOUT) {
      await db.update('game_sessions', session.id, {
        status: 'expired',
        expired_at: new Date().toISOString()
      });
      return { success: false, message: 'Session expired', statusCode: 404 };
    }

    const level = await db.findById('game_levels', session.level_id);
    const currentScreen = level.screens[session.current_screen_index];

    if (currentScreen.type !== 'QUIZ') {
      return { success: false, message: 'Current screen is not a quiz', statusCode: 400 };
    }

    const hasAnswered = session.answered_questions.some(
      q => q.screen_id === currentScreen.id
    );

    if (hasAnswered) {
      return { success: false, message: 'Already answered this question', statusCode: 400 };
    }

    const selectedOption = currentScreen.options?.find(o => o.text === answerId);
    if (!selectedOption) {
      return { success: false, message: 'Invalid answer', statusCode: 400 };
    }

    const isCorrect = selectedOption.is_correct;
    const pointsEarned = isCorrect ? (currentScreen.reward?.points || 20) : 0;

    const updatedSession = await db.update('game_sessions', sessionId, {
      answered_questions: [
        ...session.answered_questions,
        {
          screen_id: currentScreen.id,
          answer: answerId,
          is_correct: isCorrect,
          points: pointsEarned,
          answered_at: new Date().toISOString()
        }
      ],
      score: session.score + pointsEarned,
      last_activity: new Date().toISOString() // UPDATE LAST ACTIVITY
    });

    return {
      success: true,
      message: isCorrect ? 'Correct answer!' : 'Wrong answer',
      data: {
        is_correct: isCorrect,
        points_earned: pointsEarned,
        total_score: updatedSession.score,
        explanation: selectedOption.explanation,
        correct_answer: isCorrect ? null : currentScreen.options.find(o => o.is_correct)?.text
      }
    };
  }

  async submitTimelineOrder(sessionId, userId, eventOrder) {
    const session = await db.findOne('game_sessions', {
      id: parseInt(sessionId),
      user_id: userId,
      status: 'in_progress'
    });

    if (!session) {
      return {
        success: false,
        message: 'Session not found or expired',
        statusCode: 404
      };
    }

    // CHECK SESSION TIMEOUT
    const SESSION_TIMEOUT = 24 * 60 * 60 * 1000;
    const lastActivity = new Date(session.last_activity || session.started_at).getTime();
    if (Date.now() - lastActivity > SESSION_TIMEOUT) {
      await db.update('game_sessions', session.id, {
        status: 'expired',
        expired_at: new Date().toISOString()
      });
      return {
        success: false,
        message: 'Session expired',
        statusCode: 404
      };
    }

    const level = await db.findById('game_levels', session.level_id);
    const currentScreen = level.screens[session.current_screen_index];

    // CHECK SCREEN TYPE
    if (currentScreen.type !== 'TIMELINE') {
      return {
        success: false,
        message: 'Current screen is not a timeline',
        statusCode: 400
      };
    }

    // GET CORRECT ORDER
    const correctOrder = currentScreen.events
      .sort((a, b) => a.year - b.year)
      .map(e => e.id);

    // VALIDATE ARRAY LENGTH
    if (eventOrder.length !== correctOrder.length) {
      return {
        success: false,
        message: `Timeline must have exactly ${correctOrder.length} events`,
        statusCode: 400,
        data: { required: correctOrder.length, received: eventOrder.length }
      };
    }

    // VALIDATE EVENT IDs
    const validEventIds = new Set(correctOrder);
    const hasInvalidIds = eventOrder.some(id => !validEventIds.has(id));

    if (hasInvalidIds) {
      return {
        success: false,
        message: 'Invalid event IDs in timeline order',
        statusCode: 400
      };
    }

    // CHECK CORRECT ORDER
    const isCorrect = JSON.stringify(eventOrder) === JSON.stringify(correctOrder);

    // SAVE ORDER (even if wrong for retry)
    await db.update('game_sessions', session.id, {
      timeline_order: eventOrder,
      last_activity: new Date().toISOString()
    });

    if (!isCorrect) {
      return {
        success: false,
        message: 'Timeline order is incorrect. Please try again.',
        statusCode: 400,
        data: {
          isCorrect: false,
          hint: 'Check the years of each event carefully'
          // ❌ DON'T reveal correctOrder in production
        }
      };
    }

    // ADD POINTS IF CORRECT
    const pointsEarned = currentScreen.reward?.points || 20;
    await db.update('game_sessions', session.id, {
      score: session.score + pointsEarned
    });

    return {
      success: true,
      message: 'Timeline order is correct!',
      data: {
        isCorrect: true,
        pointsEarned,
        totalScore: session.score + pointsEarned
      }
    };
  }

  /**
   * Navigate to next screen in level
   */

  async navigateToNextScreen(sessionId, userId) {
    const session = await db.findOne('game_sessions', {
      id: parseInt(sessionId),
      user_id: userId,
      status: 'in_progress'
    });

    if (!session) {
      return {
        success: false,
        message: 'Session not found or expired',
        statusCode: 404
      };
    }

    // CHECK SESSION TIMEOUT
    const SESSION_TIMEOUT = 24 * 60 * 60 * 1000;
    const lastActivity = new Date(session.last_activity || session.started_at).getTime();
    if (Date.now() - lastActivity > SESSION_TIMEOUT) {
      await db.update('game_sessions', session.id, {
        status: 'expired',
        expired_at: new Date().toISOString()
      });
      return {
        success: false,
        message: 'Session expired',
        statusCode: 404
      };
    }

    const level = await db.findById('game_levels', session.level_id);
    const currentScreen = level.screens[session.current_screen_index];

    // Validate screen completion - Check if can proceed (completed current screen requirements)
    const canProceed = this.validateScreenCompletion(currentScreen, session);
    if (!canProceed.success) {
      return canProceed;
    }

    // Find next screen
    let nextScreenIndex = session.current_screen_index + 1;

    // Check if has custom next_screen_id
    if (currentScreen.next_screen_id) {
      nextScreenIndex = level.screens.findIndex(s => s.id === currentScreen.next_screen_id);
      if (nextScreenIndex === -1) {
        return {
          success: false,
          message: 'Invalid next_screen_id configuration',
          statusCode: 500
        };
      }
    }

    // Check if level finished
    if (nextScreenIndex >= level.screens.length) {
      // Auto complete level
      return {
        success: false,
        message: 'Level completed. Please call completeLevel endpoint.',
        statusCode: 400,
        data: {
          level_finished: true,
          final_score: session.score
        }
      };
    }

    const nextScreen = level.screens[nextScreenIndex];

    // Update session
    const updatedSession = await db.update('game_sessions', session.id, {
      current_screen_id: nextScreen.id,
      current_screen_index: nextScreenIndex,
      completed_screens: [...session.completed_screens, currentScreen.id],
      last_activity: new Date().toISOString() // ⚡ UPDATE LAST ACTIVITY
    });

    return {
      success: true,
      message: 'Navigated to next screen',
      data: {
        session_id: session.id,
        current_screen: this.enrichScreen(
          nextScreen,
          updatedSession,
          nextScreenIndex,
          level.screens.length
        ),
        progress: {
          completed_screens: updatedSession.completed_screens.length,
          total_screens: level.screens.length,
          percentage: Math.round(
            (updatedSession.completed_screens.length / level.screens.length) * 100
          )
        }
      }
    };
  }

  /**
   * Validate if current screen is completed
   */
  validateScreenCompletion(screen, session) {
    switch (screen.type) {
      case 'HIDDEN_OBJECT':
        const requiredItems = screen.required_items || screen.items?.length || 0;
        const collectedCount = session.collected_items.filter(
          item => screen.items?.some(i => i.id === item)
        ).length;

        if (collectedCount < requiredItems) {
          return {
            success: false,
            message: `Need to collect ${requiredItems - collectedCount} more items`,
            statusCode: 400
          };
        }
        break;

      case 'QUIZ':
        const hasAnswered = session.answered_questions.some(
          q => q.screen_id === screen.id
        );
        if (!hasAnswered) {
          return {
            success: false,
            message: 'Must answer the question first',
            statusCode: 400
          };
        }
        break;

      case 'DIALOGUE':
        if (!screen.skip_allowed && !screen.auto_advance) {
          const screenState = session.screen_states?.[screen.id];
          if (!screenState?.read) {
            return {
              success: false,
              message: 'Must read the dialogue first',
              statusCode: 400
            };
          }
        }
        break;

      case 'TIMELINE':

        const userOrder = session.timeline_order;

        if (!userOrder || userOrder.length === 0) {
          return {
            success: false,
            message: 'Must submit timeline order first',
            statusCode: 400,
            data: {
              hint: 'Use POST /sessions/:id/submit-timeline to arrange events'
            }
          };
        }

        // CHECK IF ORDER IS CORRECT (already validated in submit)
        const correctOrder = screen.events
          .sort((a, b) => a.year - b.year)
          .map(e => e.id);

        const isCorrect = JSON.stringify(userOrder) === JSON.stringify(correctOrder);

        if (!isCorrect) {
          return {
            success: false,
            message: 'Timeline order is incorrect. Please try again.',
            statusCode: 400,
            data: {
              userOrder,
              correctOrder, // Show for debugging (remove in production)
              hint: 'Check the years of each event carefully'
            }
          };
        }
        break;

      case 'VIDEO':
      case 'IMAGE_VIEWER':
        // ✅ These screens auto-complete when viewed
        break;
    }

    return { success: true };
  }

  async completeLevel(levelId, userId, { score, timeSpent } = {}) {


    const session = await db.findOne('game_sessions', {
      level_id: levelId,
      user_id: userId,
      status: 'in_progress'
    });

    if (!session) {
      return { success: false, message: 'No active session', statusCode: 404 };
    }

    const level = await db.findById('game_levels', levelId);
    const progress = await db.findOne('game_progress', { user_id: userId });

    // ✅ CHECK IF ALREADY COMPLETED
    const alreadyCompleted = progress.completed_levels.includes(levelId);

    if (alreadyCompleted) {
      // Update session as completed but NO rewards
      await db.update('game_sessions', session.id, {
        status: 'completed',
        completed_at: new Date().toISOString()
      });

      return {
        success: true,
        message: 'Level completed (no rewards for replay)',
        data: {
          passed: true,
          score: score || session.score,
          alreadyCompleted: true,
          rewardsGiven: false,
          note: 'You already completed this level. No additional rewards.'
        }
      };
    }

    // ✅ FIRST TIME COMPLETION - GIVE REWARDS
    const timeBonus = this.calculateTimeBonus(timeSpent || session.time_spent, level.time_limit);
    const hintPenalty = session.hints_used * 5;
    const finalScore = Math.max(0, (score || session.score) + timeBonus - hintPenalty);
    const passed = finalScore >= (level.passing_score || 70);

    // Cập nhật session
    await db.update('game_sessions', session.id, {
      status: 'completed',
      score: finalScore,
      completed_at: new Date().toISOString()
    });

    if (!passed) {
      return {
        success: true,
        message: 'Level completed but not passed',
        data: {
          passed: false,
          score: finalScore,
          required_score: level.passing_score || 70,
          can_retry: true
        }
      };
    }

    // ✅ GIVE REWARDS (First time only)
    const rewards = level.rewards || {};
    const newPetals = progress.total_sen_petals + (rewards.petals || 1);
    const newCoins = progress.coins + (rewards.coins || 50);
    const newCompleted = [...progress.completed_levels, levelId];

    let newCharacters = [...progress.collected_characters];
    if (rewards.character && !newCharacters.includes(rewards.character)) {
      newCharacters.push(rewards.character);
    }

    const sessionBackup = { ...session };
    const progressBackup = { ...progress };


    try {
      await db.update('game_sessions', session.id, { status: 'completed' });
      await db.update('game_progress', progress.id, {
        completed_levels: newCompleted,
        total_sen_petals: newPetals,
        total_points: progress.total_points + finalScore,
        coins: newCoins,
        collected_characters: newCharacters
      });

      return {
        success: true,
        message: 'Level completed successfully!',
        data: {
          passed: true,
          score: finalScore,
          rewards: {
            petals: rewards.petals || 1,
            coins: rewards.coins || 50,
            character: rewards.character || null
          },
          new_totals: {
            petals: newPetals,
            points: progress.total_points + finalScore,
            coins: newCoins
          }
        }
      };
    } catch (error) {
      // Rollback
      await db.update('game_sessions', session.id, sessionBackup);
      await db.update('game_progress', progress.id, progressBackup);
      throw error;
    }
  }

  calculateTimeBonus(timeSpent, timeLimit) {
    if (!timeLimit) return 0;
    const remaining = timeLimit - timeSpent;
    return remaining > 0 ? Math.floor(remaining / 10) : 0;
  }

  // ==================== VALIDATION ====================

  validateScreensStructure(screens) {
    if (!Array.isArray(screens) || screens.length === 0) {
      return {
        success: false,
        message: 'Screens must be a non-empty array',
        statusCode: 400
      };
    }

    const errors = [];
    const screenIds = new Set();

    screens.forEach((screen, index) => {
      if (!screen.id) {
        errors.push(`Screen ${index}: Missing id`);
      } else if (screenIds.has(screen.id)) {
        errors.push(`Screen ${index}: Duplicate id '${screen.id}'`);
      } else {
        screenIds.add(screen.id);
      }

      if (!screen.type) {
        errors.push(`Screen ${index}: Missing type`);
      }
    });

    if (errors.length > 0) {
      return { success: false, message: 'Invalid screens structure', errors };
    }

    return { success: true };
  }

  enrichScreen(screen, session, index, totalScreens) {
    return {
      ...screen,
      index,
      is_first: index === 0,
      is_last: index === totalScreens - 1,
      is_completed: session.completed_screens.includes(screen.id),
      state: session.screen_states?.[screen.id] || {}
    };
  }

  // ==================== MUSEUM ====================

  async getMuseum(userId) {
    const progress = await this.getProgress(userId);
    const lastCollection = progress.data.last_museum_collection || progress.data.created_at;

    // Tính thu nhập tích lũy (read-only, không modify DB)
    const incomeInfo = this.calculatePendingIncome(progress.data, lastCollection);

    return {
      success: true,
      data: {
        is_open: progress.data.museum_open,
        income_per_hour: incomeInfo.rate,
        total_income_generated: progress.data.museum_income || 0,
        pending_income: incomeInfo.pending,
        hours_accumulated: incomeInfo.hours_accumulated,
        capped: incomeInfo.capped || false,
        characters: progress.data.collected_characters,
        visitor_count: progress.data.collected_characters.length * 10,
        can_collect: incomeInfo.pending > 0,
        next_collection_in: this.getNextCollectionTime(incomeInfo.rate),

        // ✅ WARNING MESSAGE
        ...(incomeInfo.capped && {
          cap_notice: `Income capped at ${incomeInfo.pending} coins. Please collect regularly to maximize earnings!`
        })
      }
    };
  }

  /**
   * Tính toán thu nhập đang chờ
   */
  calculatePendingIncome(progressData, lastCollectionTime) {
    if (!progressData.museum_open || progressData.collected_characters.length === 0) {
      return { rate: 0, pending: 0, hours_accumulated: 0, capped: false };
    }

    const ratePerHour = progressData.collected_characters.length * 5; // 5 coins/character/hour
    const now = new Date();
    const last = new Date(lastCollectionTime);
    const diffHours = Math.abs(now - last) / 36e5;

    // Cap hours to 24 (encourage daily login)
    const cappedHours = Math.min(diffHours, 24);

    // ✅ ADD HARD CAP FOR PENDING INCOME
    const MAX_PENDING_INCOME = 5000; // Hard economy cap
    const rawPending = Math.floor(ratePerHour * cappedHours);
    const pending = Math.min(rawPending, MAX_PENDING_INCOME);

    // ✅ LOG WARNING IF HIT CAP
    const hitCap = rawPending > MAX_PENDING_INCOME;
    if (hitCap) {
      console.log(`⚠️ User ${progressData.user_id} hit max pending income cap (${rawPending} → ${MAX_PENDING_INCOME})`);
    }

    return {
      rate: ratePerHour,
      pending: pending,
      hours_accumulated: cappedHours.toFixed(1),
      capped: hitCap,
      would_be_without_cap: hitCap ? rawPending : null // For transparency
    };
  }

  /**
   * Mở/đóng bảo tàng
   */
  async toggleMuseum(userId, isOpen) {
    const progress = await db.findOne('game_progress', { user_id: userId });

    await db.update('game_progress', progress.id, {
      museum_open: isOpen
    });

    return {
      success: true,
      message: `Museum ${isOpen ? 'opened' : 'closed'}`,
      data: {
        is_open: isOpen,
        income_per_hour: this.calculateMuseumIncome(progress)
      }
    };
  }

  /**
   * Thu hoạch tiền từ bảo tàng (WITH LOCK MECHANISM)
   */
  async collectMuseumIncome(userId) {
    // === STEP 1: CHECK LOCK ===
    const lockKey = `museum_collect_${userId}`;

    // Nếu đang có request collect khác, reject ngay
    if (this.activeLocks.has(lockKey)) {
      return {
        success: false,
        message: 'Income collection already in progress. Please wait.',
        statusCode: 429 // Too Many Requests
      };
    }

    // === STEP 2: ACQUIRE LOCK ===
    this.activeLocks.add(lockKey);
    console.log(`🔒 Lock acquired for user ${userId} museum collection`);

    try {
      // === STEP 3: BUSINESS LOGIC (TRONG TRY BLOCK) ===

      const progress = await db.findOne('game_progress', { user_id: userId });

      if (!progress) {
        return {
          success: false,
          message: 'User progress not found',
          statusCode: 404
        };
      }

      if (!progress.museum_open) {
        return {
          success: false,
          message: 'Museum is closed',
          statusCode: 400
        };
      }

      const lastCollection = progress.last_museum_collection || progress.created_at;
      const incomeInfo = this.calculatePendingIncome(progress, lastCollection);

      if (incomeInfo.pending <= 0) {
        return {
          success: false,
          message: 'No income to collect yet',
          statusCode: 400
        };
      }

      // === CRITICAL SECTION: UPDATE DB ===
      const newCoins = (progress.coins || 0) + incomeInfo.pending;
      const newTotalMuseumIncome = (progress.museum_income || 0) + incomeInfo.pending;

      // Single atomic update để tránh partial updates
      const updatedProgress = await db.update('game_progress', progress.id, {
        coins: newCoins,
        museum_income: newTotalMuseumIncome,
        last_museum_collection: new Date().toISOString()
      });

      console.log(`✅ User ${userId} collected ${incomeInfo.pending} coins from museum`);

      return {
        success: true,
        message: `Collected ${incomeInfo.pending} coins from Museum!`,
        data: {
          collected: incomeInfo.pending,
          total_coins: newCoins,
          total_museum_income: newTotalMuseumIncome,
          next_collection_in: this.getNextCollectionTime(incomeInfo.rate)
        }
      };

    } catch (error) {
      // === STEP 4: ERROR HANDLING ===
      console.error(`❌ Museum collection error for user ${userId}:`, error);

      return {
        success: false,
        message: 'Failed to collect income. Please try again.',
        statusCode: 500
      };

    } finally {
      // === STEP 5: RELEASE LOCK (ALWAYS) ===
      this.activeLocks.delete(lockKey);
      console.log(`🔓 Lock released for user ${userId} museum collection`);
    }
  }

  /**
   * Helper: Tính thời gian có thể collect tiếp theo
   */
  getNextCollectionTime(ratePerHour) {
    if (ratePerHour === 0) return 'Museum has no income';

    const minutesToNextCoin = Math.ceil(60 / ratePerHour);
    return `${minutesToNextCoin} minutes`;
  }


  // ==================== SCAN ====================



  /**
   * Scan object tại di tích
   */
  async scanObject(userId, code, location) {
    const artifact = await db.findOne('scan_objects', { code: code.toUpperCase() });

    if (!artifact) {
      return { success: false, message: 'Invalid scan code', statusCode: 404 };
    }

    // ✅ CHECK DUPLICATE SCAN - Prevent farming
    const existingScan = await db.findOne('scan_history', {
      user_id: userId,
      object_id: artifact.id
    });

    if (existingScan) {
      return {
        success: false,
        message: 'You have already scanned this object',
        statusCode: 400,
        data: {
          scanned_at: existingScan.scanned_at,
          artifact: artifact
        }
      };
    }

    // Kiểm tra vị trí nếu có
    if (artifact.latitude && location.latitude) {
      const distance = calculateDistance(
        location.latitude,
        location.longitude,
        artifact.latitude,
        artifact.longitude
      );

      if (distance > 0.5) {
        return { success: false, message: 'You are too far from the location', statusCode: 400 };
      }
    }

    const progress = await db.findOne('game_progress', { user_id: userId });

    const reward = {
      coins: artifact.reward_coins || 100,
      petals: artifact.reward_petals || 1,
      character: artifact.reward_character || null
    };

    let newCharacters = [...progress.collected_characters];
    if (reward.character && !newCharacters.includes(reward.character)) {
      newCharacters.push(reward.character);
    }

    await db.update('game_progress', progress.id, {
      coins: progress.coins + reward.coins,
      total_sen_petals: progress.total_sen_petals + reward.petals,
      collected_characters: newCharacters
    });

    // Lưu scan history
    await db.create('scan_history', {
      user_id: userId,
      object_id: artifact.id,
      location: location,
      scanned_at: new Date().toISOString()
    });

    return {
      success: true,
      message: 'Scan successful!',
      data: { artifact, rewards: reward }
    };
  }


  // ==================== BADGES & ACHIEVEMENTS ====================

  /**
   * Lấy badges
   */
  async getBadges(userId) {
    const progress = await this.getProgress(userId);
    const allBadges = await db.findAll('game_badges');

    const enriched = allBadges.map(badge => ({
      ...badge,
      is_unlocked: progress.data.badges.includes(badge.id)
    }));

    return { success: true, data: enriched };
  }

  async getAchievements(userId) {
    const progress = await this.getProgress(userId);
    const allAchievements = await db.findAll('game_achievements');

    const enriched = allAchievements.map(achievement => ({
      ...achievement,
      is_completed: progress.data.achievements.includes(achievement.id)
    }));

    return { success: true, data: enriched };
  }

  // ==================== LEADERBOARD ====================

  /**
 * Bảng xếp hạng
 */
  async getLeaderboard(type = 'global', limit = 20) {
    // Optimized: Use findAllAdvanced directly with sort
    const result = await db.findAllAdvanced('game_progress', {
      sort: 'total_points',
      order: 'desc',
      limit: limit,
      page: 1
    });

    const leaderboard = await Promise.all(result.data.map(async (prog, index) => {
      const user = await db.findById('users', prog.user_id);
      return {
        rank: index + 1,
        user_id: prog.user_id,
        user_name: user?.name || 'Unknown',
        user_avatar: user?.avatar,
        total_points: prog.total_points,
        level: prog.level,
        sen_petals: prog.total_sen_petals,
        characters_count: prog.collected_characters?.length || 0
      };
    }));

    return { success: true, data: leaderboard };
  }

  /**
   * Phần thưởng hàng ngày
   */
  async getDailyReward(userId) {
    let progress = await db.findOne('game_progress', { user_id: userId });

    // Fix: Auto-initialize if not exists
    if (!progress) {
      progress = await this.initializeProgress(userId);
    }

    const today = new Date().toISOString().split('T')[0];
    const lastLogin = new Date(progress.last_login).toISOString().split('T')[0];

    // Note: If newly initialized, last_login is 'today', so this correct logic will return "already claimed"
    // which effectively prevents claiming on the very first day (Registration Day).
    if (today === lastLogin) {
      return { success: false, message: 'Daily reward already claimed', statusCode: 400 };
    }

    const reward = { coins: 50, petals: 1 };

    await db.update('game_progress', progress.id, {
      coins: progress.coins + reward.coins,
      total_sen_petals: progress.total_sen_petals + reward.petals,
      last_login: new Date().toISOString()
    });

    return {
      success: true,
      message: 'Daily reward claimed',
      data: reward
    };
  }

  // ==================== SHOP & INVENTORY ====================

  /**
   * Mua item trong shop
   */
  async purchaseItem(userId, itemId, quantity) {
    const item = await db.findById('shop_items', itemId);
    if (!item) {
      return { success: false, message: 'Item not found', statusCode: 404 };
    }

    const progress = await db.findOne('game_progress', { user_id: userId });
    const totalCost = item.price * quantity;

    if (progress.coins < totalCost) {
      return { success: false, message: 'Not enough coins', statusCode: 400 };
    }

    // ✅ TRANSACTION SAFETY: Backup state for rollback
    const originalCoins = progress.coins;
    let inventoryBackup = null;

    try {
      // Step 1: Deduct coins
      await db.update('game_progress', progress.id, {
        coins: progress.coins - totalCost
      });

      // Step 2: Update inventory
      let inventory = await db.findOne('user_inventory', { user_id: userId });
      if (!inventory) {
        inventory = await db.create('user_inventory', { user_id: userId, items: [] });
      }

      // Backup inventory state
      inventoryBackup = { ...inventory, items: [...inventory.items] };

      const existingItem = inventory.items.find(i => i.item_id === itemId);
      if (existingItem) {
        existingItem.quantity += quantity;
      } else {
        inventory.items.push({
          item_id: itemId,
          quantity: quantity,
          acquired_at: new Date().toISOString()
        });
      }

      await db.update('user_inventory', inventory.id, { items: inventory.items });

      // ✅ SUCCESS
      return {
        success: true,
        message: 'Purchase successful',
        data: {
          item,
          quantity,
          total_cost: totalCost,
          remaining_coins: progress.coins - totalCost
        }
      };

    } catch (error) {
      // ✅ ROLLBACK on error
      console.error('❌ Purchase failed, rolling back:', error);

      // Restore coins
      await db.update('game_progress', progress.id, {
        coins: originalCoins
      });

      // Restore inventory if it was modified
      if (inventoryBackup) {
        await db.update('user_inventory', inventoryBackup.id, {
          items: inventoryBackup.items
        });
      }

      return {
        success: false,
        message: 'Purchase failed. Your coins have been refunded.',
        statusCode: 500
      };
    }
  }

  /**
   * Lấy inventory
   */
  async getInventory(userId) {
    const inventory = await db.findOne('user_inventory', { user_id: userId });

    if (!inventory) {
      return { success: true, data: { items: [] } };
    }

    const enriched = await Promise.all(inventory.items.map(async (item) => {
      const itemData = await db.findById('shop_items', item.item_id);
      return { ...item, ...itemData };
    }));

    return { success: true, data: { items: enriched } };
  }

  /**
   * Sử dụng item
   */
  async useItem(userId, itemId, targetId) {
    const inventory = await db.findOne('user_inventory', { user_id: userId });

    if (!inventory) {
      return { success: false, message: 'No inventory found', statusCode: 404 };
    }

    const item = inventory.items.find(i => i.item_id === itemId);
    if (!item || item.quantity <= 0) {
      return { success: false, message: 'Item not found or quantity is 0', statusCode: 400 };
    }

    const itemData = await db.findById('shop_items', itemId);

    item.quantity -= 1;
    await db.update('user_inventory', inventory.id, { items: inventory.items });

    return {
      success: true,
      message: 'Item used successfully',
      data: { item: itemData, effect: 'Applied successfully' }
    };
  }
}

module.exports = new GameService();