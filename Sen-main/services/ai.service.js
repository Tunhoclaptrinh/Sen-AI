const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');
const db = require('../config/database');

const DB_PATH = path.join(__dirname, '../database/db.json');
const PYTHON_SERVICE_URL = 'http://localhost:8000/process_query';

class AIService {
    constructor() {

    this.API_KEY = process.env.OPENAI_API_KEY || process.env.GEMINI_API_KEY;
    this.MODEL = process.env.AI_MODEL || 'gpt-4o-mini';
    this.API_URL = process.env.OPENAI_API_KEY
      ? 'https://api.openai.com/v1/chat/completions'
      : 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent';
  }

// async chat(userId, message, context = {}) {
//     const cleanMessage = message.trim();
//     try {
//       // LOG 1: Kiểm tra xem hàm chat đã được gọi chưa
//       console.log("\n--- [DEBUG] BẮT ĐẦU GỌI AI SERVICE ---");

//       // Lấy nhân vật
//       const character = await this.getCharacterContext(context, userId);
      
//       // Lấy lịch sử (Chú ý tên biến ở đây)
//       const historyData = await this._getFormattedHistory(userId, context.characterId);

//       // LOG 2: ĐÂY LÀ ĐOẠN BẠN ĐANG CẦN KIỂM TRA
//       console.log("👉 Input người dùng:", cleanMessage);
//       console.log("👉 History gửi sang Python (5 câu gần nhất):", JSON.stringify(historyData, null, 2));

//       // Gọi sang Python
//       const response = await axios.post(PYTHON_SERVICE_URL, {
//         user_input: cleanMessage,
//         history: historyData // Gửi mảng đã format
//       }, { timeout: 15000 });

//       // LOG 3: Kiểm tra kết quả từ Python trả về
//       console.log("✅ Python Response:", response.data.answer.substring(0, 50) + "...");

//       const { answer, rewritten_query, route } = response.data;

//       // Lưu vào DB
//       const chatRecord = await db.create('ai_chat_history', {
//         user_id: userId,
//         level_id: context.levelId || null,
//         character_id: context.characterId || 1,
//         message: cleanMessage,
//         response: answer,
//         context: { ...context, rewritten: rewritten_query, route: route },
//         created_at: new Date().toISOString()
//       });

//       return { success: true, data: { message: answer, character, timestamp: chatRecord.created_at } };

//     } catch (error) {
//       // LOG 4: Nếu có lỗi, nó sẽ hiện ở đây thay vì chỉ hiện tin nhắn bảo trì
//       console.error('❌ LỖI TẠI AI SERVICE:', error.message);
//       return {
//         success: false,
//         message: 'Dịch vụ AI đang bảo trì, Minh sẽ quay lại sớm!',
//         statusCode: 500
//       };
//     }
//   }



    /**
     * CHAT CHÍNH: Kết nối NodeJS - db.json - FastAPI
     */
    async chat(userId, message, context = {}) {

      const cleanMessage = message.trim();


      if (!cleanMessage) return { success: false, message: 'Nội dung trống' };

      try {

          // 1. LẤY NHÂN VẬT (NPC) - Sửa lỗi "getCharacterContext is not a function"
          const character = await this.getCharacterContext(context, userId);

          // 2. LẤY LỊCH SỬ CHO REFLECTION
          const history = await this._getFormattedHistory(userId, context.characterId);

          // 3. GỌI SANG PYTHON FASTAPI
          const response = await axios.post(PYTHON_SERVICE_URL, {
              user_input: cleanMessage,
              history: history
          }, { timeout: 15000 });

          const { answer, rewritten_query, route, score } = response.data;

          // 4. LƯU VÀO db.json QUA WRAPPER DATABASE CỦA BẠN
          const chatRecord = await db.create('ai_chat_history', {
              user_id: userId,
              level_id: context.levelId || null,
              character_id: context.characterId || (character ? character.id : 1),
              message: cleanMessage,
              response: answer,
              context: {
                  ...context,
                  rewritten: rewritten_query,
                  route: route
              },
              created_at: new Date().toISOString()
          });

          return {
              success: true,
              data: {
                  message: answer,
                  character: character,
                  timestamp: chatRecord.created_at,
                  route: route
              }
          };


      } catch (error) {
          console.error('AI Chat Error:', error);
          return {
              success: false,
              message: 'Dịch vụ AI đang bảo trì, Minh sẽ quay lại sớm!',
              statusCode: 500
          };
      }
    }

    /**
     * Lấy thông tin nhân vật (Hàm này vừa bị thiếu dẫn đến lỗi của bạn)
     */
    async getCharacterContext(context, userId) {
        let characterId = context.characterId;

        // Nếu không có characterId, thử lấy từ level
        if (!characterId && context.levelId) {
            const level = await db.findById('game_levels', context.levelId);
            if (level) characterId = level.ai_character_id;
        }

        if (!characterId) characterId = 1; // Mặc định là Minh/Tễu

        const character = await db.findById('game_characters', characterId);
        if (!character) return { name: "Minh", speaking_style: "Thân thiện" };

        return {
            id: character.id,
            name: character.name,
            persona: character.persona,
            speaking_style: character.speaking_style,
            avatar: character.avatar
        };
    }

    /**
     * Lấy lịch sử hội thoại và format chuẩn cho Reflection
     */
    async _getFormattedHistory(userId, characterId, limit = 5) {
        try {
            const query = { user_id: userId };
            if (characterId) query.character_id = characterId;

            const rawHistory = await db.findMany('ai_chat_history', query);
            
            const formatted = rawHistory
                .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                .slice(0, limit)
                .reverse()
                .map(h => [
                    { role: 'user', content: h.message },
                    { role: 'assistant', content: h.response }
                ])
                .flat();

            return formatted;
        } catch (error) {
            return [];
        }
    }

    /**
     * Lấy lịch sử chat đơn thuần cho UI
     */
    async getHistory(userId, levelId, limit = 20) {
        const query = { user_id: userId };
        if (levelId) query.level_id = levelId;
        const history = await db.findMany('ai_chat_history', query);
        return { success: true, data: history.slice(-limit) };
    }

    /**
     * Xóa lịch sử
     */
    async clearHistory(userId) {
        const history = await db.findMany('ai_chat_history', { user_id: userId });
        for (const h of history) {
            await db.delete('ai_chat_history', h.id);
        }
        return { success: true, message: 'Lịch sử đã được dọn dẹp.' };
    }
}

module.exports = new AIService();



// /**
//  * AI Service - Tích hợp AI chatbot
//  * Sử dụng OpenAI hoặc Gemini API
//  */

// const db = require('../config/database');

// class AIService {
//   constructor() {
//     this.API_KEY = process.env.OPENAI_API_KEY || process.env.GEMINI_API_KEY;
//     this.MODEL = process.env.AI_MODEL || 'gpt-3.5-turbo';
//     this.API_URL = process.env.OPENAI_API_KEY
//       ? 'https://api.openai.com/v1/chat/completions'
//       : 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent';
//   }

//   /**
//    * Chat với AI
//    */
//   async chat(userId, message, context = {}) {

//     // Sanitize user input - Simple validation
//     const cleanMessage = message
//       .replace(/</g, '&lt;')
//       .replace(/>/g, '&gt;')
//       .replace(/"/g, '&quot;')
//       .replace(/'/g, '&#x27;')
//       .trim();

//     // Length limit
//     if (cleanMessage.length > 500) {
//       return {
//         success: false,
//         message: 'Message too long (max 500 characters)'
//       };
//     }

//     try {
//       // Lấy character context từ level hiện tại
//       const character = await this.getCharacterContext(context, userId);

//       // Lấy knowledge base
//       const knowledge = await this.getKnowledgeBase(context);

//       // Build system prompt
//       const systemPrompt = this.buildSystemPrompt(character, knowledge);

//       // Lấy conversation history
//       const history = await this.getConversationHistory(userId, context.levelId, 5);

//       // Call AI API
//       const aiResponse = await this.callAI(systemPrompt, history, message);

//       // Lưu vào database
//       const chatRecord = await db.create('ai_chat_history', {
//         user_id: userId,
//         level_id: context.levelId || null,
//         character_id: context.characterId || null,
//         message: message,
//         response: aiResponse,
//         context: context,
//         created_at: new Date().toISOString()
//       });

//       return {
//         success: true,
//         data: {
//           message: aiResponse,
//           character: character,
//           timestamp: chatRecord.created_at
//         }
//       };
//     } catch (error) {
//       console.error('AI Chat Error:', error);
//       return {
//         success: false,
//         message: 'AI service temporarily unavailable',
//         statusCode: 500
//       };
//     }
//   }

//   /**
//    * Lấy context của character
//    */
//   async getCharacterContext(context, userId) {
//     // Lấy thông tin nhân vật gốc
//     let characterId = context.characterId;

//     // Nếu đang trong game session, lấy character của level đó
//     if (!characterId && context.levelId) {
//       const level = await db.findById('game_levels', context.levelId);
//       if (level) characterId = level.ai_character_id;
//     }

//     if (!characterId) return null; // Fallback default character

//     const character = await db.findById('game_characters', characterId);

//     // KIỂM TRA TRẠNG THÁI TIẾN ĐỘ CỦA USER VỚI LEVEL NÀY
//     // Để quyết định dùng persona nào (Mất trí nhớ hay Đã hồi phục)
//     const progress = await db.findOne('game_progress', { user_id: userId });
//     const isLevelCompleted = progress?.completed_levels?.includes(context.levelId);

//     // Logic chọn Persona
//     let activePersona = character.persona_amnesia; // Mặc định là mất trí nhớ
//     let activeAvatar = character.avatar_locked;

//     // Nếu đã hoàn thành level HOẶC đang ở màn hình kết thúc (completion screen)
//     if (isLevelCompleted || context.screenType === 'COMPLETION') {
//       activePersona = character.persona_restored;
//       activeAvatar = character.avatar_unlocked;
//     }

//     return {
//       name: character.name,
//       persona: activePersona, // Dùng persona động
//       speaking_style: character.speaking_style,
//       avatar: activeAvatar,
//     };
//   }

//   /**
//    * Lấy knowledge base
//    */
//   async getKnowledgeBase(context) {
//     let knowledge = "";

//     // Lấy kiến thức từ level
//     if (context.levelId) {
//       const level = await db.findById('game_levels', context.levelId);
//       if (level && level.knowledge_base) {
//         knowledge += level.knowledge_base + "\n\n";
//       }

//       // Lấy thông tin artifacts trong level
//       if (level.artifact_ids && level.artifact_ids.length > 0) {
//         const artifacts = (await Promise.all(level.artifact_ids.map(id =>
//           db.findById('artifacts', id)
//         ))).filter(Boolean);

//         artifacts.forEach(artifact => {
//           knowledge += `Artifact: ${artifact.name}\n`;
//           knowledge += `Description: ${artifact.description}\n`;
//           knowledge += `Year: ${artifact.year_created}\n\n`;
//         });
//       }
//     }

//     // Lấy kiến thức từ heritage site
//     if (context.heritageSiteId) {
//       const site = await db.findById('heritage_sites', context.heritageSiteId);
//       if (site) {
//         knowledge += `Heritage Site: ${site.name}\n`;
//         knowledge += `Description: ${site.description}\n`;
//         knowledge += `History: ${site.historical_significance || ''}\n\n`;
//       }
//     }

//     return knowledge || "Kiến thức về lịch sử và văn hóa Việt Nam.";
//   }

//   /**
//    * Build system prompt
//    */
//   buildSystemPrompt(character, knowledge) {
//     // Default character if null
//     if (!character) {
//       character = {
//         persona: 'Bạn là trợ lý AI thông minh về văn hóa Việt Nam.',
//         speaking_style: 'Thân thiện, dễ hiểu, hài hước'
//       };
//     }

//     return `${character.persona}

// Phong cách nói chuyện: ${character.speaking_style}

// KIẾN THỨC CỦA BẠN (CHỈ TRẢ LỜI TRONG PHẠM VI NÀY):
// ${knowledge}

// QUY TẮC:
// 1. Chỉ trả lời dựa trên kiến thức được cung cấp ở trên
// 2. Nếu câu hỏi nằm ngoài phạm vi kiến thức, hãy lịch sự từ chối và hướng người chơi về chủ đề liên quan
// 3. Trả lời ngắn gọn, dễ hiểu (2-3 câu)
// 4. Sử dụng emoji phù hợp để tạo không khí vui vẻ
// 5. Khuyến khích người chơi khám phá thêm`;
//   }

//   /**
//    * Lấy conversation history
//    */
//   async getConversationHistory(userId, levelId, limit = 5) {
//     const query = { user_id: userId };
//     if (levelId) query.level_id = levelId;

//     const history = (await db.findMany('ai_chat_history', query))
//       .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
//       .slice(0, limit)
//       .reverse();

//     return history.map(h => [
//       { role: 'user', content: h.message },
//       { role: 'assistant', content: h.response }
//     ]).flat();
//   }

//   /**
//    * Call AI API (OpenAI hoặc Gemini)
//    */
//   async callAI(systemPrompt, history, userMessage) {
//     if (!this.API_KEY) {
//       // Fallback response nếu không có API key
//       return this.getFallbackResponse(userMessage);
//     }

//     try {
//       const messages = [
//         { role: 'system', content: systemPrompt },
//         ...history,
//         { role: 'user', content: userMessage }
//       ];

//       const response = await fetch(this.API_URL, {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//           'Authorization': `Bearer ${this.API_KEY}`
//         },
//         body: JSON.stringify({
//           model: this.MODEL,
//           messages: messages,
//           max_tokens: 150,
//           temperature: 0.7
//         })
//       });

//       const data = await response.json();

//       if (process.env.OPENAI_API_KEY) {
//         return data.choices[0].message.content;
//       } else {
//         // Gemini response format
//         return data.candidates[0].content.parts[0].text;
//       }
//     } catch (error) {
//       console.error('AI API Error:', error);
//       return this.getFallbackResponse(userMessage);
//     }
//   }

//   /**
//    * Fallback response nếu AI không khả dụng
//    */
//   getFallbackResponse(message) {
//     const responses = [
//       "Hm, câu hỏi hay đấy! Hãy quan sát xung quanh và tìm thêm manh mối nhé! 🔍",
//       "Ta nghĩ bạn đang trên đường đúng rồi đấy! Hãy tiếp tục khám phá! ✨",
//       "Thật tuyệt vời! Bạn đang học hỏi rất nhiều về lịch sử Việt Nam! 🏛️",
//       "Câu hỏi thú vị! Hãy tìm kiếm các vật phẩm xung quanh để tìm câu trả lời nhé! 🎯"
//     ];

//     return responses[Math.floor(Math.random() * responses.length)];
//   }

//   /**
//    * Cung cấp gợi ý
//    */
//   async provideHint(userId, levelId, clueId) {
//     const level = await db.findById('game_levels', levelId);
//     if (!level) {
//       return {
//         success: false,
//         message: 'Level not found',
//         statusCode: 404
//       };
//     }

//     // Kiểm tra coins
//     const progress = await db.findOne('game_progress', { user_id: userId });
//     const hintCost = 10;

//     if (progress.coins < hintCost) {
//       return {
//         success: false,
//         message: 'Not enough coins for hint',
//         statusCode: 400
//       };
//     }

//     // Trừ coins
//     await db.update('game_progress', progress.id, {
//       coins: progress.coins - hintCost
//     });

//     // Lấy hint
//     let hint = "Hãy quan sát kỹ xung quanh! 👀";

//     if (clueId && level.clues) {
//       const clue = level.clues.find(c => c.id === clueId);
//       if (clue && clue.hint) {
//         hint = clue.hint;
//       }
//     }

//     return {
//       success: true,
//       data: {
//         hint: hint,
//         cost: hintCost,
//         remaining_coins: progress.coins - hintCost
//       }
//     };
//   }

//   /**
//    * Giải thích về artifact
//    */
//   async explainArtifact(userId, type, id) {
//     let item;

//     if (type === 'artifact') {
//       item = await db.findById('artifacts', id);
//     } else if (type === 'heritage_site') {
//       item = await db.findById('heritage_sites', id);
//     }

//     if (!item) {
//       return {
//         success: false,
//         message: `${type} not found`,
//         statusCode: 404
//       };
//     }

//     // Build context
//     const context = {
//       name: item.name,
//       description: item.description,
//       history: item.historical_context || item.historical_significance || '',
//       significance: item.cultural_significance || ''
//     };

//     // Generate explanation using AI
//     const character = await this.getCharacterContext({});
//     const prompt = `Hãy giải thích về ${context.name} một cách ngắn gọn, dễ hiểu cho trẻ em:
    
// ${context.description}

// Lịch sử: ${context.history}
// Ý nghĩa: ${context.significance}

// Trả lời bằng giọng điệu ${character.speaking_style}.`;

//     const explanation = await this.callAI(
//       character.persona,
//       [],
//       prompt
//     );

//     return {
//       success: true,
//       data: {
//         item: item,
//         explanation: explanation,
//         character: character
//       }
//     };
//   }

//   /**
//    * Tạo quiz từ AI
//    */
//   async generateQuiz(topicId, difficulty) {
//     // Implementation for generating quiz questions
//     const topic = await db.findById('game_levels', topicId);

//     if (!topic) {
//       return {
//         success: false,
//         message: 'Topic not found',
//         statusCode: 404
//       };
//     }

//     // Generate quiz using AI (mock implementation)
//     const quiz = {
//       questions: [
//         {
//           id: 1,
//           question: `Câu hỏi về ${topic.name}?`,
//           options: ['A', 'B', 'C', 'D'],
//           correct_answer: 'A',
//           explanation: 'Giải thích...'
//         }
//       ]
//     };

//     return {
//       success: true,
//       data: quiz
//     };
//   }

//   /**
//    * Lấy lịch sử chat
//    */
//   async getHistory(userId, levelId, limit) {
//     const query = { user_id: userId };
//     if (levelId) query.level_id = levelId;

//     const history = (await db.findMany('ai_chat_history', query))
//       .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
//       .slice(0, limit);

//     return {
//       success: true,
//       data: history
//     };
//   }

//   /**
//    * Xóa lịch sử
//    */
//   async clearHistory(userId) {
//     const history = await db.findMany('ai_chat_history', { user_id: userId });

//     for (const h of history) {
//       await db.delete('ai_chat_history', h.id);
//     }

//     return {
//       success: true,
//       message: 'Chat history cleared'
//     };
//   }
// }

// module.exports = new AIService();