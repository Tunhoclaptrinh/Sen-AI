const fs = require('fs').promises;
const axios = require('axios');

async function testNPC() {
    const HISTORY_FILE = './history.json';
    const userInput = "Hoàng Thành Thăng Long nằm ở đâu?";

    try {
        // 1. Đọc file (Nếu chưa có thì tạo mới)
        let history = [];
        try {
            const data = await fs.readFile(HISTORY_FILE, 'utf8');
            history = JSON.parse(data);
        } catch {
            history = [{ role: "system", content: "Bạn là hướng dẫn viên Minh." }];
        }

        // 2. Gọi FastAPI
        console.log("🚀 Đang gửi câu hỏi sang FastAPI...");
        const response = await axios.post('http://localhost:8000/process_query', {
            user_input: userInput,
            history: history
        });

        const { answer, rewritten_query, route } = response.data;
        console.log(`🎯 Route nhận diện: ${route}`);
        console.log(`📝 Câu hỏi đã làm rõ: ${rewritten_query}`);
        console.log(`🤖 NPC Minh: ${answer}`);

        // 3. Ghi lại lịch sử
        history.push({ role: "user", content: userInput });
        history.push({ role: "assistant", content: answer });
        await fs.writeFile(HISTORY_FILE, JSON.stringify(history, null, 2));
        console.log("✅ Đã cập nhật lịch sử vào file JSON.");

    } catch (error) {
        console.error("❌ Lỗi kết nối:", error.message);
    }
}

testNPC();