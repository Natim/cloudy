function auto_complete_expiry_date() {
    var day = parseInt($('#id_achievement_date_day').val());
    var month = parseInt($('#id_achievement_date_month').val());
    var year = parseInt($('#id_achievement_date_year').val());

    /* We first check that all the achievement selects are selected */
    if (day == 0 || month == 0 || year == 0) {
        return null;
    }

    /* We check we have a duration value */
    var duration = CURRENT_QTYPE.duration;
    console.log("foo");
    console.log(duration);
    if (duration == '0' || duration == '-1') {
        return null;
    }

    /* Duration is formated with /day/month/year */
    var d_split = duration.split('/');
    var p_day = d_split[0] == '' ? 0 : parseInt(d_split[0]);
    var p_month = d_split[1] == '' ? 0 : parseInt(d_split[1]);
    var p_year = d_split[2] == '' ? 0 : parseInt(d_split[2]);

    /* Increment months */
    month = month + p_month;
    if (month > 12) {
        month = month - 12;
        year = year + 1;
    }

    /* Increment years */
    year = year + p_year;

    /* NOTE: we do not increment days: it's a pain in the ass so I won't do it until needed. */

    /* Reset selects */
    $('#id_expiry_date_day option').attr('selected', '');
    $('#id_expiry_date_month option').attr('selected', '');
    $('#id_expiry_date_year option').attr('selected', '');

    /* Update selects */
    $('#id_expiry_date_day option[value='+day+']').attr('selected', 'selected');
    $('#id_expiry_date_month option[value='+month+']').attr('selected', 'selected');
    $('#id_expiry_date_year option[value='+year+']').attr('selected', 'selected');

    /* Uniform... */
    $.uniform.update();

    return 0;
}


function show_expiry() {
    $('#id_expiry_date_day').parent().parent().parent().show();
    $('#id_alert_days_before').parent().parent().parent().show();
    $('#id_alert_days_before').parent().parent().next('.help-field').show();
    $('#id_sms_alert').parent().parent().parent().parent().show()
    $('#id_sms_alert').parent().parent().parent().next('.help-field').show();
    $('#id_email_alert').parent().parent().parent().parent().show()
    $('#id_email_alert').parent().parent().parent().next('.help-field').show();
    $.uniform.update();
}


function reset_expiry() {
    $('#id_expiry_date_day option').attr('selected', '');
    $('#id_expiry_date_month option').attr('selected', '');
    $('#id_expiry_date_year option').attr('selected', '');
    $('#id_expiry_date_day option[value=0]').attr('selected', 'selected');
    $('#id_expiry_date_month option[value=0]').attr('selected', 'selected');
    $('#id_expiry_date_year option[value=0]').attr('selected', 'selected');
    $.uniform.update();
}


function hide_expiry() {
    $('#id_expiry_date_day').parent().parent().parent().hide();
    $('#id_alert_days_before').parent().parent().parent().hide();
    $('#id_alert_days_before').parent().parent().next('.help-field').hide();
    $('#id_sms_alert').parent().parent().parent().parent().hide()
    $('#id_sms_alert').parent().parent().parent().next('.help-field').hide();
    $('#id_email_alert').parent().parent().parent().parent().hide()
    $('#id_email_alert').parent().parent().parent().next('.help-field').hide();
    $('#id_email_alert').attr('checked', false);
    $('#id_sms_alert').attr('checked', false);
    $.uniform.update();
}


function swap_date_fields(duration) {
    if (duration == undefined) {
        duration = CURRENT_QTYPE.duration;
    }
    console.log(duration);
    /* This is a manual input. */
    if (duration == '-1') {
        show_expiry();
    }
    /* No expiry of any kind. */
    else if (duration == "0") {
        hide_expiry();
    }
    else {
        show_expiry();
        //auto_complete_expiry_date();
    }
}


function get_qualification(call) {
    var uid = $('#select_qualif option:selected').val();

    $.ajax({
        url: "/alerts/data/qualification/",
        cache: true,
        dataType: 'json',
        data: {pk: uid},
        success: function(data) {
            CURRENT_QTYPE = data;
            swap_date_fields();
            if (call != undefined) { call(); }
        }
    });
}



function _set_select(name) {
    return function(value){
        /* Reset */
        $('#select_'+name+' option').attr('selected', '');
        /* Set */
        $('#select_'+name+' option[value='+value+']').attr('selected', 'selected');
    };
}
var set_subtype = _set_select('subtype');
var set_type = _set_select('type');
var set_qualif = _set_select('qualif');



$(document).ready(function(){

    bindings();

    /* Hide checkbox for sms and mail alerts */
    var sms_checkbox = document.getElementById("uniform-id_sms_alert").parentNode.parentNode;
    sms_checkbox.setAttribute("style", "position:absolute; visibility:hidden;");
    var mail_checkbox = document.getElementById("uniform-id_email_alert").parentNode.parentNode;
    mail_checkbox.setAttribute("style", "position:absolute; visibility:hidden;");

    /* Bind achievement selects to autocomplete the date */
    $("#id_achievement_date_day, #id_achievement_date_month, #id_achievement_date_year").change(function(){ auto_complete_expiry_date(); });

    /* Bind the form submit to auto complete the hidden form fields. */
    $('form').submit(function(event){
        var uid = $("#select_qualif option:selected").val();
        if (uid == 'none') {
            var error = document.getElementById("correctqualif");
            if (error != null) {
                error.remove();
            }
            $('.submit').before("<p id='correctqualif' class='error'>Vous devez correctement sélectionner une qualification avant de continuer.</p>");
            return false;
        }

        if (uid != 'none') {
            var qualif = $("#select_qualif option:selected").text();
            var title = document.getElementById(qualif);
            var button = document.getElementsByClassName("short")[0].firstChild.data;

            if (button == "Enregistrer" || button == "Register") {
                if (title != null) {
                    title = title.getAttribute("id");
                    error = document.getElementById("correctqualif");
                    if (error != null) {
                        error.remove();
                    }
                    $('.submit').before("<p id='correctqualif' class='error'>Cette qualification existe déjà. Veuillez la modifier ou la supprimer pour en ajouter une nouvelle.</p>");
                    return false;
                }
            }

        }

        $('#id_qualif_uid').val(uid);
    });


    $('a.delete').click(function() {
        return confirm($(this).attr('rel'));
    });

    initialize();
});
