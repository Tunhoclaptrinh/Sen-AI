module.exports = {
    name: {
        type: 'string',
        required: true,
        description: 'Tên thành tựu'
    },
    description: {
        type: 'string',
        required: true,
        description: 'Mô tả'
    },
    icon: {
        type: 'string',
        required: true,
        description: 'Icon URL'
    },
    points: {
        type: 'number',
        default: 10,
        description: 'Điểm thưởng'
    },
    target: {
        type: 'number',
        required: true,
        description: 'Mục tiêu cần đạt'
    },
    type: {
        type: 'string',
        required: true,
        description: 'Loại thành tựu (orders, reviews, etc)'
    }
};
