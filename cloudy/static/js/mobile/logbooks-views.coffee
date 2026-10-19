###############################
# Logbook Views
###############################
class LogbooksView extends Backbone.View
  constructor: ->
    super
    @page_id = "logbooks-view"
    $("body").prepend( _.template( $("#jquery-page-canvas").html(), {page_id: @page_id} ) )
    @el = $("#" + @page_id)
    @template = _.template($("#logbooks-view-template").html())
    @template_header = _.template($("#logbooks-view-template-header").html())

    @collection.bind 'reset', @render

  logout: =>
    console.log("loging out")
    $.cookie('api_key', null)
    console.log(app.homeController._views)
    for view_key of app.homeController._views
      app.homeController._views[view_key].close()
    app.homeController._views = {}
    app.homeController.login()
    @unbind()
    @remove()
    @collection.unbind("reset", @render)

  render: =>
    # Build the content using undescore.js templating system
    @el.find('.cloudy-content').html(@template({logbooks: @collection}))
    @el.find('.cloudy-header').html(@template_header())

    # Dont use backbone view events hash because el is dynamicaly created...
    @el.find(".logout-button").bind("click", @logout)

    # Show page
    app.switchCurrentPage(@el)

    # instanciate iScroll
    that = this
    app.launchIScroll('logbooks-view-content', false, { onScrollEnd: ->
	    if ($('#pullDown').hasClass('flip'))
		    $('#pullDown').addClass('loading')
		    $('#pullDown').find('.pullDownLabel').html('Loading...')
		    that.collection.fetch()
    })

  close: =>
    @collection.unbind("reset", @render)
    @unbind()
    @remove()
