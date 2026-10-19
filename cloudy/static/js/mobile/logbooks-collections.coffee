#
# Logbook Collection
#
class LogbookCollection extends Backbone.Collection
  model: (attrs, options) ->
    switch attrs.cat
      when 'ulm_ffplum' then new UlmFfplumLogbook attrs, options
      when 'plane_dgac' then new PlaneDgacLogbook attrs, options
      when 'glider_dgac' then new GliderDgacLogbook attrs, options
      when 'plane_fcl1080' then new PlaneFcl1080Logbook attrs, options
      when 'helicopter_dgac' then new HelicopterDgacLogbook attrs, options
      when 'balloon_dgac' then new BalloonDgacLogbook attrs, options
      when 'parachute_cloudy' then new ParachuteCloudyLogbook attrs, options

  url: ->
    "/api/logbooks?k=" + $.cookie('api_key') + "&v=3"

  constructor: ->
    super
    @bind 'reset', @logbookAdded

  # When fetched from the server
  # The list of logbooks is contained in the data json attribute :
  # {ok: true, data: [...]}
  parse: (data) ->
    return data.data

  logbookAdded: =>
    console.log("[LogbookCollection] logbooks fetched (reset event on the collection)")
