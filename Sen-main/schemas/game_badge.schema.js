module.exports = {
    name: {
        type: 'string',
        required: true,
        description: 'Tên huy hiệu'
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
    condition: {
        type: 'object',
        required: false,
        description: 'Điều kiện mở khóa'
    },
    type: {
        type: 'string',
        enum: ['level', 'collection', 'special'],
        default: 'special'
    }
};
