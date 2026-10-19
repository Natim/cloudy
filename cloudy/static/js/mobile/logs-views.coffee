###############################
# Log Views
###############################
class LogsView extends Backbone.View
  constructor: (options) ->
    super
    @logbook = options.logbook
    @page_id = "logbook-" + @logbook.id + "-logs-view"
    @css_class_bg = "cloudy-background-mobile"
    $("body").prepend( _.template( $("#jquery-page-canvas").html(), {page_id: @page_id, css_class_bg: @css_class_bg} ) )
    @el = $("#" + @page_id)

    @template = _.template($("#logs-view-template").html())
    @template_header = _.template($("#logs-view-template-header").html())

    @collection.bind 'reset', @render


  render: =>
    # Build the content using undescore.js templating system
    @el.find('.cloudy-content').html(@template({logs : @collection}))
    @el.find('.cloudy-header').html(@template_header({logbook: @logbook}))

    # Show page
    app.switchCurrentPage(@el)

    # instanciate iScroll
    scroller = @page_id + '-content'
    that = this
    app.launchIScroll(scroller, false, { onScrollEnd: ->
	    if ($('#pullDown').hasClass('flip'))
		    $('#pullDown').addClass('loading')
		    $('#pullDown').find('.pullDownLabel').html('Loading...')
		    that.collection.fetch()
    })

  close: =>
    @collection.unbind("reset", @render)
    @unbind()
    @remove()






###############################
# New log Views
###############################
class NewLogView  extends Backbone.View
  buildTemplate: ->
    $("body").prepend( _.template( $("#jquery-page-canvas").html(), {page_id: @page_id} ) )
    @el = $("#" + @page_id)

    @template = _.template($("#" + @page_id + "-template").html())
    @template_header = _.template($("#" + @page_id + "-template-header").html())

  render: =>
    # Build the content using undescore.js templating system
    @el.find('.cloudy-content').html(@template({log: @model}))
    @el.find('.cloudy-header').html(@template_header({logbook: @logbook}))

    # Show page
    app.switchCurrentPage(@el)

    # Dont use backbone view events hash because el is dynamicaly created...
    @el.find(".save-button").bind("click", @saveLog)
    @el.find(".back-button").bind("click", @back)


    # instanciate iScroll
    scroller = @page_id + '-content'
    app.launchIScroll(scroller)
    $("input.time-scroller").scroller({ theme: 'ios', preset: 'time', ampm: false, timeFormat: 'HH:ii', width: 80 })
    $("input.date-scroller").scroller({ theme: 'ios', preset: 'date', dateFormat: 'yyyy-mm-dd', width: 80  })
    $(".jquery-ui-radio").buttonset()

  validateAndSaveLog: =>
    if @model.isValid() == true
      console.log("Log is valid => Saving it on the server")
      that = this
      @model.save null,
        success: (model, response) ->
          console.log("Success ! Log saved !")
          app.homeController.logbookLogs(that.model.logbook.id, that.model.logbook.cat)
          app.homeController.navigate("logbooks-" + that.model.logbook.id + "-logs", false);
          that.close()

  unsetUnusedAttributes: =>
    @model.unset('files', {silent: true} )
    @model.unset('visibl', {silent: true} )
    @model.unset('deleted', {silent: true} )
    @model.unset('optional_filter', {silent: true} )
    @model.unset('lbook', {silent: true} )
    @model.unset('cdate', {silent: true} )
    @model.unset('udate', {silent: true} )

  back: =>
    history.back()
    @close()

  close: =>
    @unbind()
    @remove()
    $("input.time-scroller").scroller('destroy')
    $("input.date-scroller").scroller('destroy')



class NewPlaneDgacLogView  extends NewLogView
  constructor: (options) ->
    super
    @logbook = options.logbook
    @page_id = "new-plane-dgac-log-view"
    @buildTemplate()
    @render()

  saveLog: =>
    # Membre équipage
    @model.set( {'mbr_equipage_nuit': 0, 'mbr_equipage_jour': 0} , {silent: true})
    current_mbr_equipage = 'mbr_equipage_' + $('[name=mbr_eq_period]').val()
    console.log "Membre équipage Selected mode : " + current_mbr_equipage
    json = {}
    json[current_mbr_equipage] = app.scrollerTimeArrayToMinutes( $('[name=mbr_eq_time]').scroller('getValue') )
    @model.set( json, {silent: true} )

    # Pilote Monomoteur
    @model.set( {'mono_jdbl': 0, 'mono_jcdb': 0, 'mono_ndbl': 0, 'mono_ncdb': 0} , {silent: true})
    mono_dbl_or_cdb = $('[name=mono_dbl_or_cdb]:checked').val()
    current_mono = 'mono_' + $('[name=mono_period]').val() + mono_dbl_or_cdb
    console.log "Pilote Monomoteur Selected mode : " + current_mono
    if (mono_dbl_or_cdb != undefined)
      json = {}
      json[current_mono] = app.scrollerTimeArrayToMinutes( $('[name=mono_time]').scroller('getValue') )
      @model.set( json, {silent: true} )

    # Pilote Multimoteurs multi_dbl_cplt_or_cdb
    @model.set( {'mul_jdbl': 0, 'mul_jcdb': 0, 'mul_jcplt': 0, 'mul_ndbl': 0, 'mul_ncdb': 0, 'mul_ncplt': 0} , {silent: true})
    mul_dbl_cplt_or_cdb = $('[name=mul_dbl_cplt_or_cdb]:checked').val()
    current_mul = 'mul_' + $('[name=mul_period]').val() + mul_dbl_cplt_or_cdb
    console.log "Pilote Multimoteurs Selected mode : " + current_mul
    if (mul_dbl_cplt_or_cdb != undefined)
      json = {}
      json[current_mul] = app.scrollerTimeArrayToMinutes( $('[name=mul_time]').scroller('getValue') )
      @model.set( json, {silent: true} )

    # Vol aux instruments
    @model.set( {'vai_dbl': 0, 'vai_plt': 0} , {silent: true})
    instru_dbl_or_plt = $('[name=instru_dbl_or_plt]:checked').val()
    console.log "Vol aux instruments Selected mode : " + 'vai_' + instru_dbl_or_plt
    if (instru_dbl_or_plt != undefined)
      current_instru = 'vai_' + instru_dbl_or_plt
      json = {}
      json[current_instru] = app.scrollerTimeArrayToMinutes( $('[name=instru_time]').scroller('getValue')  )
      @model.set( json, {silent: true} )

    # Autres
    @model.set( {'aeronef_type': $('[name=aeronef_type]').val() }, {silent: true} )
    @model.set( {'aeronef_imma': $('[name=aeronef_imma]').val() }, {silent: true} )
    @model.set( {'natvol':  $('[name=natvol]').val() }, {silent: true} )
    @model.set( {'fctbrd': $('[name=fctbrd]').val() }, {silent: true} )
    @model.set( {'simu': app.scrollerTimeArrayToMinutes( $('[name=simu_time]').scroller('getValue') ) }, {silent: true} )
    @model.set( {'ifr': $('[name=ifr]').val() || 0 }, {silent: true} )
    @model.set( {'obs': $('[name=obs]').val()}, {silent: true} )
    @model.set( {'date': app.scrollerDateArrayToMinutes($('[name=date]').scroller('getValue')) }, {silent: true} )

    # Optionnels
    # TODO
    @model.unset('airpar', {silent: true} )
    @model.unset('airpdep', {silent: true} )
    @model.unset('staffob', {silent: true} )

    @unsetUnusedAttributes()
    @validateAndSaveLog()
    return false



class NewGliderDgacLogView  extends NewLogView

  constructor: (options) ->
    super
    @logbook = options.logbook
    @page_id = "new-glider-dgac-log-view"
    @buildTemplate()
    @render()

  saveLog: =>
    # Heures de vol
    @model.set( {'flytime_dbl': 0, 'flytime_cdb': 0, 'flytime_ins': 0} , {silent: true})
    flytime_dbl_cdb_or_ins = $('[name=flytime_dbl_cdb_or_ins]:checked').val()
    console.log "Flytime Selected mode : " + 'flytime_' + flytime_dbl_cdb_or_ins
    if (flytime_dbl_cdb_or_ins != undefined)
      current_instru = 'flytime_' + flytime_dbl_cdb_or_ins
      json = {}
      json[current_instru] = app.scrollerTimeArrayToMinutes( $('[name=flytime_time]').scroller('getValue')  )
      @model.set( json, {silent: true} )

    # Autres
    @model.set( {'glider_type': $('[name=glider_type]').val() }, {silent: true} )
    @model.set( {'glider_imma': $('[name=glider_imma]').val() }, {silent: true} )
    @model.set( {'fctbrd': $('[name=fctbrd]').val() }, {silent: true} )
    @model.set( {'natvol':  $('[name=natvol]').val() }, {silent: true} )
    @model.set( {'lmode':  $('[name=lmode]').val() }, {silent: true} )
    @model.set( {'obs': $('[name=obs]').val()}, {silent: true} )
    @model.set( {'date': app.scrollerDateArrayToMinutes($('[name=date]').scroller('getValue')) }, {silent: true} )

    # Optionnels
    # TODO
    @model.unset('airpar', {silent: true} )
    @model.unset('airpdep', {silent: true} )
    @model.unset('staffob', {silent: true} )
    @model.unset('cmmts', {silent: true} )

    @unsetUnusedAttributes()
    @validateAndSaveLog()
    return false




class NewUlmFfplumLogView  extends NewLogView

  constructor: (options) ->
    super
    @logbook = options.logbook
    @page_id = "new-ulm-ffplum-log-view"
    @buildTemplate()
    @render()

  saveLog: =>
    # Heures de vol
    @model.set( {'flytime_dbl': 0, 'flytime_cdb': 0} , {silent: true})
    flytime_dbl_or_cdb = $('[name=flytime_dbl_or_cdb]:checked').val()
    console.log "Flytime Selected mode : " + 'flytime_' + flytime_dbl_or_cdb
    if (flytime_dbl_or_cdb != undefined)
      current_instru = 'flytime_' + flytime_dbl_or_cdb
      json = {}
      json[current_instru] = app.scrollerTimeArrayToMinutes( $('[name=flytime_time]').scroller('getValue')  )
      @model.set( json, {silent: true} )

    # Autres
    @model.set( {'ulm_type': $('[name=ulm_type]').val() }, {silent: true} )
    @model.set( {'ulm_imma': $('[name=ulm_imma]').val() }, {silent: true} )
    @model.set( {'obs': $('[name=obs]').val()}, {silent: true} )
    @model.set( {'date': app.scrollerDateArrayToMinutes($('[name=date]').scroller('getValue')) }, {silent: true} )

    # Optionnels
    # TODO

    @unsetUnusedAttributes()
    @validateAndSaveLog()
    return false
