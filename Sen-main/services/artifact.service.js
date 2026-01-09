const BaseService = require('../utils/BaseService');
const db = require('../config/database');

class ArtifactService extends BaseService {
  constructor() {
    super('artifacts');
  }

  async getByType(type) {
    const artifacts = await db.findMany('artifacts', { artifact_type: type });
    return {
      success: true,
      data: artifacts
    };
  }

  async getRelated(artifactId) {
    const artifact = await db.findById('artifacts', artifactId);
    if (!artifact) {
      return { success: false, message: 'Artifact not found', statusCode: 404 };
    }

    const allArtifacts = await db.findAll('artifacts');
    const related = allArtifacts
      .filter(a =>
        a.id !== artifactId &&
        (a.heritage_site_id === artifact.heritage_site_id ||
          a.cultural_category_id === artifact.cultural_category_id)
      )
      .slice(0, 5);

    return {
      success: true,
      data: related
    };
  }

  async getStats() {
    const allArtifacts = await db.findAll('artifacts');
    const allSites = await db.findAll('heritage_sites');
    const allReviews = await db.findMany('reviews', { type: 'artifact' });

    const siteMap = allSites.reduce((acc, site) => {
      acc[site.id] = site;
      return acc;
    }, {});

    // Calculate average rating
    const totalRating = allReviews.reduce((sum, r) => sum + (r.rating || 0), 0);
    const avgRating = allReviews.length > 0 ? (totalRating / allReviews.length).toFixed(1) : "0.0";

    const stats = {
      total: allArtifacts.length,
      onDisplay: allArtifacts.filter(a => a.is_on_display !== false).length,
      goodCondition: allArtifacts.filter(a => ['excellent', 'good'].includes(a.condition)).length,
      avgRating: avgRating,
      unesco: allArtifacts.filter(a => siteMap[a.heritage_site_id]?.unesco_listed).length,
      region: {
        north: allArtifacts.filter(a => {
          const region = siteMap[a.heritage_site_id]?.region;
          return region === 'Bắc' || region === 'North';
        }).length,
        center: allArtifacts.filter(a => {
          const region = siteMap[a.heritage_site_id]?.region;
          return region === 'Trung' || region === 'Center';
        }).length,
        south: allArtifacts.filter(a => {
          const region = siteMap[a.heritage_site_id]?.region;
          return region === 'Nam' || region === 'South';
        }).length
      }
    };

    return {
      success: true,
      data: stats
    };
  }
}

module.exports = new ArtifactService();
