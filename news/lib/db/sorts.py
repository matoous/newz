
sorts = {
    'trending': 'LOG(GREATEST(ABS(ups - downs), 1)) * SIGN(ups - downs) + (EXTRACT(EPOCH FROM created_at) / 45000) DESC',
    'new': 'created_at DESC',
    'best': 'ups - downs DESC',
}