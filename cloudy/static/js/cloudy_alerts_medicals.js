function get_qualifications_list(call) {
    $.ajax({
        url: "/alerts/data/medicals/",
        cache: true,
        dataType: 'json',
        success: function(data){
            $("#select_qualif option").remove();
            $("#select_qualif").append("<option value='none'>---</option>");
            for (var index in data) {
                var element = data[index];
                $("#select_qualif").append("<option value='"+element.pk+"'>"+element.fields.name+"</option>");
            }
            $('.select_qualif').show();
            // Call uniform again when we need proper look and feel update...
            $.uniform.update();
            if (call != undefined) { call(); }
         }
    });
}


function initialize() {
    /* If we are in the case of an edit, we have to preload the select fields
     * dynamically.
     * The `EDIT`, `ORIG_SUBTYPE`, `ORIG_TYPE` and `ORIG_ID` variables ared
     * defined in the main template. Yeah that's ugly. */
    if (EDIT == true) {
        /* OK the following is somewhat LISP-style, but it's easily
         * understandable (like LISP btw). We just chain the actions using
         * callbacks. See get_* implementations. */

        /* Initialize the qualification selector (the three selects). */
        get_qualifications_list(function(){
        set_qualif(ORIG_ID);

        /* Fill the corresponding qualification ID */
        $('#id_qualif_uid').val(ORIG_ID);

        /* Display or hide the date fields if needed (with expiration, without
         * and so on...)*/
        swap_date_fields();

        /* Check the boxes if some alerts are already set up. */
        $("id_email_alert").attr('checked', ORIG_EMAIL_ALERT);
        $("id_sms_alert").attr('checked', ORIG_SMS_ALERT);

        /* Fill the corresponding number of days before the expiration. */
        if (ORIG_DAYS_BEFORE != null) {
            $('#id_alert_days_before option').attr('selected', '');
            $('#id_alert_days_before option[value='+ORIG_DAYS_BEFORE+']').attr('selected', 'selected');
        }

        /* Let's update the UI... */
        $.uniform.update();
        });
    }
    /* Otherwise it's just an empty form so we just get the subtype. */
    else {
        get_qualifications_list();
    }
}


function bindings() {
    /* Set the form as a qualification form. */
    $('#id_qualif_categ').val('medical');

    /* Bind changes events */
    $("#select_qualif").change(function(){
        var uid = $("#select_qualif option:selected").val();
        if (uid != 'none') {
            get_qualification();
            //reset_expiry();
        }
    });
}
