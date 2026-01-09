const express = require('express');
const cors = require('cors');
require('dotenv').config();
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 requests
  message: 'Too many login attempts, please try again later'
});


const app = express();

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));


// Middleware
const path = require('path');
const corsOptions = {
  origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : '*',
  credentials: process.env.CORS_CREDENTIALS === 'true' || false
};
app.use(cors(corsOptions));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve Static Files (Uploads)
app.use('/uploads', express.static(path.join(__dirname, 'database/uploads')));

// Logging
app.use(require('./middleware/logger.middleware'));

// Query parsing
const { parseQuery, formatResponse, validateQuery, logQuery } = require('./middleware/query.middleware');
app.use(parseQuery);
app.use(formatResponse);
app.use(validateQuery);
app.use(logQuery);

// Apply rate limiting BEFORE routes
app.use('/api/auth/login', authLimiter);
app.use('/api/auth/register', authLimiter);

// Import Routes
// Mount all routes
app.use('/api', require('./routes'));
app.use('/api/admin', require('./routes/admin'));

// API Documentation
app.get('/api', (req, res) => {
  res.json({
    name: 'SEN API - Cultural Heritage Game',
    version: '1.0.0',
    description: 'Backend API cho game giáo dục lịch sử văn hóa Việt Nam',
    documentation: 'https://github.com/your-repo/sen-backend',
    endpoints: {
      // Authentication
      auth: {
        base: '/api/auth',
        routes: [
          'POST /api/auth/register',
          'POST /api/auth/login',
          'GET /api/auth/me',
          'POST /api/auth/logout',
          'PUT /api/auth/change-password'
        ]
      },

      // Users
      users: {
        base: '/api/users',
        routes: [
          'GET /api/users',
          'GET /api/users/:id',
          'PUT /api/users/profile',
          'GET /api/users/stats/summary'
        ]
      },

      // Heritage & Culture
      heritage: {
        base: '/api/heritage-sites',
        routes: [
          'GET /api/heritage-sites',
          'GET /api/heritage-sites/search',
          'GET /api/heritage-sites/nearby',
          'GET /api/heritage-sites/:id',
          'GET /api/heritage-sites/:id/artifacts',
          'GET /api/heritage-sites/:id/timeline',
          'POST /api/heritage-sites (admin/researcher)',
          'PUT /api/heritage-sites/:id (admin/researcher)',
          'DELETE /api/heritage-sites/:id (admin)'
        ]
      },

      artifacts: {
        base: '/api/artifacts',
        routes: [
          'GET /api/artifacts',
          'GET /api/artifacts/search',
          'GET /api/artifacts/:id',
          'GET /api/artifacts/:id/related'
        ]
      },

      categories: {
        base: '/api/categories',
        routes: [
          'GET /api/categories',
          'GET /api/categories/:id'
        ]
      },

      exhibitions: {
        base: '/api/exhibitions',
        routes: [
          'GET /api/exhibitions',
          'GET /api/exhibitions/active',
          'GET /api/exhibitions/:id'
        ]
      },

      // Game System
      game: {
        base: '/api/game',
        routes: [
          'GET /api/game/progress',
          'GET /api/game/chapters',
          'GET /api/game/chapters/:id',
          'POST /api/game/chapters/:id/unlock',
          'GET /api/game/levels/:chapterId',
          'GET /api/game/levels/:id/detail',
          'POST /api/game/levels/:id/start',
          'POST /api/game/levels/:id/collect-clue',
          'POST /api/game/levels/:id/complete',
          'POST /api/game/sessions/:id/next-screen',
          'POST /api/game/sessions/:id/submit-answer',
          'GET /api/game/museum',
          'POST /api/game/museum/toggle',
          'POST /api/game/museum/collect',
          'GET /api/game/badges',
          'GET /api/game/achievements',
          'POST /api/game/scan',
          'GET /api/game/leaderboard',
          'GET /api/game/daily-reward',
          'POST /api/game/shop/purchase',
          'GET /api/game/inventory',
          'POST /api/game/inventory/use'
        ]
      },

      // AI System
      ai: {
        base: '/api/ai',
        routes: [
          'POST /api/ai/chat',
          'GET /api/ai/history',
          'POST /api/ai/ask-hint',
          'POST /api/ai/explain',
          'POST /api/ai/quiz',
          'DELETE /api/ai/history'
        ]
      },

      // Learning & Quests
      learning: {
        base: '/api/learning',
        routes: [
          'GET /api/learning',
          'GET /api/learning/path',
          'GET /api/learning/:id',
          'POST /api/learning/:id/complete'
        ]
      },

      quests: {
        base: '/api/quests',
        routes: [
          'GET /api/quests',
          'GET /api/quests/available',
          'GET /api/quests/leaderboard',
          'POST /api/quests/:id/complete'
        ]
      },

      // User Content
      collections: {
        base: '/api/collections',
        routes: [
          'GET /api/collections',
          'GET /api/collections/:id',
          'POST /api/collections',
          'PUT /api/collections/:id',
          'DELETE /api/collections/:id',
          'POST /api/collections/:id/artifacts/:artifactId',
          'DELETE /api/collections/:id/artifacts/:artifactId'
        ]
      },

      favorites: {
        base: '/api/favorites',
        routes: [
          'GET /api/favorites',
          'GET /api/favorites/:type',
          'GET /api/favorites/stats',
          'POST /api/favorites/:type/:id',
          'POST /api/favorites/:type/:id/toggle',
          'DELETE /api/favorites/:type/:id'
        ]
      },

      reviews: {
        base: '/api/reviews',
        routes: [
          'GET /api/reviews',
          'GET /api/reviews/type/:type',
          'POST /api/reviews',
          'PUT /api/reviews/:id',
          'DELETE /api/reviews/:id'
        ]
      },

      // Admin CMS
      admin: {
        base: '/api/admin',
        routes: [
          'Levels Management: /api/admin/levels',
          'Chapters Management: /api/admin/chapters',
          'Characters Management: /api/admin/characters',
          'Assets Management: /api/admin/assets'
        ]
      }
    },

    // Query parameters
    queryParams: {
      pagination: '?_page=1&_limit=10',
      sorting: '?_sort=name&_order=asc',
      filtering: '?field_gte=1000&field_lte=2000',
      search: '?q=search_term',
      nearby: '?latitude=21.0285&longitude=105.8542&radius=5'
    },

    // Response format
    responseFormat: {
      success: {
        success: true,
        message: 'Operation successful',
        data: {}
      },
      error: {
        success: false,
        message: 'Error message',
        statusCode: 400
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

    // Authentication
    authentication: {
      type: 'JWT Bearer Token',
      header: 'Authorization: Bearer <token>',
      testAccounts: {
        admin: 'admin@sen.com / 123456',
        researcher: 'tuanpham@sen.com / 123456',
        customer: 'huong.do@sen.com / 123456'
      }
    }
  });
});

// Health Check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'OK',
    message: 'SEN API is running',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || 'development'
  });
});

// ==================== ERROR HANDLING ====================

// 404 Handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: 'Route not found',
    path: req.path,
    method: req.method
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error('❌ Error:', {
    message: err.message,
    path: req.path,
    method: req.method
  });

  const statusCode = err.status || err.statusCode || 500;
  const response = {
    success: false,
    message: err.message || 'Internal Server Error',
    error: process.env.NODE_ENV === 'development' ? {
      type: err.name,
      stack: err.stack
    } : undefined
  };

  res.status(statusCode).json(response);
});

// ==================== SERVER START ====================

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════════════════════════════╗
║   🏛️ Sen Server Started!                                 ║
╠══════════════════════════════════════════════════════════════════╣
║   📍 URL: http://localhost:${PORT}                                  ║
║   🌍 Environment: ${process.env.NODE_ENV || 'development'}                                    ║
║   📊 API Docs: http://localhost:${PORT}/api                         ║
║   ❤️  Health: http://localhost:${PORT}/api/health                    ║
╚══════════════════════════════════════════════════════════════════╝
  `);
});

module.exports = app;