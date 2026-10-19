#
# Log Collection
#
class LogCollection extends Backbone.Collection
  model: (attrs, options) =>
    if @logbook
      switch @logbook.get('cat')
        when 'ulm_ffplum' then new UlmFfplumLog attrs, options
        when 'plane_dgac' then new PlaneDgacLog attrs, options
        when 'glider_dgac' then new GliderDgacLog attrs, options
        when 'plane_fcl1080' then new PlaneFcl1080Log attrs, options
        when 'helicopter_dgac' then new HelicopterDgacLog attrs, options
        when 'balloon_dgac' then new BalloonDgacLog attrs, options
        when 'parachute_cloudy' then new ParachuteCloudyLog attrs, options
        else
          throw Error("Can't find subclass and Log is an abstract class")
    else
      new Log attrs, options # Must instanciate a Log even if models is empty...

  url: ->
    return "/api/logbooks/" + this.logbook.get("id") + "?k=" + $.cookie('api_key') + "&v=3"

  # Set the logbook_id correponding to this log collection
  # Params = { models: [...], options: {} }
  constructor: (params) ->
    super(params)
    this.logbook = params.options.logbook
    @bind 'reset', @logsFetched
    @bind 'add', @logAdded

  # When fetched from the server
  # The list of logs is contained in the data json attribute :
  # {ok: true, data: [...]}
  parse: (resp) ->
    return resp.data

  logsFetched: =>
    console.log("[LogCollection] logs fetched (reset event on the collection)")
    that = this
    @.each (log) ->
      log.logbook = that.logbook

  logAdded: =>
    console.log("[LogCollection] log added (add event on the collection)")
