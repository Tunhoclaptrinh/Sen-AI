module.exports = {
    user_id: {
        type: 'number',
        required: true,
        foreignKey: 'users',
        description: 'User ID'
    },
    object_id: {
        type: 'number',
        required: true,
        foreignKey: 'scan_objects',
        description: 'Object ID đã scan'
    },
    location: {
        type: 'object',
        required: false,
        description: 'Vị trí scan { lat, long }'
    },
    scanned_at: {
        type: 'date',
        required: true,
        default: Date.now,
        description: 'Thời gian scan'
    }
};
