# 🎮 SEN Game System - Complete Guide (FIXED & UPDATED)

## 📋 Tổng quan

Backend game system đã được **HOÀN TOÀN TÁI CẤU TRÚC** với các cải tiến:

✅ **Screen-based gameplay** - Màn chơi theo từng màn hình tuần tự  
✅ **Session management** - Quản lý phiên chơi với auto-cleanup  
✅ **AI integration** - Chatbot với context-aware responses  
✅ **Museum system** - Bảo tàng sinh thu nhập thụ động  
✅ **QR scanning** - Tích hợp AR tại di tích thực tế  
✅ **Full gamification** - Badges, achievements, leaderboard

---

## 🏗️ Kiến trúc Game System

### Hierarchy

```
GAME STRUCTURE
│
├── CHAPTERS (Lớp Cánh Sen) ───────────────────┐
│   ├── Chapter 1: Sen Hồng (Cội Nguồn)        │ 3 chapters
│   ├── Chapter 2: Sen Vàng (Giao Thoa)        │
│   └── Chapter 3: Sen Trắng (Di Sản)          │
│                                              │
├── LEVELS (Màn chơi) ─────────────────────────┤
│   ├── Level có nhiều SCREENS                 │ 15-20 levels
│   ├── Mỗi screen = 1 tương tác               │
│   └── Navigation: screen → screen            │
│                                              │
├── SCREENS (Màn hình tương tác) ──────────────┤
│   ├── DIALOGUE - Hội thoại                   │ 7 loại
│   ├── HIDDEN_OBJECT - Tìm đồ vật             │
│   ├── QUIZ - Trắc nghiệm                     │
│   ├── TIMELINE - Sắp xếp sự kiện             │
│   ├── IMAGE_VIEWER - Xem hình ảnh            │
│   ├── VIDEO - Xem video                      │
│   └── MEMORY - Trò chơi trí nhớ              │
│                                              │
├── AI CHARACTERS ─────────────────────────────┤
│   ├── NPCs lịch sử (Chú Tễu, Thị Kính...)    │
│   ├── 2 states: Amnesia ↔ Restored           │
│   └── Context-aware conversations            │
│                                              │
└── MUSEUM ────────────────────────────────────┘
    ├── Thu thập characters từ levels
    ├── Sinh thu nhập thụ động (5 coins/char/hour)
    └── Capped tối đa 24h, 5000 coins
```

---

## 🎯 Luồng chơi hoàn chỉnh (FIXED)

### **1. Khởi tạo**

```
User đăng ký/đăng nhập
    ↓
Auto-tạo game_progress
    ├─ Coins: 1000
    ├─ Petals: 0
    ├─ Level: 1
    └─ Unlocked: [Chapter 1]
```

### **2. Chọn Chapter & Level**

```javascript
// GET /api/game/chapters
{
  chapters: [
    {
      id: 1,
      name: "Sen Hồng - Cội Nguồn",
      is_unlocked: true,
      total_levels: 5,
      completed_levels: 0,
    },
    {
      id: 2,
      name: "Sen Vàng - Giao Thoa",
      is_unlocked: false, // Cần petals để mở
      required_petals: 5,
    },
  ];
}

// GET /api/game/chapters/1/levels
{
  levels: [
    {
      id: 1,
      name: "Ký ức Chú Tễu",
      is_locked: false, // Level 1 luôn mở
      is_completed: false,
    },
    {
      id: 2,
      name: "Bí mật Hoàng Thành",
      is_locked: true, // Cần hoàn thành level 1
      required_level: 1,
    },
  ];
}
```

### **3. Bắt đầu Level (START SESSION)**

```javascript
// POST /api/game/levels/1/start
Response: {
  session_id: 123,
  level: {
    id: 1,
    name: "Ký ức Chú Tễu",
    total_screens: 5
  },
  current_screen: {
    id: "screen_01",
    type: "DIALOGUE",
    index: 0,
    is_first: true,
    is_last: false,
    content: [
      {
        speaker: "AI",
        text: "Chào bạn! Ta là Chú Tễu...",
        avatar: "teu_bw.png"  // Black & white = mất trí nhớ
      }
    ],
    skip_allowed: true
  }
}
```

**QUAN TRỌNG:**

- ✅ Mỗi level chỉ có **1 active session** tại 1 thời điểm
- ✅ Session cũ sẽ auto-expire khi tạo session mới
- ✅ Session timeout: 24 giờ không hoạt động

---

## 🎬 Screen Types & Interactions (FIXED)

### **A. DIALOGUE Screen**

**Chức năng:** Hiển thị hội thoại giữa AI và người chơi

```javascript
{
  type: "DIALOGUE",
  content: [
    {
      speaker: "AI",
      text: "Bạn có muốn tìm hiểu về trống đồng không?",
      avatar: "teu_bw.png"
    }
  ],
  skip_allowed: true,        // Có thể skip
  auto_advance: false,       // Không tự động next
  next_screen_id: "screen_02"
}
```

**Flow:**

```
User đọc xong → Click "Next" → POST /api/game/sessions/{id}/next-screen
```

---

### **B. HIDDEN_OBJECT Screen**

**Chức năng:** Tìm các vật phẩm ẩn trong hình

```javascript
{
  type: "HIDDEN_OBJECT",
  background_image: "stage.jpg",
  guide_text: "Tìm 3 vật phẩm của Chú Tễu",
  items: [
    {
      id: "item_fan",
      name: "Cái quạt mo",
      coordinates: { x: 15, y: 45, width: 10, height: 10 },
      fact_popup: "Cái quạt Chú Tễu dùng để phe phẩy",
      points: 10
    },
    {
      id: "item_flag",
      name: "Cờ hội",
      coordinates: { x: 80, y: 20, width: 5, height: 15 },
      points: 15
    }
  ],
  required_items: 2,          // Cần tìm 2/3 items
  ai_hints_enabled: true,
  next_screen_id: "screen_03"
}
```

**Flow:**

```
1. User click vào tọa độ item
   ↓
2. POST /api/game/levels/{id}/collect-clue
   Body: { clueId: "item_fan" }
   ↓
3. Response: {
     points_earned: 10,
     progress: { collected: 1, required: 2 }
   }
   ↓
4. Khi đủ required_items → Có thể next screen
```

**FIXED: Validation logic**

```javascript
// Kiểm tra có đủ items chưa
if (collected_items.length < required_items) {
  return {
    success: false,
    message: `Need ${required_items - collected_items.length} more items`,
  };
}
```

---

### **C. QUIZ Screen**

**Chức năng:** Trả lời câu hỏi trắc nghiệm

```javascript
{
  type: "QUIZ",
  question: "Chú Tễu là nhân vật trong nghệ thuật nào?",
  options: [
    { text: "Múa rối nước", is_correct: true },
    { text: "Ca trù", is_correct: false },
    { text: "Tuồng", is_correct: false }
  ],
  time_limit: 60,
  reward: {
    points: 20,
    coins: 10
  },
  next_screen_id: "screen_04"
}
```

**Flow:**

```
1. User chọn đáp án
   ↓
2. POST /api/game/sessions/{id}/submit-answer
   Body: { answerId: "Múa rối nước" }
   ↓
3. Response: {
     is_correct: true,
     points_earned: 20,
     total_score: 120
   }
   ↓
4. Auto-save answer → Có thể next screen
```

**FIXED: Answer validation**

```javascript
// Không cho answer 2 lần
if (session.answered_questions.some((q) => q.screen_id === currentScreen.id)) {
  return {success: false, message: "Already answered"};
}
```

---

### **D. TIMELINE Screen (FIXED)**

**Chức năng:** Sắp xếp sự kiện theo thứ tự thời gian

```javascript
{
  type: "TIMELINE",
  instruction: "Sắp xếp các sự kiện theo đúng thứ tự thời gian",
  events: [
    { id: "evt1", year: 1802, text: "Nguyễn Ánh lên ngôi" },
    { id: "evt2", year: 1858, text: "Pháp tấn công Đà Nẵng" },
    { id: "evt3", year: 1945, text: "Cách mạng Tháng Tám" }
  ],
  correct_order: ["evt1", "evt2", "evt3"],  // Server tự sort theo year
  next_screen_id: "screen_05"
}
```

**Flow (FIXED):**

```
1. User drag & drop để sắp xếp
   ↓
2. POST /api/game/sessions/{id}/submit-timeline
   Body: { eventOrder: ["evt1", "evt2", "evt3"] }
   ↓
3. Server validate:
   - Lấy correct_order = events.sort(by year)
   - So sánh userOrder === correctOrder
   ↓
4. Response: {
     isCorrect: true,
     message: "Timeline order is correct!"
   }
   ↓
5. Nếu correct → Có thể next screen
```

**BUG FIX:**

```javascript
// OLD CODE (MISSING VALIDATION):
// submitTimelineOrder chỉ save order, không validate

// NEW CODE (FIXED):
validateScreenCompletion(screen, session) {
  if (screen.type === 'TIMELINE') {
    const userOrder = session.timeline_order;

    if (!userOrder || userOrder.length === 0) {
      return {
        success: false,
        message: 'Must arrange timeline events first'
      };
    }

    // Validate correct order
    const correctOrder = screen.events
      .sort((a, b) => a.year - b.year)
      .map(e => e.id);

    const isCorrect = JSON.stringify(userOrder) === JSON.stringify(correctOrder);

    if (!isCorrect) {
      return {
        success: false,
        message: 'Timeline order is incorrect'
      };
    }
  }

  return { success: true };
}
```

---

### **E. IMAGE_VIEWER & VIDEO Screens**

```javascript
// IMAGE_VIEWER
{
  type: "IMAGE_VIEWER",
  image: "artifact.jpg",
  caption: "Trống đồng Ngọc Lũ",
  description: "Trống đồng thời Đông Sơn...",
  next_screen_id: "screen_06"
}

// VIDEO
{
  type: "VIDEO",
  video_url: "documentary.mp4",
  duration: 120,
  can_skip: false,          // Phải xem hết mới next
  next_screen_id: "screen_07"
}
```

---

## 🔄 Navigation Flow (FIXED)

### **Quy tắc navigation:**

```javascript
// 1. Check screen completion trước khi next
validateScreenCompletion(currentScreen, session):
  ├─ DIALOGUE: ✓ Always can proceed (except if auto_advance=false)
  ├─ HIDDEN_OBJECT: ✓ Must collect required_items
  ├─ QUIZ: ✓ Must answer question
  ├─ TIMELINE: ✓ Must arrange events correctly
  └─ VIDEO: ✓ Must watch until end (if can_skip=false)

// 2. Navigate to next screen
POST /api/game/sessions/{id}/next-screen
  ├─ Validate current screen completed
  ├─ Find next screen (via next_screen_id or index++)
  ├─ Update session state
  └─ Return next screen data

// 3. Check if level finished
if (nextScreenIndex >= level.screens.length) {
  return {
    level_finished: true,
    message: "Please call completeLevel endpoint"
  }
}
```

---

## ✅ Hoàn thành Level (COMPLETION)

```javascript
// POST /api/game/levels/1/complete
Body: {
  score: 850,
  timeSpent: 300
}

// Server logic:
1. Tính final score = score + timeBonus - hintPenalty
2. Check passed = (finalScore >= passing_score)
3. Nếu passed:
   - Cộng petals, coins, points
   - Unlock character (nếu có)
   - Mark level completed
   - Update progress
4. Response: {
     passed: true,
     score: 850,
     rewards: {
       petals: 2,
       coins: 100,
       character: "teu_full_color"
     },
     new_totals: {
       petals: 2,
       coins: 1100,
       points: 850
     }
   }
```

**IMPORTANT: First-time completion only**

```javascript
// Nếu đã complete trước đó:
if (progress.completed_levels.includes(levelId)) {
  return {
    message: "Level completed (no rewards for replay)",
    alreadyCompleted: true,
    rewardsGiven: false,
  };
}
```

---

## 🤖 AI Character System (FIXED)

### **2 States: Amnesia ↔ Restored**

```javascript
// CHARACTER SCHEMA
{
  name: "Chú Tễu",
  avatar_locked: "teu_bw.png",        // Black & white
  avatar_unlocked: "teu_color.png",   // Full color

  persona_amnesia: "Ta là ai? Đây là đâu? Ký ức ta mờ mịt...",
  persona_restored: "Ha ha! Ta là Chú Tễu, nghệ nhân múa rối!"
}
```

### **State switching logic:**

```javascript
// In AI service:
getCharacterContext(context, userId) {
  const character = db.findById('game_characters', characterId);
  const progress = db.findOne('game_progress', { user_id: userId });

  // Check if level completed
  const isLevelCompleted = progress.completed_levels.includes(context.levelId);

  // Choose persona
  let activePersona = character.persona_amnesia;  // Default
  let activeAvatar = character.avatar_locked;

  if (isLevelCompleted || context.screenType === 'COMPLETION') {
    activePersona = character.persona_restored;
    activeAvatar = character.avatar_unlocked;
  }

  return {
    name: character.name,
    persona: activePersona,
    avatar: activeAvatar
  };
}
```

### **Chat flow:**

```javascript
// POST /api/ai/chat
Body: {
  message: "Chú Tễu ơi, cái quạt ở đâu?",
  context: {
    levelId: 1,
    screenType: "HIDDEN_OBJECT",
    screenId: "screen_02"
  }
}

// Server builds context:
1. Get character state (amnesia/restored)
2. Get knowledge base from level
3. Get conversation history
4. Call AI API với system prompt
5. Save to ai_chat_history
6. Return response

Response: {
  message: "Hỡi ôi... cái quạt... ta nghĩ nó ở đâu đó bên trái...",
  character: {
    name: "Chú Tễu",
    avatar: "teu_bw.png"  // Still amnesia
  }
}
```

---

## 🏛️ Museum System (FIXED)

### **Cơ chế:**

```javascript
// Thu thập characters từ levels
progress.collected_characters = ["teu_full_color", "thikinh", "giong"]

// Mở museum → Thu nhập thụ động
income_per_hour = collected_characters.length × 5
// Ví dụ: 3 characters × 5 = 15 coins/hour

// Capped mechanism:
- Max 24 giờ tích lũy
- Max 5000 coins pending
- Phải collect thường xuyên
```

### **API Flow (FIXED WITH LOCK):**

```javascript
// GET /api/game/museum
{
  is_open: true,
  income_per_hour: 15,
  pending_income: 360,      // 24 hours accumulated
  hours_accumulated: 24,
  capped: true,             // Hit 24h cap
  can_collect: true
}

// POST /api/game/museum/collect (WITH LOCK)
// Server logic:
1. Acquire lock (prevent double-claim)
2. Calculate pending income
3. Cap to max 5000 coins
4. Update progress atomically:
   - coins += pending_income
   - last_museum_collection = now
5. Release lock
6. Return success

Response: {
  collected: 360,
  total_coins: 1460,
  next_collection_in: "4 minutes"
}
```

**BUG FIX:**

```javascript
// OLD: Race condition khi spam click collect
// NEW: Use lock mechanism
activeLocks = new Set();

collectMuseumIncome(userId) {
  const lockKey = `museum_collect_${userId}`;

  if (this.activeLocks.has(lockKey)) {
    return {
      success: false,
      message: 'Collection already in progress'
    };
  }

  this.activeLocks.add(lockKey);

  try {
    // ... collect logic
  } finally {
    this.activeLocks.delete(lockKey);
  }
}
```

---

## 🔄 Session Management (FIXED)

### **Lifecycle:**

```
CREATE SESSION
    ↓
IN_PROGRESS (active)
    ↓
[After 24h inactive]
    ↓
EXPIRED (auto-cleanup)
```

### **Auto-cleanup mechanism:**

```javascript
// Background job runs every 1 hour
startSessionCleanup() {
  setInterval(() => {
    const SESSION_TIMEOUT = 24 * 60 * 60 * 1000;  // 24 hours
    const now = Date.now();

    allSessions.forEach(session => {
      if (session.status !== 'in_progress') return;

      const lastActivity = new Date(session.last_activity).getTime();

      if (now - lastActivity > SESSION_TIMEOUT) {
        db.update('game_sessions', session.id, {
          status: 'expired',
          expired_reason: 'Session timeout (24 hours inactive)'
        });
      }
    });
  }, 60 * 60 * 1000);  // Run every hour
}
```

### **Session validation:**

```javascript
// Every API call checks session validity
getActiveSession(levelId, userId) {
  const session = db.findOne('game_sessions', {
    level_id: levelId,
    user_id: userId,
    status: 'in_progress'
  });

  if (!session) return null;

  // Check timeout
  const lastActivity = new Date(session.last_activity).getTime();
  if (Date.now() - lastActivity > 24 * 60 * 60 * 1000) {
    db.update('game_sessions', session.id, { status: 'expired' });
    return null;
  }

  return session;
}
```

---

## 🎯 Rewards & Progression

### **Points System:**

```javascript
// Level completion
- Base score: từ gameplay
- Time bonus: remaining_time / 10
- Hint penalty: hints_used × 5
- Final score = base + bonus - penalty

// Progression
- Sen petals: Mở chapters (stable currency)
- Coins: Mua items (fast currency)
- Points: Level up user rank (experience)
```

### **Unlocking:**

```
Level 1 → Always unlocked
Level 2 → Cần complete Level 1
Level 3 → Cần complete Level 2
...

Chapter 1 → Always unlocked
Chapter 2 → Cần 5 petals
Chapter 3 → Cần 10 petals
```

---

## 🐛 Major Bug Fixes

### **1. Timeline validation**

- ✅ OLD: Không validate correct order
- ✅ NEW: Validate với server-side correct_order

### **2. Museum race condition**

- ✅ OLD: Có thể spam collect nhiều lần
- ✅ NEW: Lock mechanism prevent double-claim

### **3. Session timeout**

- ✅ OLD: Sessions không expire
- ✅ NEW: Background job cleanup every hour

### **4. Screen completion**

- ✅ OLD: Có thể skip screens không hoàn thành
- ✅ NEW: Strict validation trước khi next

### **5. First-time completion**

- ✅ OLD: Có thể replay để farm rewards
- ✅ NEW: Rewards chỉ cho lần đầu complete

---

## 📊 Database Schema

```javascript
// game_progress
{
  user_id: 1,
  total_sen_petals: 5,
  coins: 1200,
  total_points: 850,
  level: 5,
  unlocked_chapters: [1, 2],
  completed_levels: [1, 2, 3],
  collected_characters: ["teu_full_color", "thikinh"],
  museum_open: true,
  last_museum_collection: "2025-12-30T10:00:00Z"
}

// game_sessions
{
  id: 123,
  user_id: 1,
  level_id: 1,
  status: "in_progress",
  current_screen_id: "screen_03",
  current_screen_index: 2,
  collected_items: ["item_fan"],
  answered_questions: [
    { screen_id: "screen_02", answer: "Múa rối nước", is_correct: true }
  ],
  timeline_order: [],
  score: 120,
  completed_screens: ["screen_01", "screen_02"],
  started_at: "2025-12-30T10:00:00Z",
  last_activity: "2025-12-30T10:15:00Z"
}
```

---

## 🚀 Quick Test Flow

```bash
# 1. Đăng ký/Đăng nhập
POST /api/auth/login
{ "email": "player@sen.com", "password": "123456" }
# → Get token

# 2. Xem progress
GET /api/game/progress
Authorization: Bearer {token}

# 3. Xem chapters
GET /api/game/chapters

# 4. Xem levels trong chapter 1
GET /api/game/chapters/1/levels

# 5. Bắt đầu level 1
POST /api/game/levels/1/start

# 6. Navigate screens
POST /api/game/sessions/{session_id}/next-screen

# 7. Submit answer (nếu QUIZ)
POST /api/game/sessions/{session_id}/submit-answer
{ "answerId": "Múa rối nước" }

# 8. Collect clue (nếu HIDDEN_OBJECT)
POST /api/game/levels/1/collect-clue
{ "clueId": "item_fan" }

# 9. Complete level
POST /api/game/levels/1/complete
{ "score": 850, "timeSpent": 300 }

# 10. Check museum
GET /api/game/museum

# 11. Collect income
POST /api/game/museum/collect
```

---

## 📝 Notes for Frontend

### **1. Session management**

- Lưu `session_id` khi startLevel
- Pass `session_id` cho mọi navigation/action
- Handle session expired (status 404)

### **2. Screen rendering**

- Check `screen.type` để render đúng UI
- Validate completion trước khi enable "Next" button
- Show progress: `{completed_screens}/{total_screens}`

### **3. AI chat**

- Avatar thay đổi theo state (bw → color)
- Personality thay đổi (confused → clear)
- Context-aware: gửi `levelId`, `screenType`

### **4. Museum**

- Show pending income real-time
- Disable collect nếu `pending_income === 0`
- Show cap warning nếu `capped === true`

---

## ✅ Summary of Fixes

| Issue                  | Status   | Solution                             |
| ---------------------- | -------- | ------------------------------------ |
| Timeline validation    | ✅ FIXED | Server-side correct order validation |
| Museum race condition  | ✅ FIXED | Lock mechanism                       |
| Session timeout        | ✅ FIXED | Background cleanup job               |
| Screen completion skip | ✅ FIXED | Strict validation                    |
| Replay reward farming  | ✅ FIXED | First-time completion only           |
| Navigation edge cases  | ✅ FIXED | Comprehensive validation             |

---

**Version:** 2.0 (Fixed)  
**Last Updated:** December 30, 2025  
**Status:** Production Ready ✅
