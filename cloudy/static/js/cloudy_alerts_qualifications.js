
function get_subtype(call) {
    $.ajax({
        url: "/alerts/data/sub_type/",
        cache: true,
        dataType: 'json',
        success: function(data){
            $("#select_subtype option").remove();
            $("#select_subtype").append("<option value='none'>---</option>");
            for (var key in data) {
                var element = data[key];
                $("#select_subtype").append("<option value='"+key+"'>"+element+"</option>");
            }
            $('.select_subtype').show();
            // Call uniform again when we need proper look and feel update...
            $.uniform.update();
            if (call != undefined) { call(); }
         }
    });
}


function get_type(call) {
    $.ajax({
        url: "/alerts/data/type/",
        cache: true,
        dataType: 'json',
        success: function(data){
            $("#select_type option").remove();
            $("#select_type").append("<option value='none'>---</option>");
            for (var key in data) {
                var element = data[key];
                $("#select_type").append("<option value='"+key+"'>"+element+"</option>");
            }
            $('.select_type').show();
            // Call uniform again when we need proper look and feel update...
            $.uniform.update();
            if (call != undefined) { call(); }
         }
    });
}


function get_qualifications_list(call) {
    var type = $('#select_type option:selected').val();
    var subtype = $('#select_subtype option:selected').val();

    $.ajax({
        url: "/alerts/data/qualifications_list/",
        cache: true,
        dataType: 'json',
        data: {
            type: type,
            sub_type: subtype
        },
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
        get_subtype(function(){
        set_subtype(ORIG_SUBTYPE);

        get_type(function(){
        set_type(ORIG_TYPE);

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
        });});});
    }
    /* Otherwise it's just an empty form so we just get the subtype. */
    else {
        $('.select_type').hide();
        $('.select_qualif').hide();
        get_subtype();
    }
}


function bindings() {
    /* Set the form as a qualification form. */
    $('#id_qualif_categ').val('qualification');

    /* Bind changes events */
    $('#select_subtype').change(function(){
        var subtype = $("#select_subtype option:selected").val();
        if (subtype == 'none') {
            $('.select_type').hide();
            $('#select_type option').attr('selected', '');
            $('#select_type option[value=0]').attr('selected', 'selected');
        }
        $('.select_qualif').hide();
        $('#select_qualif option').attr('selected', '');
        $('#select_qualif option[value=0]').attr('selected', 'selected');
        get_type(function(){
        set_type('none');
        });
    });
    $('#select_type').change(function(){
        var type = $("#select_type option:selected").val();
        if (type == 'none') {
            $('.select_qualif').hide();
            $('#select_qualif option').attr('selected', '');
            $('#select_qualif option[value=0]').attr('selected', 'selected');
        }
        else {
            get_qualifications_list();
        }
    });
    $("#select_qualif").change(function(){
        var uid = $("#select_qualif option:selected").val();
        if (uid != 'none') {
            get_qualification();
            //reset_expiry();
            $('#correctqualif').remove();
        }
    });
}
