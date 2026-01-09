module.exports = {
    user_id: {
        type: 'number',
        required: true,
        unique: true,
        foreignKey: 'users',
        description: 'User ID'
    },
    items: {
        type: 'array',
        default: [],
        description: 'Danh sách items: { item_id, quantity, acquired_at }'
    }
};
