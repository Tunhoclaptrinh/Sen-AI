module.exports = {
    user_id: {
        type: 'number',
        required: true,
        foreignKey: 'users',
        description: 'User ID'
    },
    level_id: {
        type: 'number',
        required: true,
        foreignKey: 'game_levels',
        description: 'Level ID'
    },
    status: {
        type: 'string',
        required: true,
        enum: ['in_progress', 'completed', 'expired'],
        default: 'in_progress',
        description: 'Trạng thái session'
    },
    current_screen_id: {
        type: 'string', // Can be string id
        required: true,
        description: 'Screen hiện tại'
    },
    current_screen_index: {
        type: 'number',
        required: true,
        default: 0,
        description: 'Index screen hiện tại'
    },
    collected_items: {
        type: 'array',
        default: [],
        description: 'Items đã thu thập trong session'
    },
    answered_questions: {
        type: 'array',
        default: [],
        description: 'Câu hỏi đã trả lời'
    },
    timeline_order: {
        type: 'array',
        default: [],
        description: 'Thứ tự timeline user sắp xếp'
    },
    score: {
        type: 'number',
        default: 0,
        description: 'Điểm số hiện tại của session'
    },
    total_screens: {
        type: 'number',
        required: true,
        description: 'Tổng số màn chơi'
    },
    completed_screens: {
        type: 'array',
        default: [],
        description: 'Danh sách screen ID đã hoàn thành'
    },
    screen_states: {
        type: 'object',
        default: {},
        description: 'Lưu trạng thái từng screen (read dialogue, etc)'
    },
    time_spent: {
        type: 'number',
        default: 0,
        description: 'Thời gian chơi (seconds)'
    },
    hints_used: {
        type: 'number',
        default: 0,
        description: 'Số hint đã dùng'
    },
    started_at: {
        type: 'date',
        required: true,
        default: Date.now,
        description: 'Thời gian bắt đầu'
    },
    last_activity: {
        type: 'date',
        required: true,
        default: Date.now,
        description: 'Hoạt động cuối'
    },
    completed_at: {
        type: 'date',
        required: false,
        description: 'Thời gian hoàn thành'
    },
    expired_at: {
        type: 'date',
        required: false,
        description: 'Thời gian hết hạn'
    },
    expired_reason: {
        type: 'string',
        required: false,
        description: 'Lý do hết hạn'
    }
};
