#
# Some helper methods
#
app =
  scrollerTimeArrayToMinutes: (time_array) ->
    return if time_array? then (parseInt(time_array[0]) * 60 + parseInt(time_array[1])) else 0

  scrollerDateArrayToMinutes: (date_array) ->
    return if date_array? then (parseInt(date_array[2]) + "-" + app.zeroPad( parseInt(date_array[0]) + 1, 2) + "-" + app.zeroPad( parseInt(date_array[1]), 2) + "T00:00:00Z")

  timeToMinutes: (time_str) ->
    return 0 if (time_str || time_str == "")
    match = time_str.match(/^([01]\d|2[0-3]):([0-5]\d)$/)
    return match[1] * 60 + match[2]
    # console.log "time = " + time + "/ in minutes = " + minutes

  minutesToTime: (minutes) ->
    minutes_left = minutes % 60
    hour = Math.floor(minutes / 60)
    # console.log "minutes => " + hour + ":" + minutes_left
    return app.zeroPad(hour, 2) + ":" + app.zeroPad(minutes_left, 2)

  timestampToFormattedDate: (timestamp) ->
    date = new Date(timestamp)
    return app.dateToFormattedDateIso(date)

  dateToFormattedDate: (date) ->
    return app.zeroPad(date.getUTCDate(), 2) + "/" + app.zeroPad(date.getUTCMonth() + 1, 2) + "/" + date.getUTCFullYear()

  dateStrToFormattedDate: (date) ->
    arr = date.split(/[-T :]/)
    date = new Date(arr[0], arr[1]-1, arr[2], arr[3], arr[4], arr[5])
    return app.dateToFormattedDate(date)

  dateToFormattedDateIso: (date) ->
    return date.getUTCFullYear()+ "-" + app.zeroPad(date.getUTCMonth() + 1, 2) + "-" +  app.zeroPad(date.getUTCDate(), 2)

  dateStrToFormattedDateIso: (date) ->
    arr = date.split(/[-T :]/)
    date = new Date(arr[0], arr[1]-1, arr[2], arr[3], arr[4], arr[5])
    return app.dateToFormattedDateIso(date)

  dateStringToDateTimeIso: (str_date) ->
    return str_date + "T00:00:01"

  ISODateString: (d) ->
    d.getUTCFullYear() + "-" + app.zeroPad(d.getUTCMonth() + 1, 2) + "-" + app.zeroPad(d.getUTCDate(), 2) + "T" + app.zeroPad(d.getUTCHours(), 2) + ":" + app.zeroPad(d.getUTCMinutes(),2) + ":" + app.zeroPad(d.getUTCSeconds(), 2)

  switchCurrentPage: (el) ->
    $(".current-page").hide()
    $(".current-page").removeClass("current-page")
    el.addClass("current-page")
    $(".current-page").show()

  zeroPad: (num, count) ->
    numZeropad = num + ''
    while (numZeropad.length < count)
      numZeropad = "0" + numZeropad
    return numZeropad


  # Options to prevent iScroll scrolling activation on form element
  iScrollOptions: {
    useTransform: true,
    momentum: true,
		onBeforeScrollStart: (e) ->
			target = e.target
			while (target.nodeType != 1)
			  target = target.parentNode
			if (target.tagName != 'SELECT' && target.tagName != 'INPUT' && target.tagName != 'TEXTAREA')
				e.preventDefault()
  }

  launchIScroll: (scroller_id) ->
    document.addEventListener('touchmove',  (e) ->
      e.preventDefault()
    , false)
    new iScroll(scroller_id, this.iScrollOptions)
