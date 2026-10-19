
# coffee --join static/js/mobile/cloudy-mobile.js --watch --compile static/js/mobile/app-helpers.coffee static/js/mobile/logbooks.coffee static/js/mobile/logbooks-collections.coffee static/js/mobile/logs.coffee static/js/mobile/logs-collections.coffee static/js/mobile/logbooks-views.coffee static/js/mobile/logs-views.coffee static/js/mobile/login-view.coffee static/js/mobile/app-controller.coffee static/js/mobile/cloudy-mobile.coffee



app.homeController = new HomeController()

#
# Start the app
#
$(document).ready ->
  Backbone.emulateJSON = true
  Backbone.history.start()
  #app.homeController.navigate("", true);


@app = app
