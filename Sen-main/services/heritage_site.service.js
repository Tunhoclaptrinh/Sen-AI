const BaseService = require('../utils/BaseService');
const db = require('../config/database');
const { calculateDistance } = require('../utils/helpers');

class HeritageSiteService extends BaseService {
  constructor() {
    super('heritage_sites');
  }

  /**
   * Transform data before create
   */
  async beforeCreate(data) {
    // Transform input data
    if (data.location) {
      if (data.location.address) data.address = data.location.address;
      if (data.location.latitude) data.latitude = data.location.latitude;
      if (data.location.longitude) data.longitude = data.location.longitude;
    }

    if (data.period && !data.cultural_period) {
      data.cultural_period = data.period;
    }

    return super.beforeCreate(data);
  }

  /**
   * Transform data before update
   */
  async beforeUpdate(id, data) {
    // Transform input data
    if (data.location) {
      if (data.location.address) data.address = data.location.address;
      if (data.location.latitude) data.latitude = data.location.latitude;
      if (data.location.longitude) data.longitude = data.location.longitude;
    }

    if (data.period && !data.cultural_period) {
      data.cultural_period = data.period;
    }

    return super.beforeUpdate(id, data);
  }

  async findNearby(lat, lon, radius = 5, options = {}) {
    const allSites = await db.findAll('heritage_sites');

    const nearby = allSites
      .filter(site => site.latitude && site.longitude)
      .map(site => ({
        ...site,
        distance: calculateDistance(lat, lon, site.latitude, site.longitude)
      }))
      .filter(site => site.distance <= radius)
      .sort((a, b) => a.distance - b.distance);

    return {
      success: true,
      data: nearby,
      count: nearby.length
    };
  }

  async getArtifacts(siteId) {
    const artifacts = await db.findMany('artifacts', { heritage_site_id: parseInt(siteId) });
    return {
      success: true,
      data: artifacts,
      count: artifacts.length
    };
  }

  async getTimeline(siteId) {
    const timelines = (await db.findMany('timelines', { heritage_site_id: parseInt(siteId) }))
      .sort((a, b) => a.year - b.year);
    return {
      success: true,
      data: timelines
    };
  }

  async getStats() {
    const allSites = await db.findAll('heritage_sites');

    const stats = {
      total: allSites.length,
      unesco: allSites.filter(s => s.unesco_listed).length,
      topRated: allSites.filter(s => s.rating >= 4).length,
      region: {
        north: allSites.filter(s => s.region === 'Bắc' || s.region === 'North').length,
        center: allSites.filter(s => s.region === 'Trung' || s.region === 'Center').length,
        south: allSites.filter(s => s.region === 'Nam' || s.region === 'South').length
      }
    };

    return {
      success: true,
      data: stats
    };
  }
}

module.exports = new HeritageSiteService();