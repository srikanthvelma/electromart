const admin = (req, res, next) => {
  if (!req.user) {
    return res.status(401).json({ error: 'Access denied. No token provided.' });
  }

  if (req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Access denied. Admin privileges required.' });
  }

  next();
};

module.exports = admin;
