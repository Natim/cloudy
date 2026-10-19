#
# Logbook class
#
class Logbook extends Backbone.Model
  constructor: (attributes, options) ->
    super


class UlmFfplumLogbook extends Logbook
  getIcon: -> "/static/raw_css/images/v_ulm_ffplum.png"

class PlaneDgacLogbook extends Logbook
  getIcon: -> "/static/raw_css/images/v_plane_dgac.png"

class GliderDgacLogbook extends Logbook
  getIcon: -> "/static/raw_css/images/v_glider_dgac.png"

class PlaneFcl1080Logbook extends Logbook
  getIcon: -> "/static/raw_css/images/v_plane_dgac.png"

class HelicopterDgacLogbook extends Logbook
  getIcon: -> "/static/raw_css/images/v_helicopter_dgac.png"

class BalloonDgacLogbook extends Logbook
  getIcon: -> "/static/raw_css/images/icon-focus-baloon.png"

class ParachuteCloudyLogbook extends Logbook
  getIcon: -> "/static/raw_css/images/icon-focus-parachute.png"
