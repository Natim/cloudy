#
# Our only controller
#

class HomeController extends Backbone.Router
  routes:
    "login": "login"
    "logbooks-:id-logs": "logbookLogs"
    "logbooks-new": "newLogbook"
    "": "logbooksIndex"
    "logbook-:logbookid-logs-new": "newLog"
    "logbook-:logbookid-logs-:logid": "editLog"

  constructor: ->
    super
    @_views = {}
    @logs = []

  user_logged_in: ->
    if $.cookie('api_key')
      return true
    else
      @login()
      return false

  login: (error_msg) ->
    console.log("==> Route to : Login, error = " + error_msg)
    @_views['login'] = new LoginView( model: new Backbone.Model({email: $.cookie('last_email'), mdp: "", error: error_msg}) )

  logbooksIndex: ->
    console.log("==> Route to : Logbooks")
    if @user_logged_in()
      if @_views['logbooks']
        #@_views['logbooks'].render()
        this.logbooks.fetch(error: (model, error) -> app.homeController.login(error.statusText) )
      else
        this.logbooks = new LogbookCollection()
        @_views['logbooks'] = new LogbooksView( collection: this.logbooks )
        this.logbooks.fetch(error: (model, error) -> app.homeController.login(error.statusText) )

  logbookLogs: (id) ->
    console.log("==> Route to : Logs of " + id)

    # We need the logbook here to build the apropriate type of Logs in the LogCollection
    if this.logbooks
      current_logbook = this.logbooks.get(id)
    else
      app.homeController.navigate("", true);

    if @_views["logbooks-#{id}-logs"]
      this.logs[id].fetch(error: (model, error) -> app.homeController.login(error.statusText) )
    else
      this.logs[id] = new LogCollection( models: [], options: {logbook: current_logbook} )
      @_views["logbooks-#{id}-logs"] = new LogsView ( collection: this.logs[id], logbook: current_logbook )
      this.logs[id].fetch(error: (model, error) -> app.homeController.login(error.statusText) )


  newLogbook: ->
    console.log("==> Route to new Logbook")
    @_views["logbooks-new"] = new NewLogbookView ( model: new Logbook() )

  newLog: (logbookid)  ->
    console.log("==> Route to : new Log of " + logbookid)

    # We need the parent logbook here to build the apropriate type of Logs in the LogCollection
    if this.logbooks
      current_logbook = this.logbooks.get(logbookid)
    else
      app.homeController.navigate("", true);


    @_views["logbook-#{logbookid}-logs-new"] = switch current_logbook.get('cat')
        when 'ulm_ffplum'
          ulm_ffplum_log = new UlmFfplumLog()
          ulm_ffplum_log.logbook = current_logbook
          new NewUlmFfplumLogView ( model: ulm_ffplum_log, options: {logbook: current_logbook} )
        when 'plane_dgac'
          plane_dgac_log = new PlaneDgacLog()
          plane_dgac_log.logbook = current_logbook
          new NewPlaneDgacLogView ( model: plane_dgac_log, options: {logbook: current_logbook} )
        when 'glider_dgac'
          glider_dgac_log = new GliderDgacLog()
          glider_dgac_log.logbook = current_logbook
          new NewGliderDgacLogView ( model: glider_dgac_log, options: {logbook: current_logbook} )
        when 'plane_fcl1080' then new PlaneFcl1080Log attrs, options
        when 'helicopter_dgac'
          plane_dgac_log = new PlaneDgacLog()
          plane_dgac_log.logbook = current_logbook
          new NewPlaneDgacLogView ( model: plane_dgac_log, options: {logbook: current_logbook} )
        when 'balloon_dgac' then new BalloonDgacLog attrs, options
        when 'parachute_cloudy' then new ParachuteCloudyLog attrs, options

  editLog: (logbookid, logid)  ->
    console.log("==> Route to : edit Log " + logid + " of " + logbookid)

    # We need the parent logbook here to build the apropriate type of Logs in the LogCollection
    if this.logbooks
      current_logbook = this.logbooks.get(logbookid)
    else
      app.homeController.navigate("", true);

    current_log = this.logs[logbookid].get(logid)
    @_views["logbook-#{logbookid}-logs-#{logid}-edit"] = switch current_logbook.get('cat')
        when 'ulm_ffplum'
          new NewUlmFfplumLogView ( model: current_log, options: {logbook: current_logbook} )
        when 'plane_dgac'
          new NewPlaneDgacLogView ( model: current_log, options: {logbook: current_logbook} )
        when 'glider_dgac'
          new NewGliderDgacLogView ( model: current_log, options: {logbook: current_logbook} )
        when 'plane_fcl1080' then new PlaneFcl1080Log attrs, options
        when 'helicopter_dgac'
          new NewPlaneDgacLogView ( model: current_log, options: {logbook: current_logbook} )
        when 'balloon_dgac' then new BalloonDgacLog attrs, options
        when 'parachute_cloudy' then new ParachuteCloudyLog attrs, options
