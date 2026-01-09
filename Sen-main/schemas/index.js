module.exports = {
  // Auth & User
  user: require('./user.schema'),

  // Heritage & Culture
  heritage_site: require('./heritage_site.schema'),
  artifact: require('./artifact.schema'),
  cultural_category: require('./cultural_category.schema'),
  exhibition: require('./exhibition.schema'),
  timeline: require('./timeline.schema'),

  // User Content
  collection: require('./collection.schema'),
  favorite: require('./favorite.schema'),
  review: require('./review.schema'),
  notification: require('./notification.schema'),

  // Game System
  game_chapter: require('./game_chapter.schema'),
  game_level: require('./game_level.schema'),
  game_character: require('./game_character.schema'),
  game_progress: require('./game_progress.schema'),
  scan_object: require('./scan_object.schema'),
  shop_item: require('./shop_item.schema')
};