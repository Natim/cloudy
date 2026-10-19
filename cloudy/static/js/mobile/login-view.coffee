

class LoginView  extends Backbone.View
  constructor: (options) ->
    super
    @page_id = "login-view"
    $("body").prepend( _.template( $("#jquery-page-canvas-login").html(), {page_id: @page_id} ) )
    @el = $("#" + @page_id)

    @template = _.template($("#login-view-template").html())
    @template_header = _.template($("#login-view-template-header").html())

    @model.bind("change", @render)

    @render()



  render: =>
    # Build the content using undescore.js templating system
    @el.find('.cloudy-content').html(@template({loginInfo: @model}))
    @el.find('.cloudy-header').html(@template_header())

    # Dont use backbone view events hash because el is dynamicaly created...
    @el.find(".login-button").bind("click", @login)

    # Show page
    app.switchCurrentPage(@el)

  login: =>
    console.log("Loging in")
    that = this
    $.ajax({
      url: "/api/session?email=" + $('[name=email]').val() + "&pwd=" + $('[name=mdp]').val(),
      contentType: 'application/json',
      type: "GET",
      success: ( resp ) ->
        resp = $.parseJSON(resp)
        if (resp.ok == true)
          console.log( 'Login success :', resp.ok)
          $.cookie('api_key', resp.data, {expires: 365})
          $.cookie('last_email', $('[name=email]').val())
          app.homeController.logbooksIndex()
          that.model.destroy()
          that.remove()
        else
          console.log( 'Login error :', resp.ok)
          that.model.set(email:$('[name=email]').val(), mdp: "", error: resp.data)
    });
    return false;


  close: =>
    @remove()
    @unbind()
