/**
 * SEN API Endpoints Configuration
 * Auto-generated reference for all API endpoints
 * Base URL: http://localhost:3000/api
 */

const BASE_URL = process.env.API_URL || 'http://localhost:3000/api/';

/**
 * Authentication Endpoints
 */
const auth = {
  register: '/auth/register',
  login: '/auth/login',
  logout: '/auth/logout',
  getMe: '/auth/me',
  changePassword: '/auth/change-password'
};

/**
 * User Management Endpoints
 */
const users = {
  list: '/users',
  getById: (id) => `/users/${id}`,
  updateProfile: '/users/profile',
  getStats: '/users/stats/summary'
};

/**
 * Heritage Sites Endpoints
 */
const heritageSites = {
  list: '/heritage-sites',
  search: '/heritage-sites/search',
  nearby: '/heritage-sites/nearby',
  getById: (id) => `/heritage-sites/${id}`,
  getArtifacts: (id) => `/heritage-sites/${id}/artifacts`,
  getTimeline: (id) => `/heritage-sites/${id}/timeline`,
  create: '/heritage-sites',
  update: (id) => `/heritage-sites/${id}`,
  delete: (id) => `/heritage-sites/${id}`
};

/**
 * Artifacts Endpoints
 */
const artifacts = {
  list: '/artifacts',
  search: '/artifacts/search',
  getById: (id) => `/artifacts/${id}`,
  getRelated: (id) => `/artifacts/${id}/related`,
  create: '/artifacts',
  update: (id) => `/artifacts/${id}`,
  delete: (id) => `/artifacts/${id}`
};

/**
 * Cultural Categories Endpoints
 */
const categories = {
  list: '/categories',
  getById: (id) => `/categories/${id}`,
  create: '/categories',
  update: (id) => `/categories/${id}`,
  delete: (id) => `/categories/${id}`
};

/**
 * Game Endpoints
 */
const game = {
  // Progress
  getProgress: '/game/progress',

  // Chapters (Sen Flower Layers)
  getChapters: '/game/chapters',
  getChapterDetail: (id) => `/game/chapters/${id}`,
  unlockChapter: (id) => `/game/chapters/${id}/unlock`,

  // Levels
  getLevels: (chapterId) => `/game/levels/${chapterId}`,
  getLevelDetail: (id) => `/game/levels/${id}/detail`,
  startLevel: (id) => `/game/levels/${id}/start`,
  collectClue: (id) => `/game/levels/${id}/collect-clue`,
  completeLevel: (id) => `/game/levels/${id}/complete`,

  // Screen Navigation
  nextScreen: (sessionId) => `/game/sessions/${sessionId}/next-screen`,
  submitAnswer: (sessionId) => `/game/sessions/${sessionId}/submit-answer`,
  submitTimeline: (sessionId) => `/game/sessions/${sessionId}/submit-timeline`,

  // Museum
  getMuseum: '/game/museum',
  toggleMuseum: '/game/museum/toggle',
  collectIncome: '/game/museum/collect',

  // Badges & Achievements
  getBadges: '/game/badges',
  getAchievements: '/game/achievements',

  // Scan
  scanObject: '/game/scan',

  // Leaderboard
  getLeaderboard: '/game/leaderboard',
  getDailyReward: '/game/daily-reward',

  // Shop & Inventory
  purchaseItem: '/game/shop/purchase',
  getInventory: '/game/inventory',
  useItem: '/game/inventory/use'
};

/**
 * AI Endpoints
 */
const ai = {
  chat: '/ai/chat',
  getHistory: '/ai/history',
  askHint: '/ai/ask-hint',
  explain: '/ai/explain',
  generateQuiz: '/ai/quiz',
  clearHistory: '/ai/history'
};

/**
 * Learning Endpoints
 */
const learning = {
  list: '/learning',
  getById: (id) => `/learning/${id}`,
  getLearningPath: '/learning/path',
  complete: (id) => `/learning/${id}/complete`,
  create: '/learning',
  update: (id) => `/learning/${id}`,
  delete: (id) => `/learning/${id}`
};

/**
 * Quest Endpoints
 */
const quests = {
  list: '/quests',
  getAvailable: '/quests/available',
  getLeaderboard: '/quests/leaderboard',
  getById: (id) => `/quests/${id}`,
  complete: (id) => `/quests/${id}/complete`,
  create: '/quests',
  update: (id) => `/quests/${id}`,
  delete: (id) => `/quests/${id}`
};

/**
 * Collections Endpoints
 */
const collections = {
  list: '/collections',
  getById: (id) => `/collections/${id}`,
  create: '/collections',
  update: (id) => `/collections/${id}`,
  delete: (id) => `/collections/${id}`,
  addArtifact: (id, artifactId) => `/collections/${id}/artifacts/${artifactId}`,
  removeArtifact: (id, artifactId) => `/collections/${id}/artifacts/${artifactId}`
};

/**
 * Favorites Endpoints
 */
const favorites = {
  list: '/favorites',
  getByType: (type) => `/favorites/${type}`,
  getIds: (type) => `/favorites/${type}/ids`,
  getTrending: (type) => `/favorites/trending/${type}`,
  getStats: '/favorites/stats',
  check: (type, id) => `/favorites/${type}/${id}/check`,
  add: (type, id) => `/favorites/${type}/${id}`,
  toggle: (type, id) => `/favorites/${type}/${id}/toggle`,
  remove: (type, id) => `/favorites/${type}/${id}`,
  clearByType: (type) => `/favorites/${type}`,
  clearAll: '/favorites'
};

/**
 * Reviews Endpoints
 */
const reviews = {
  list: '/reviews',
  getByType: (type) => `/reviews/type/${type}`,
  create: '/reviews',
  update: (id) => `/reviews/${id}`,
  delete: (id) => `/reviews/${id}`
};

/**
 * Exhibitions Endpoints
 */
const exhibitions = {
  list: '/exhibitions',
  getActive: '/exhibitions/active',
  getById: (id) => `/exhibitions/${id}`,
  create: '/exhibitions',
  update: (id) => `/exhibitions/${id}`,
  delete: (id) => `/exhibitions/${id}`
};

/**
 * Upload Endpoints
 */
const upload = {
  uploadAvatar: '/upload/avatar',
  deleteFile: '/upload/file',
  getFileInfo: '/upload/file/info',
  getStats: '/upload/stats',
  cleanup: '/upload/cleanup'
};

/**
 * Admin CMS Endpoints
 */
const admin = {
  // Levels Management
  levels: {
    list: '/admin/levels',
    getById: (id) => `/admin/levels/${id}`,
    preview: (id) => `/admin/levels/${id}/preview`,
    templates: '/admin/levels/templates',
    validate: '/admin/levels/validate',
    create: '/admin/levels',
    update: (id) => `/admin/levels/${id}`,
    delete: (id) => `/admin/levels/${id}`,
    clone: (id) => `/admin/levels/${id}/clone`,
    bulkImport: '/admin/levels/bulk/import',
    reorder: (chapterId) => `/admin/levels/chapters/${chapterId}/reorder`,
    stats: '/admin/levels/stats'
  },

  // Chapters Management
  chapters: {
    list: '/admin/chapters',
    getById: (id) => `/admin/chapters/${id}`,
    create: '/admin/chapters',
    update: (id) => `/admin/chapters/${id}`,
    delete: (id) => `/admin/chapters/${id}`
  },

  // Characters Management
  characters: {
    list: '/admin/characters',
    getById: (id) => `/admin/characters/${id}`,
    create: '/admin/characters',
    update: (id) => `/admin/characters/${id}`,
    delete: (id) => `/admin/characters/${id}`
  },

  // Assets Management (Scan Objects)
  assets: {
    list: '/admin/assets',
    getById: (id) => `/admin/assets/${id}`,
    create: '/admin/assets',
    update: (id) => `/admin/assets/${id}`,
    delete: (id) => `/admin/assets/${id}`
  }
};

/**
 * Query Parameters Reference
 */
const queryParams = {
  pagination: {
    _page: 'Page number (default: 1)',
    _limit: 'Items per page (default: 10, max: 100)',
    page: 'Alternative to _page',
    limit: 'Alternative to _limit'
  },
  sorting: {
    _sort: 'Field to sort by',
    _order: 'Sort order: asc or desc (default: asc)',
    sort: 'Alternative to _sort',
    order: 'Alternative to _order'
  },
  filtering: {
    q: 'Full-text search',
    field_gte: 'Greater than or equal',
    field_lte: 'Less than or equal',
    field_ne: 'Not equal',
    field_like: 'Contains (case-insensitive)',
    field_in: 'In array of values'
  },
  relationships: {
    _embed: 'Embed related collections (comma-separated)',
    _expand: 'Expand foreign key references (comma-separated)'
  }
};

/**
 * Common Response Formats
 */
const responseFormats = {
  success: {
    simple: {
      success: true,
      message: 'Operation successful',
      data: {}
    },
    paginated: {
      success: true,
      count: 10,
      data: [],
      pagination: {
        page: 1,
        limit: 10,
        total: 100,
        totalPages: 10,
        hasNext: true,
        hasPrev: false
      }
    }
  },
  error: {
    notFound: {
      success: false,
      message: 'Resource not found',
      statusCode: 404
    },
    unauthorized: {
      success: false,
      message: 'Not authorized',
      statusCode: 401
    },
    validation: {
      success: false,
      message: 'Validation failed',
      errors: [
        { field: 'field_name', message: 'Error message' }
      ]
    }
  }
};

/**
 * HTTP Methods
 */
const methods = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  PATCH: 'PATCH',
  DELETE: 'DELETE'
};

/**
 * Status Codes
 */
const statusCodes = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE: 422,
  SERVER_ERROR: 500
};

/**
 * Authentication Headers
 */
const headers = {
  contentType: { 'Content-Type': 'application/json' },
  authorization: (token) => ({ 'Authorization': `Bearer ${token}` }),
  combined: (token) => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  })
};

/**
 * API Collections for Different Roles
 */
const byRole = {
  public: [
    heritageSites.list,
    artifacts.list,
    categories.list,
    exhibitions.list
  ],
  customer: [
    ...Object.values(auth),
    ...Object.values(game),
    ...Object.values(collections),
    ...Object.values(favorites),
    ...Object.values(reviews)
  ],
  researcher: [
    heritageSites.create,
    artifacts.create,
    exhibitions.create
  ],
  admin: [
    // All endpoints
  ]
};

/**
 * Common Query Examples
 */
const examples = {
  pagination: '?_page=1&_limit=10',
  sorting: '?_sort=rating&_order=desc',
  filtering: '?categoryId=1&year_gte=1000&year_lte=2000',
  search: '?q=hoang+thanh',
  combined: '?q=chua&_page=1&_limit=10&_sort=year',
  nearby: '?latitude=21.0285&longitude=105.8542&radius=5'
};

module.exports = {
  BASE_URL,
  auth,
  users,
  heritageSites,
  artifacts,
  categories,
  game,
  ai,
  learning,
  quests,
  collections,
  favorites,
  reviews,
  exhibitions,
  upload,
  admin,
  queryParams,
  responseFormats,
  methods,
  statusCodes,
  headers,
  byRole,
  examples
};