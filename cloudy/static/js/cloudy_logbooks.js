/*JSHINT */
/*global $: true, simpleSlide: true, cloudy: true, Mustache: true, cloudyFormBuilder: true, TIME_FORMAT:true, logbookRootUrl: true, logbookId: true, logbookPage:true, qq: true */


/* Hide date and edit over row buttons */
function clear_row_on_hover_buttons() {
    $("div.date-slip").hide();
    $("div.edit-slip").hide();
}

/* Reset log form from edit to add */
function reset_log_form_to_add() {
    /* logbookType is a global variable set by logbook_base.html */
    if (logbookType === "parachute_cloudy") {
        $('#add-log-title').html("Ajout d'un saut");
    }
    else {
        $('#add-log-title').html("Ajout d'un vol");
    }
    cloudy.reset_form("#add-log-form");
}

$(function() {
    /* loggbook logs slide */
    simpleSlide({
        'swipe':'true',
        'set_speed': 200,
        'callback': function() {

         }
    });
    /* Pop up new logbook */
   $("ul.tabs").tabs("div.panes > div");
    var ovrConf = {
        effect: 'drop',
        api: true,
        mask: {
            color: '#000',
            loadSpeed: 0,
            opacity: 0.4
        },
        top: 300
    };

    // Do not show the logbook popup on default
/*  if ($("a#trigger-add-logbook[rel]").hasClass('empty')) {
        ovrConf.load = true;
    } */

    /* Reset edit form to add form when add log is clicked */
    $("a#trigger-add-log").click( function() {
        reset_log_form_to_add();
        // set hidden field to no val
        $("#id_log_id").val("");
    });

    /* Pop up new/edit log configuration */
    var ovrConfAddLogPopup = {
        effect: 'drop',
        api: true,
        mask: {
            color: '#000',
            loadSpeed: 0,
            opacity: 0.4
        },
        top: 300

    };

     $('div#add-log-popup input.date').dateinput({
        format: 'dd/mm/yyyy',
        offset: [30, 0],
        selectors: true,
        yearRange: [-80, 1]
      // set initial value and show dateinput when page loads
    }).data("dateinput");

    // open add log popup if there are mistakes in the form
    if ($("a#trigger-add-log[rel]").hasClass('show_form')) {
        ovrConfAddLogPopup.load = true;
    }


    $("a#trigger-add-logbook[rel]").overlay(ovrConf);
    $("a#trigger-export[rel]").overlay(ovrConf);
    $("a#trigger-import[rel]").overlay(ovrConf);
    $("a#trigger-add-log[rel]").overlay(ovrConfAddLogPopup);


    // We need to know if an input is in focus
    var inFocus = false;
    $('input, textarea').focus(function() {
      inFocus = true;
    });
    $('input, textarea').blur(function() {
      inFocus = false;
    });

    // and the current logbook page position (left/right)
    var page_position = "left";


    // disable next prev button
    // we need to know if a slide animation is going on
    var slide_anim_done = true;
    $("div#slide-left-page").hide();
    $("div#slide-right-page").click(function(event) {
        event.preventDefault();
        $(this).hide();
        slide_anim_done = false;
        page_position = "right";
        clear_row_on_hover_buttons();
        $("div#slide-left-page").delay(100).fadeIn(400,
                function() { slide_anim_done = true;}
        );
    });
    $("div#slide-left-page").click(function(event) {
        event.preventDefault();
        $(this).hide();
        page_position = "left";
        slide_anim_done = false;
        clear_row_on_hover_buttons();
        $("div#slide-right-page").delay(100).fadeIn(400,
            function() { slide_anim_done = true;}
        );
    });

    // to react accordingly on left/right arrow
    $(document).keydown(function(e){
        // right left binding to move between pages
        if ((e.keyCode === 37 || e.keyCode === 39) && inFocus === false && slide_anim_done === true) {
            if (e.keyCode === 37 && page_position !== "left") {
                 $('.left-button').click();
             }
            if (e.keyCode === 39 && page_position !== "right") {
                 $('.right-button').click();
              }
        }

    });

});



function CloudyFormBuilder(tdElmt, overlay, tooltip) {
    this.td = tdElmt;
    this.overlay = overlay;
    this.tooltip = tooltip;
    this.txtFormTemplate = "<h4>Texte <span>(<span id='tooltip-char-count'>{{currentCount}}</span>/{{max}})</span></h4>" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<form action='.' id='tooltip-form' method='post'  enctype='multipart/form-data'>" +
        "<input type='text' value='{{val}}' name='td' id='tooltip-text-input' />" +
        "<input type='hidden' value='{{log_id}}' name='log_id'/>" +
        "<br class='clear'/><img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<input type='submit' value='ok' />" +
    "</form>";
    this.timeFormTemplate = "<h4>Heures : Minutes</h4>" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<form action='.' id='tooltip-form-time' method='post'  enctype='multipart/form-data'>" +
        "<input type='text' value='{{hours}}' name='td' id='tooltip-hours-input' />" +
        "<label for='tooltip-hours-input'>:</label>" +
        "<input type='text' value='{{mins}}' name='td' id='tooltip-mins-input' />" +
        "<input type='hidden' value='{{log_id}}' name='log_id'/>" +
        "<br class='clear'/><img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<input type='submit' value='ok' />" +
    "</form>";
    this.dateFormTemplate = "<h4>Date</h4>" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<form action='.' id='tooltip-form-date' method='post'  enctype='multipart/form-data'>" +
        "<input type='hidden' value='{{log_id}}' name='log_id'/>" +
        "<input type='text'  id='tooltip-input-date' class='date' />"+
        "<br class='clear'/><img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<input type='submit' value='ok' />" +
    "</form>";
    this.intFormTemplate = "<h4>{{title}}</h4>" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<form action='.' id='tooltip-form-int' method='post'  enctype='multipart/form-data'>" +
        "<input type='hidden' value='{{log_id}}' name='log_id'/>" +
        "<input type='text' value='{{val}}' name='td' size=1 id='tooltip-text-int' />" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<br class='clear'/><input type='submit' value='ok' />" +
    "</form>";
    this.selectFormTemplate = "<h4>{{title}}</h4>" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<form action='.' id='tooltip-form-select' method='post'  enctype='multipart/form-data'>" +
        "<input type='hidden' value='{{log_id}}' name='log_id'/>" +
        "<select name='select-foo'  id='tooltip-select'>{{#options}}<option value='{{val}}'" +
        "{{#selected}}selected='{{selected}}'{{/selected}}>{{val}}</option>{{/options}}</select>" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<br class='clear'/><input type='submit' value='ok' />" +
    "</form>";
    this.textAreamTemplate = "<div class='wrap-tooltip'>" +
        "<div class='head-tooltip'></div>" +
        "<div class='content-tooltip'>" +
        "<h4>Texte <span>(<span id='tooltip-char-count'>{{currentCount}}</span>/{{max}})</span></h4>" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<form action='.' id='tooltip-form-tarea' method='post'  enctype='multipart/form-data'>" +
        "<input type='hidden' value='{{log_id}}' name='log_id'/>" +
        "<textarea id='tooltip-textarea' rows='7' cols='21'>{{val}}</textarea>" +
        "<input type='submit' value='ok' />" +
        "<br class='clear'/><img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
    "</form>" +
    "</div>" +
    "<div class='footer-tooltip'></div>" +
    "</div>";
    this.textMediaTemplate = "<div class='wrap-tooltip'>" +
        "<div class='head-tooltip'></div>" +
        "<div class='content-tooltip'>" +
        "<h4>Images et Documents</h4>" +
        "<img id='ajax-loading' src='/static/img/ajax-loader.gif' />" +
        "<div id='mediacont'>{{{ mediaList }}}</div>" +
        "<form action='.' id='tooltip-form-media' method='post'  enctype='multipart/form-data'>" +
        "<input type='hidden' value='{{log_id}}' name='log_id'/>" +
        "<div id='file-uploader'></div>" +
        "<br class='clear'/>" +
     "</form>" +
    "</div>" +
    "<div class='footer-tooltip'></div>" +
   "</div>";
}

function isInteger(str) {
   return (/^[0-9]+$/.test(str));
}

/* Time formatting
 * Please note that this is the exact reimplementation of
 * /time_format/formatters.py
 * I *FUCKING HATE* code redundancy. */
var time_formatting = {};

/* HHMM computation */
var hhmm =  {};
hhmm.output = function(mins) {
    var hours = (mins / 60) >> 0;
    var minutes = mins % 60;

    if (minutes < 10) {
        minutes = "0"+minutes;
    }

    return hours + ":" + minutes;
};

hhmm.output_min = function(mins) {
    var hours = (mins / 60) >> 0;
    var minutes = mins % 60;
    if (minutes < 10) {
        minutes = "0"+minutes;
    }    return minutes;
};

hhmm.output_hour = function(mins) {
    var hours = (mins / 60) >> 0;
    return hours;
};

hhmm.input = function(format) {
    var value_hours = parseInt(format.split(':')[0],10);
    var value_mins = parseInt(format.split(':')[1],10);
    var value = value_hours * 60 + value_mins;
    return parseInt(value, 10);
};
hhmm.legend = "hh:mm"

time_formatting[0] = hhmm;

/* Tenth computation */
var tenth = {};
tenth.output = function(mins) {
    var res = Math.round(mins/60.0*10)/10;

    if (res % 1 === 0) {
        return res+".0";
    }
    else {
        return res;
    }
};

tenth.output_min = function(tenth) {
    var res = tenth/10;
    if (res % 1 === 0) {
        res += ".0";
    }
    return res.toString().split('.')[1];
};

tenth.output_hour = function(tenth) {
    var res = tenth/10;
    if (res % 1 === 0) {
        res += ".0";
    }
    return res.toString().split('.')[0];
};

tenth.input = function(format) {
    return parseInt(parseFloat(format,10)*60, 10);
};
tenth.legend = "dixièmes"

time_formatting[1] = tenth;

/* Some bindings for transparent access */
time_formatting.output_hour = time_formatting[TIME_FORMAT].output_hour;
time_formatting.output_min = time_formatting[TIME_FORMAT].output_min;
time_formatting.output = time_formatting[TIME_FORMAT].output;
time_formatting.input = time_formatting[TIME_FORMAT].input;
time_formatting.legend = time_formatting[TIME_FORMAT].legend;

/* height formatters */
var height_formatting = {};

/* HHMM computation */
var meters =  {};
meters.output = function(cms) {
    return parseInt(cms, 10)*100;
};
meters.input = function(meters) {
    return parseInt(meters, 10)/100;
};
height_formatting[0] = meters;
var feets = {};
feets.output = function(cms) {
    return Math.round(parseInt(cms, 10)*30.48);
};
feets.input = function(feets) {
    return Math.round(parseInt(feets, 10)/30.48);
};
height_formatting[1] = feets;

height_formatting.output = height_formatting[HEIGHT_FORMAT].output;
height_formatting.input = height_formatting[HEIGHT_FORMAT].input;
/* Update report times */
function report_times_update() {

    var sums = {};
    var fields_list = [];

    // Retrieve the list of the sums
    $("td[sum-field]").each(function(){
        var field_name = $(this).attr('sum-field');
        sums[field_name] = 0;
        fields_list.push(field_name);
    });


    // Now count
    $("td[data-field]").each(function(){
        var field_name = $(this).attr('data-field');
        var value_raw = $.trim($(this).text().replace(/ /g,''));

        if (value_raw !== '--' && value_raw !== '' && value_raw !== 'N/A') {
            if ($(this).attr('type-field') === 'int'){
                 sums[field_name] += parseInt(value_raw, 10);
            }
            else {
                sums[field_name] += time_formatting.input(value_raw);
            }
        }
    });

    // Compute the full field
    var full = 0;

    // Reformat and display
    $("td[sum-field]").each(function(){
        var field_name = $(this).attr('sum-field');
        var value_raw = sums[field_name];
        var value = "";
        var field_type = $(this).attr('type-field');
        var field_attribute = $(this).attr('attr-field');
        if (field_type == 'int') {
            value = value_raw;
        }
        /* int_min when we need to return the min part only
        and update the hours field value if needed */
        else if (field_type == 'int_min') {
             value = time_formatting.output_min(value_raw);
             var sum_field_value =  $(this).attr('rel');
             var selector = $('td[sum-field=' + sum_field_value + ']');
             if (selector) {
                 var sum_hours_whithout_min_report = parseInt(selector.text(), 10);
                 if (sum_hours_whithout_min_report === 0 && value_raw === 0) {
                    selector.text("");
                    value = "";
                 }
                 else {
                     // set new hour
                     var hours = time_formatting.output_hour(value_raw);
                     selector.text(sum_hours_whithout_min_report + parseInt(hours, 10));
                 }
            }
        }
        else {
            if (field_attribute !== 'ignore') {
                full += value_raw;
            }
            if (value_raw === 0) {
                //value = "--";
                value = "";
            }
            else {
                value = time_formatting.output(value_raw);
            }
        }
        $(this).html(value);
    });


    /* Special case FCL 0180 */
    // Recalculate grand totals (TOTAL THIS PAGE + TOTAL FROM PREVIOUS PAGE)
    $("td[sum-field-with-report]").each(function(){
        var field_name = $(this).attr('sum-field-with-report');
        var field_type = $(this).attr('type-field');
        /* TOTAL THIS PAGE */
        var total_page_value = $('td[sum-field=' + field_name + ']').text();
        var report_page_value = $('td[report-data-field][rel=' + field_name + '].reports-info').text();

        if (total_page_value === '' &&  report_page_value === '')  {
            return;
        }
        var total = 0;
        if (report_page_value === '') {
            total = parseInt(total_page_value, 10);
        }
        else if (total_page_value === '') {
            total = parseInt(report_page_value, 10);
        }
        else {
            total = parseInt(total_page_value, 10) +  parseInt(report_page_value, 10);
        }


        if (field_type == 'int') {
            $(this).text(total);
        }
        if (field_type == 'int_min') {
            $(this).text(time_formatting.output_min(total));
            var total_sum_field_hour_value =  $(this).attr('rel');
            var selector = $('td[sum-field-with-report=' + total_sum_field_hour_value + ']');

             if (selector) {

                 if (total === 0 && parseInt(selector.text(), 10) === 0) {
                    selector.text("");
                    $(this).text("");
                 }
                 else {
                     var extra_hours = time_formatting.output_hour(total);
                     var sum_hours_with_report = parseInt(selector.text(), 10);
                     selector.text(parseInt(extra_hours, 10) + parseInt(sum_hours_with_report,10));
                }
             }
        }

    });
    var value = time_formatting.output(full);
    $("#fullreports").html(value);
}



/* Post form Update log */

CloudyFormBuilder.prototype.updateLog = function(form, logId, fieldName, fieldVal, newtdVal, reload) {
    // lobookRootUrl   defined in site_base_logbook.html as Js vars
    var postUrl = logbookRootUrl + logbookId + "/log/" + logId + "/";
    var formDataDic = form.serialize();
    formDataDic += "&field=" + fieldName + "&val=" + fieldVal;
    var instance = this;

    $.post(postUrl, formDataDic,
         function(data) {
            if (data.success===true) {
                instance.td.html(newtdVal);
                report_times_update();
                instance.overlay.close();
            }
            else {
                cloudy.create_flash(data.msg, "warning");
                cloudy.show_pending_flash();
            }
            if (reload===true) {
                location.reload();
            }
         },
         "json"
    );
};

/*
    Build a time input form for an edit inline log entry
*/
CloudyFormBuilder.prototype.timeForm = function() {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-small');
    var currentValue = this.td.html();
    var elem =  currentValue.split(':');
    // If the current value is empty which is represented by the
    // char '--' we prefill the form with 0:0
    if (elem.length != 2) {
        elem = ['0','0'];
    }
    var view = {
        hours: elem[0],
        mins: elem[1],
        log_id: logId
    };
    var html = Mustache.to_html(this.timeFormTemplate, view);
    this.tooltip.html("<p>"+ html + "</p>");
    $('input#tooltip-hours-input').focus().val(elem[0]);

    $('form#tooltip-form-time').submit(function() {
        // validate input
        var hval = $('input#tooltip-hours-input').val().replace(/\s/g, "");
        var mval = $('input#tooltip-mins-input').val().replace(/\s/g, "");

        var isValid = true;
        if (isInteger(mval) === false || parseInt(mval,0) > 59 || (mval.length > 2)) {
             $('input#tooltip-mins-input').toggleClass('invalid');
             isValid = false;
        }
        if (isInteger(hval) === false || parseInt(hval,0) > 100 || (mval.length > 3)) {
             $('input#tooltip-hours-input').toggleClass('invalid');
             isValid = false;
        }
        if (isValid === false) {
            return false;
        }

        var hmstr = hval + ":" + mval;
        var newTimeValue = parseInt(hval,0)*60 + parseInt(mval,0);
        if (newTimeValue === 0) {
            hmstr = "";
            //hmstr = "--";
        }
        instance.td.html(hmstr);
        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, newTimeValue, hmstr);
        return false;

    });
};


/*
Splited Time form for FCL 0180
*/

CloudyFormBuilder.prototype.splitedTimeForm = function(fulltime, datatarget) {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  datatarget;
    var timetype = 'min';
    if (instance.td.hasClass('hour')) {
        timetype = 'hour';
    }
    var idChuncks = instance.td.attr('id').split('_');
    var rowpos = idChuncks[0].substring(1);
    var colpos = idChuncks[1].substring(1);

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-small');
    var currentValue = fulltime;
    var elem =  currentValue.split(':');
    // If the current value is empty which is represented by the
    // char '--' we prefill the form with 0:0
    if (elem.length != 2) {
        elem = ['0','0'];
    }
    var view = {
        hours: elem[0],
        mins: elem[1],
        log_id: logId
    };
    var html = Mustache.to_html(this.timeFormTemplate, view);
    this.tooltip.html("<p>"+ html + "</p>");
    $('input#tooltip-hours-input').focus().val(elem[0]);

    $('form#tooltip-form-time').submit(function() {
        // validate input
        var hval = $('input#tooltip-hours-input').val().replace(/\s/g, "");
        var mval = $('input#tooltip-mins-input').val().replace(/\s/g, "");

        var isValid = true;
        if (isInteger(mval) === false || parseInt(mval,0) > 59 || (mval.length > 2)) {
             $('input#tooltip-mins-input').toggleClass('invalid');
             isValid = false;
        }
        if (isInteger(hval) === false || parseInt(hval,0) > 100 || (mval.length > 3)) {
             $('input#tooltip-hours-input').toggleClass('invalid');
             isValid = false;
        }
        if (isValid === false) {
            return false;
        }

        var hmstr = hval + ":" + mval;
        // update td fulltime attribute with full time value
        instance.td.attr('fulltime', hmstr);
        // calculate new time
        var newTimeValue =  parseInt(hval,0)*60 + parseInt(mval,0);
        if (newTimeValue === 0) {
            hmstr = "";
            //hmstr = "--";
        }
        var targetId = '';
        // the string we want to update is either minval or hourval
        if (timetype === 'hour') {
            hmstr = hval;
            // It is hour so we need to update min cell as well
            targetId = "r" + rowpos + "_c" + (parseInt(colpos,10)+1);
            $('td#'+targetId).html(mval);
        }
        else {
            hmstr = mval;
            targetId = "r" + rowpos + "_c" + (parseInt(colpos,10)-1);
            $('td#'+targetId).html(hval);
        }
        instance.td.html(hmstr);
        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, newTimeValue, hmstr);
        return false;

    });
};

/*
   Date input form for an edit inline log entry
*/
CloudyFormBuilder.prototype.dateForm = function(currentInputDate) {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    var dpieces = currentInputDate.split('-');
    var inputDate = new Date(dpieces[0], dpieces[1]-1, dpieces[2]);
    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-medium');
    var view = {
        val: this.td.html(),
        log_id: logId,
        init_date: this.td.html()
    };
    var html = Mustache.to_html(this.dateFormTemplate, view);

    this.tooltip.html("<p>"+ html +"</p>");
    // initialize dateinput

    var d = new Date();
    var currentyear = parseInt(d.getFullYear(), 10);
    $("input#tooltip-input-date").dateinput({
         change: function(e, date)  {
            instance.isoDate = this.getValue('yyyy-mm-dd');
            instance.mdate = this.getValue('dd mmm');
         },
        format: 'dd/mm/yyyy',
        offset: [30, 0],
        selectors: true,
        yearRange: [-80, 1],
        value: inputDate,
        onHide: function() { }
     // set initial value and show dateinput when page loads
    }).data("dateinput").setValue(inputDate).show();


    // submit form
    $('form#tooltip-form-date').submit(function() {
        var dateInput =  instance.mdate;
        instance.td.html(instance.mdate);


        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, instance.isoDate, instance.mdate, true);
        // force reload
         return false;
    });
};

/*
   Integer input form for an edit inline log entry
*/
CloudyFormBuilder.prototype.intForm = function(max) {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-small');

    var view = {
        val: this.td.html(),
        log_id: logId,
        title: this.td.attr('ctitle')
    };
    var html = Mustache.to_html(this.intFormTemplate, view);
    this.tooltip.html("<p>"+ html +"</p>");
    $('input#tooltip-text-int').focus();
    // int only
    $('input#tooltip-text-int').bind('change, keyup', function(){
         var currentCount = $(this).val().length;
         if (currentCount >= 4 || parseInt($(this).val(),0) > max) {
            $(this).addClass('invalid');
            $(this).val($(this).val().substring(0, 1));
            return;
         }
         else {
             $(this).removeClass('invalid');
        }
    });

    // submit form
    $('form#tooltip-form-int').submit(function() {
        var val = $('input#tooltip-text-int').val().replace(/\s/g, "");
        if (isInteger(val) === false || parseInt(val,0) > 1000 || (val.length > 4)) {
             $('input#tooltip-text-int').toggleClass('invalid');
             return false;
        }
        // ok
        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, val, val);
        return false;
    });
};

/* Heihght form */
CloudyFormBuilder.prototype.heightForm = function() {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-small');

    var view = {
        val: this.td.html(),
        log_id: logId,
        title: this.td.attr('ctitle')
    };
    var html = Mustache.to_html(this.intFormTemplate, view);
    this.tooltip.html("<p>"+ html +"</p>");
    $('input#tooltip-text-int').focus();
    // int only
    $('input#tooltip-text-int').bind('change, keyup', function(){
         var currentCount = $(this).val().length;
         if (currentCount >= 4 || parseInt($(this).val(),0) > 9999) {
            $(this).addClass('invalid');
            $(this).val($(this).val().substring(0, 1));
            return;
         }
         else {
             $(this).removeClass('invalid');
        }
    });

    // submit form
    $('form#tooltip-form-int').submit(function() {
        var val = $('input#tooltip-text-int').val().replace(/\s/g, "");
        if (isInteger(val) === false || parseInt(val,0) > 1000 || (val.length > 4)) {
             $('input#tooltip-text-int').toggleClass('invalid');
             return false;
        }
        // ok
        $("#ajax-loading").show();

        var real_val = height_formatting.output(val);
        instance.updateLog($(this), logId, field, real_val, val);
        return false;
    });
};


/*
    Float form for tenth time input
*/
CloudyFormBuilder.prototype.floatTenthForm = function() {
    // number regexp
    var reg = new RegExp("^[-]?[0-9]*[\.]?[0-9]$");
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-small');

    var view = {
        val: this.td.html(),
        log_id: logId,
        title: this.td.attr('ctitle')
    };

    var html = Mustache.to_html(this.intFormTemplate, view);
    this.tooltip.html("<p>"+ html +"</p>");
    $('input#tooltip-text-int').focus();

    $('input#tooltip-text-int').bind('change, keyup', function(){
         var inputVal = $(this).val();
         if (reg.test(inputVal) === false) {
            $(this).addClass('invalid');
            $(this).val(inputVal);
            return;
         }
         else {
             $(this).removeClass('invalid');
        }
    });

    // submit form
    $('form#tooltip-form-int').submit(function() {
        var val = $('input#tooltip-text-int').val().replace(/\s/g, "");
        if (reg.test(val) === false) {
             $('input#tooltip-text-int').toggleClass('invalid');
             return false;
        }
        // ok now convert this time from tenth to minute
        var minutes = tenth.input(val);
        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, minutes, val);
        return false;
    });
};


/*
    Splited float tenth form FCL 1080
*/

CloudyFormBuilder.prototype.splitedFloatTenthForm = function(fulltime, datatarget) {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  datatarget;
    var timetype = 'min';
    if (instance.td.hasClass('hour')) {
        timetype = 'hour';
    }
    var idChuncks = instance.td.attr('id').split('_');
    var rowpos = idChuncks[0].substring(1);
    var colpos = idChuncks[1].substring(1);

    var reg = new RegExp("^[-]?[0-9]*[\.]?[0-9]$");

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-small');

    var view = {
        val: fulltime,
        log_id: logId,
        title: this.td.attr('ctitle')
    };

    var html = Mustache.to_html(this.intFormTemplate, view);
    this.tooltip.html("<p>"+ html +"</p>");
    $('input#tooltip-text-int').focus();

    $('input#tooltip-text-int').bind('change, keyup', function(){
         var inputVal = fulltime;
         if (reg.test(inputVal) === false) {
            $(this).addClass('invalid');
            $(this).val(inputVal);
            return;
         }
         else {
             $(this).removeClass('invalid');
        }
    });

    // submit form
    $('form#tooltip-form-int').submit(function() {
        var val = $('input#tooltip-text-int').val().replace(/\s/g, "");
        if (reg.test(val) === false) {
             $('input#tooltip-text-int').toggleClass('invalid');
             return false;
        }
        // ok now convert this time from tenth to minute
        var minutes = tenth.input(val);
        var hval = val.split('.')[0];
        var mval = val.split('.')[1];
        // update td fulltime attribute with full time value
        instance.td.attr('fulltime', val);

        // the string we want to update is either minval or hourval
        var targetId = '';
        if (timetype === 'hour') {
            val = hval;
            // It is hour so we need to update min cell as well
            targetId = "r" + rowpos + "_c" + (parseInt(colpos,10)+1);
            $('td#'+targetId).html(mval);
        }
        else {
            val = mval;
            targetId = "r" + rowpos + "_c" + (parseInt(colpos,10)-1);
            $('td#'+targetId).html(hval);
        }

        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, minutes, val);
        return false;
    });
};


/*
    Select input form for an edit inle log entry
*/

CloudyFormBuilder.prototype.selectForm = function(curChoice, choices) {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-small');
    var view = {
        title: this.td.attr('ctitle'),
        options: choices,
        current: curChoice,
        val: 'foo',
        log_id: logId
    };

    var html = Mustache.to_html(this.selectFormTemplate, view);
    this.tooltip.html("<p>"+ html +"</p>");
    $('input#tooltip-select').focus();

    // submit form
    $('form#tooltip-form-select').submit(function() {
        var val = $('select#tooltip-select').val();
        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, val, val);
        return false;
    });
};

/*
  Text Area
*/
CloudyFormBuilder.prototype.textAreaForm = function(realContent, maxchar, prevmax) {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-textarea');
    var currentCount = '';
    try {
         currentCount = realContent.length;
    }
    catch (e) {}

    var view = {
        val: realContent,
        log_id: logId,
        max: maxchar,
        currentCount: currentCount
     };

    var html = Mustache.to_html(this.textAreamTemplate, view);
    this.tooltip.html("<p>"+ html +"</p>");
    $('textarea#tooltip-textarea').focus().val($('textarea#tooltip-textarea').val());
    // listen to change and increment counter
    $('textarea#tooltip-textarea').bind('change, keyup', function(){
         var currentCount = $(this).val().length;
         if (currentCount >= maxchar + 1) {
            $(this).addClass('invalid');
            $(this).val($(this).val().substring(0, maxchar));
            return;
         }
         else {
            $('#tooltip-char-count').html(currentCount);
            $(this).removeClass('invalid');
        }
    });

    // submit form
    $('form#tooltip-form-tarea').submit(function() {
        var val = $('textarea#tooltip-textarea').val();
        // get a mini version for the td content and put the real content
        // in pre.
        var realContent = instance.td.children('pre').html();

        var miniVal = val.substring(val, prevmax) + '...';
        // resize textare content depending on max displayable size
        if (val.length > prevmax) {
            instance.td.html(miniVal);
        }
        else {
            instance.td.html(val);
        }
        var newTxtAreaVal = miniVal + "<pre>" + val + "</pre>";
        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, val, newTxtAreaVal);
        return false;
    });
};

/*
   Media Upload Form
*/

CloudyFormBuilder.prototype.upMediaForm = function(mediaList) {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    instance.tooltip.removeClass();
    instance.tooltip.addClass('tooltip-textarea');
    var view = {
        log_id: logId,
        mediaList: mediaList
    };
    var html = Mustache.to_html(this.textMediaTemplate, view);
    this.tooltip.html("<p>"+ html +"</p>");

    var postUrl = logbookRootUrl + logbookId + "/log/" + logId + "/";

    var uploader = new qq.FileUploader({
        element: document.getElementById('file-uploader'),
        action: postUrl,
        sizeLimit: 3000000,
        params: {'field': field },
        onSubmit: function(file, ext) {
             $("#ajax-loading").show();
        },
        onComplete: function(id, fileName, data){

             if (data.success === true) {
                 $("ul.media").append("<li><a href='"+ data.data.url + "' target='_blank' >" + data.data.fname + "</a><span>" + data.data.size +"  Kb</span></li>");
            }
            else {
                cloudy.create_flash(data.msg, "warning");
                cloudy.show_pending_flash();
             }
             $("#ajax-loading").hide();

        }

    });


};


/*
   Text input form for an edit inline log entry
*/
CloudyFormBuilder.prototype.textForm = function(ltype, maxchar, prevmax, realContent) {
    var instance = this;
    var logId =  instance.td.parent().attr('alt');
    var field =  instance.td.attr("data-field");

    instance.tooltip.removeClass();
    if (ltype =="long")
        instance.tooltip.addClass('tooltip-long');
    else
        instance.tooltip.addClass('tooltip-medium');

    var view = {
        val: realContent,
        log_id: logId,
        max: maxchar,
        currentCount: realContent.length
    };

    var html = Mustache.to_html(this.txtFormTemplate, view);
    this.tooltip.html("<p>"+ html + "</p>");
    $('input#tooltip-text-input').focus().val(realContent);
    // listen to change and increment counter
    $('input#tooltip-text-input').bind('change, keyup', function(){
         var currentCount = $(this).val().length;
         if (currentCount >= maxchar + 1) {
            $(this).addClass('invalid');
            $(this).val($(this).val().substring(0, maxchar));
            return;
         }
         else {
            $('#tooltip-char-count').html(currentCount);
            $(this).removeClass('invalid');
        }
    });

    // submit form
    $('form#tooltip-form').submit(function() {
        var val = $('input#tooltip-text-input').val();
        var realContent = instance.td.children('pre').html();
        var miniVal = val.substring(val, prevmax) + '';
        // resize  content depending on max displayable size
        if (val.length > prevmax) {
            instance.td.html(miniVal);
            miniVal += '...';
        }
        else {
            instance.td.html(val);
        }

        var newTxtVal = miniVal + "<pre>" + val + "</pre>";
        $("#ajax-loading").show();
        instance.updateLog($(this), logId, field, val, newTxtVal);
        return false;




    });
};

$(document).ready(function() {

    /* Trigger on log delete bin icon Do an */
    $("div.log-actions a.delete-log").click(function() {
        var lid = $(this).parent().parent().attr("target");
        var input_box=confirm("Voulez vous vraiment effacer ce log");
        var postUrl = logbookRootUrl + logbookId + "/log/" + lid + "/del/";

        if (input_box===true) {
            $.ajax({
                type: "POST",
                url: postUrl,
                success: function(data) {
                    // reload page
                    location.reload();
                }
            });

         }
         return false;
    });

    /* Default text on forms */
   $(".defaultText").focus(function(srcc)  {
        if ($(this).val() == $(this)[0].title)
        {
            $(this).removeClass("defaultTextActive");
            $(this).val("");
        }
    });
    $(".defaultText").blur(function()  {
        if ($(this).val() === "")
        {
            $(this).addClass("defaultTextActive");
            $(this).val($(this)[0].title);
        }
    });
    $(".defaultText").blur();


    /* Add log book form */
    $('form#add-logbooks-form').submit(function() {
        //update hidden inputs if their li container has class on
        $('ul.select-fly-type li.on').each(function(){
           $("input:hidden", this).each(function(){
                $(this).attr('value', "1");
             });
        });
        $(this).submit();
    });

    /* date sticker table on right page */
    $('table.cright tbody tr').hover(
        function () {
            var position = $(this).offset();
            if ($(this).hasClass("blue")) {
                $("div.date-slip").css('background', '#edf5f8');
            }
            else {
                $("div.date-slip").css('background', '#fff');
            }
            var currentDate = $(this).children(':first-child').attr('alt');
            // no date ? we hide and return
            if (typeof(currentDate)=="undefined") {
                 $("div.date-slip").hide();
                return;
            }
            // else we show a date reminder
            var cdSplit = currentDate.split(' ');
            $("div.date-slip").html("<span>"+ cdSplit[0] + "<b>" + cdSplit[1] + "</b></span>");
            $("div.date-slip").css('top', position.top);
            $("div.date-slip").show();

        },
        function () {
         // discard
        }
    );
    /* right edit/delete button on each populated row */
     $('table.cleft tbody tr, table.cright tbody tr').hover(
        function () {
            var position = $(this).offset();
            var currentDate = $(this).children(':first-child').attr('alt');
            // no date ? we hide and return
            if (typeof(currentDate)==="undefined") {
                 $("div.log-actions").hide();
                 return;
            }
            // $("div.edit-slip").html("FOO");
            $("div.log-actions").css('top', position.top);
            $("div.log-actions").show();
            // update edit link
            // get current log id
            var logId = $(this).attr('alt');
            var postUrl = logbookRootUrl + logbookId + "/log/" + logId + "/";
            if (logbookPage !== "") {
                postUrl = postUrl + "?p=" + logbookPage;
            }
            /* Set target logid so that it can be used by delete action */
            $("div.log-actions").attr('target', logId);
            $("div.log-actions div.edit").html("<a href='" + postUrl + "' class='btn-mini red edit-trigger'> Editer </a>");
          }
    );

    /* On edit click we show a spin */
    $('.edit-trigger').live('click', function() {
            $(this).html("<img src='/static/img/ajax-loader-red.gif' alt='loading' />");
     });

    /* re eddit tooltips */
    // Use each method to gain access to all youtube links

    var tooltip = $("#tooltip");
    var api = tooltip.overlay({
        // custom top position
        top: 0,
         // some mask tweaks suitable for facebox-looking dialogs
        mask: {
            // you might also consider a "transparent" color for the mask
            color: '#fff',
            // load mask a little faster
            loadSpeed: 0,
            // very transparent
            opacity: 0
        },
        fixed: false,
        speed: 0,
        // disable this for modal dialog-type of overlays
        closeOnClick: true
    });



    $('table td.tltext, table td.tmtext, table td.tselect, table tbody td.ttime_0, \
        table tbody td.ttime,  table tbody td.ttime_1,  table tbody td.ttime_2, \
         table tbody td.ttime_splited_0, table tbody td.ttime_splited_1, \
         table tbody td.height_0, table tbody td.height_1, \
         table td.tdate, table td.tint, table td.tint_min, table td.ttextarea, table td.tmedia').click(function() {
         api.overlay().close();
         var height = $(window).height();
         var scrollTop = $(window).scrollTop();
         var offset = $(this).offset();
         var position = $(this).position();
         api.overlay().getConf().top = offset.top - scrollTop +20 ;
         // get pop up size
         var popWidth = 110;
         if ($(this).hasClass('tltext') || $(this).hasClass('ttextarea')  || $(this).hasClass('tmedia')) {
            popWidth = 240;
         }
         else if ($(this).hasClass('tmtext')) {
            popWidth = 170;
         }

         api.overlay().getConf().left = position.left + ($(this).width()/2 - popWidth/2);

         // instantiate a form builder
         cloudyFormBuilder = new CloudyFormBuilder($(this), api.overlay(), tooltip);
         api.overlay().load();

         var prevmax;
         var fulltime;
         var datatarget;
         var realContent;
         var max;

         /* ttime_0 is hh:mm format  whitle ttime_1 & ttime_2 are decimal
         BAD !!! TODO class with method
         */
         if ($(this).hasClass('ttime_0')) {
             cloudyFormBuilder.timeForm();
         }
         if ($(this).hasClass('ttime')) {
             cloudyFormBuilder.timeForm();
         }
         else if ($(this).hasClass('ttime_1')) {
             cloudyFormBuilder.floatTenthForm();
         }
         else if ($(this).hasClass('ttime_2')) {
             cloudyFormBuilder.floatTenthForm();
         }
         else if ($(this).hasClass('height_0')) {
             cloudyFormBuilder.heightForm();
         }
         else if ($(this).hasClass('height_1')) {
             cloudyFormBuilder.heightForm();
         }
         else if ($(this).hasClass('ttime_splited_0')) {
             fulltime = $(this).attr('fulltime');
             datatarget = $(this).attr('target');
             cloudyFormBuilder.splitedTimeForm(fulltime, datatarget);
         }
         else if ($(this).hasClass('ttime_splited_1')) {
             fulltime = $(this).attr('fulltime');
             datatarget = $(this).attr('target');
             cloudyFormBuilder.splitedFloatTenthForm(fulltime, datatarget);
         }
         else if ($(this).hasClass('tltext')) {
             realContent = $(this).children('pre').html();
             max = parseInt($(this).attr('alt'), 10);
             prevmax = parseInt($(this).attr('prevmax'), 10);
             cloudyFormBuilder.textForm("medium", max, prevmax, realContent);
             cloudyFormBuilder.textForm("long", max, realContent);
         }
         else if ($(this).hasClass('tmtext')) {
             realContent = $(this).children('pre').html();
             max = parseInt($(this).attr('alt'), 10);
             prevmax = parseInt($(this).attr('prevmax'), 10);
             cloudyFormBuilder.textForm("medium", max, prevmax, realContent);
         }
         else if ($(this).hasClass('tdate')) {
             var currentInputDate = $(this).attr('alt');
             cloudyFormBuilder.dateForm(currentInputDate);
         }
         else if ($(this).hasClass('tint')) {
             cloudyFormBuilder.intForm();
         }
         else if ($(this).hasClass('tint_min')) {
             cloudyFormBuilder.intForm(59);
         }
         else if ($(this).hasClass('tselect')) {
             // fetch string between pre and build a list
             // of choices from it (comma separated)
             var choices = $(this).children('pre').html();
             var curChoice = $.trim($("span", this).html());

             choices = choices.split(",");
             choices.pop();
             $.each(choices, function(i, value) {
                var choiceVal = $.trim(value);
                var selected = '';
                if (choiceVal == curChoice)
                    selected = 'selected';
                choices[i] = {
                    'val': choiceVal,
                    'selected': selected
                };
             });
             cloudyFormBuilder.selectForm(curChoice, choices);
         }
         else if ($(this).hasClass('ttextarea')) {
             realContent = $(this).children('pre').html();
             max = parseInt($(this).attr('alt'), 10);
             prevmax = parseInt($(this).attr('prevmax'), 10);
             cloudyFormBuilder.textAreaForm(realContent, max, prevmax);
         }
         else if ($(this).hasClass('tmedia')) {
             var mediaList = $(this).children('pre').html();
             cloudyFormBuilder.upMediaForm(mediaList);
         }

     });

});


$(document).ready(function(){
    report_times_update();

});
