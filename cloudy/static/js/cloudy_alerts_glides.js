
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
    var categ = $('#select_subtype option:selected').val();

    $.ajax({
        url: "/alerts/data/glides_list/",
        cache: true,
        dataType: 'json',
        data: {
            categ: categ
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

    $('a.delete').click(function() {
        return confirm($(this).attr('rel'));
    });

    /* Bind changes events */
    $('#select_subtype').change(function(){
        var subtype = $("#select_subtype option:selected").val();
        if (subtype == 'none') {
            $('.select_type').hide();
            $('#select_type option').attr('selected', '');
            $('#select_type option[value=0]').attr('selected', 'selected');
        }
        else {
            get_qualifications_list();
        }
    });
    $('#select_type').change(function(){
        var uid = $('#select_type option:selected').val();
    });

    $('form').submit(function(event){
        var exp_int = $("#id_experience_int").val()
        var exp_unity = $("#id_experience_unity").val()
        var dur_int = $("#id_duree_int").val();
        var dur_unity = $("#id_duree_unity").val();
        error = document.getElementById("correctqualif");

        if (error != null)
            error.remove();

        if (exp_int == "" || dur_int == ""){
            $('.submit').before("<p id='correctqualif' class='error'>Tous les champs doivent être remplis.</p>");
            return false;
        }

        if ((parseInt(dur_int) < 31 && dur_unity == "jour") || (parseInt(dur_int) > 99 && dur_unity == "année")){
            $('.submit').before("<p id='correctqualif' class='error'>Veuillez choisir une date compris entre 31 jours et 99 ans.</p>");
            return false;
        }

        if (parseInt(dur_int) > 99){
            $('.submit').before("<p id='correctqualif' class='error'>La durée ne peut dépasser 99.</p>");
            return false;
        }

        var subtype = $("#id_subtype").val();
        var logbook = $("#select_name option:selected").attr('name');

        switch (subtype) {
            case "plane":
                if (logbook != "plane_dgac" && logbook != "plane_fcl1080"){
                    $('.submit').before("<p id='correctqualif' class='error'>La certification choisie est pour avion. Veuillez sélectionner un carnet Avion DGAC ou FCL.</p>");
                    return false;
                }
                break;
            case "glider":
                if (logbook != "glider_dgac"){
                    $('.submit').before("<p id='correctqualif' class='error'>La certification choisie est pour planeur. Veuillez sélectionner un carnet Planeur.</p>");
                    return false;
                }
                break;
            case "copter":
                if (logbook != "helicopter_dgac"){
                    $('.submit').before("<p id='correctqualif' class='error'>La certification choisie est pour hélicoptère. Veuillez sélectionner un carnet Hélicoptère.</p>");
                    return false;
                }
                break;
            case "ulm":
                if (logbook != "ulm_ffplum"){
                    $('.submit').before("<p id='correctqualif' class='error'>La certification choisie est pour avion. Veuillez sélectionner un carnet Avion DGAC ou FCL.</p>");
                    return false;
                }
                break;
            case "para":
                if (logbook != "parachute_cloudy"){
                    $('.submit').before("<p id='correctqualif' class='error'>La certification choisie est pour parachute. Veuillez sélectionner un carnet Parachute.</p>");
                    return false;
                }
                break;
        }

        if (exp_unity == "vol" && logbook == "glider_dgac"){
            $('.submit').before("<p id='correctqualif' class='error'>Le nombre de vol n'est pas calculé pour des carnets de vol Planeur.</p>");
            return false;
        }
    });

    $("#id_subtype").change(function(){
        qualif_list_choice();
    });

    $(document).ready(function(){
        $("#id_logbook_name").val("auto");
        $("#id_qtype").val("auto");
        $("#id_qgtype_plane").parent().attr("style", "position: absolute; z-index: 5;");
        $("#id_qgtype_glider").parent().attr("style", "position: absolute; z-index: 4;");
        $("#id_qgtype_helico").parent().attr("style", "position: absolute; z-index: 3;");
        $("#id_qgtype_ulm").parent().attr("style", "position: absolute; z-index: 2;");
        $("#id_qgtype_parachute").parent().attr("style", "position: absolute; z-index: 1;");

        $("#id_experience_int, #id_duree_int").attr("style", "margin-top: 12px;");
        $("#uniform-id_experience_unity, #uniform-id_duree_unity").attr("style", "margin-top: 0px;");

        if (EDIT) {
            var certif = $("#"+$("#qualif_id").attr('name')).find('h2').attr('name');
            $("#id_subtype option").attr('selected', '');
            $("#id_subtype option[value='"+certif+"'").attr('selected', 'selected');
            certif = $("#id_subtype option:selected").text();
            $("#uniform-id_subtype").children('span').text(certif);

            qualif_list_choice();
            var qualif = $("#"+$("#qualif_id").attr('name')).find('h2').text();
            var categ = $("#id_subtype").val();
            switch (categ) {
                case "plane":
                    $("#id_qgtype_plane option").attr('selected', '');
                    $("#id_qgtype_plane option[value='"+qualif+"'").attr('selected', 'selected');
                    $("#uniform-id_qgtype_plane").children('span').text(qualif);
                    break;
                case "glider":
                    $("#id_qgtype_glider option").attr('selected', '');
                    $("#id_qgtype_glider option[value='"+qualif+"'").attr('selected', 'selected');
                    $("#uniform-id_qgtype_glider").children('span').text(qualif);
                    break;
                case "copter":
                    $("#id_qgtype_helico option").attr('selected', '');
                    $("#id_qgtype_helico option[value='"+qualif+"'").attr('selected', 'selected');
                    $("#uniform-id_qgtype_helico").children('span').text(qualif);
                    break;
                case "ulm":
                    $("#id_qgtype_ulm option").attr('selected', '');
                    $("#id_qgtype_ulm option[value='"+qualif+"'").attr('selected', 'selected');
                    $("#uniform-id_qgtype_ulm").children('span').text(qualif);
                    break;
                case "para":
                    $("#id_qgtype_parachute option").attr('selected', '');
                    $("#id_qgtype_parachute option[value='"+qualif+"'").attr('selected', 'selected');
                    $("#uniform-id_qgtype_parachute").children('span').text(qualif);
                    break;
            }
            $("#id_qgty option").attr('selected', '');
            $("#select_name option[value='"+name+"'").attr('selected', 'selected');
            $("#uniform-select_name").children('span').text(name);

            var name = $("#"+$("#qualif_id").attr('name')).find('strong').text();
            $("#select_name option").attr('selected', '');
            $("#select_name option[value='"+name+"'").attr('selected', 'selected');
            $("#uniform-select_name").children('span').text(name);
        }
    });
}

function qualif_list_choice() {
    var categ = $("#id_subtype").val();
    switch (categ) {
        case "plane":
            $("#id_qgtype_plane").parent().attr("style", "position: absolute; z-index: 5;");
            $("#id_qgtype_plane").attr("name", "qtype");
            $("#id_qgtype_glider").parent().attr("style", "position: absolute; z-index: 4;");
            $("#id_qgtype_glider").attr("name", "qtype1");
            $("#id_qgtype_helico").parent().attr("style", "position: absolute; z-index: 3;");
            $("#id_qgtype_helico").attr("name", "qtype1");
            $("#id_qgtype_ulm").parent().attr("style", "position: absolute; z-index: 2;");
            $("#id_qgtype_ulm").attr("name", "qtype1");
            $("#id_qgtype_parachute").parent().attr("style", "position: absolute; z-index: 1;");
            $("#id_qgtype_parachute").attr("name", "qtype1");
            break;
        case "glider":
            $("#id_qgtype_plane").parent().attr("style", "position: absolute; z-index: 4;");
            $("#id_qgtype_plane").attr("name", "qtype1");
            $("#id_qgtype_glider").parent().attr("style", "position: absolute; z-index: 5;");
            $("#id_qgtype_glider").attr("name", "qtype");
            $("#id_qgtype_helico").parent().attr("style", "position: absolute; z-index: 3;");
            $("#id_qgtype_helico").attr("name", "qtype1");
            $("#id_qgtype_ulm").parent().attr("style", "position: absolute; z-index: 2;");
            $("#id_qgtype_ulm").attr("name", "qtype1");
            $("#id_qgtype_parachute").parent().attr("style", "position: absolute; z-index: 1;");
            $("#id_qgtype_parachute").attr("name", "qtype1");
            break;
        case "copter":
            $("#id_qgtype_plane").parent().attr("style", "position: absolute; z-index: 3;");
            $("#id_qgtype_plane").attr("name", "qtype1");
            $("#id_qgtype_glider").parent().attr("style", "position: absolute; z-index: 4;");
            $("#id_qgtype_glider").attr("name", "qtype1");
            $("#id_qgtype_helico").parent().attr("style", "position: absolute; z-index: 5;");
            $("#id_qgtype_helico").attr("name", "qtype");
            $("#id_qgtype_ulm").parent().attr("style", "position: absolute; z-index: 2;");
            $("#id_qgtype_ulm").attr("name", "qtype1");
            $("#id_qgtype_parachute").parent().attr("style", "position: absolute; z-index: 1;");
            $("#id_qgtype_parachute").attr("name", "qtype1");
            break;
        case "ulm":
            $("#id_qgtype_plane").parent().attr("style", "position: absolute; z-index: 2;");
            $("#id_qgtype_plane").attr("name", "qtype1");
            $("#id_qgtype_glider").parent().attr("style", "position: absolute; z-index: 4;");
            $("#id_qgtype_glider").attr("name", "qtype1");
            $("#id_qgtype_helico").parent().attr("style", "position: absolute; z-index: 3;");
            $("#id_qgtype_helico").attr("name", "qtype1");
            $("#id_qgtype_ulm").parent().attr("style", "position: absolute; z-index: 5;");
            $("#id_qgtype_ulm").attr("name", "qtype");
            $("#id_qgtype_parachute").parent().attr("style", "position: absolute; z-index: 1;");
            $("#id_qgtype_parachute").attr("name", "qtype1");
            break;
        case "para":
            $("#id_qgtype_plane").parent().attr("style", "position: absolute; z-index: 1;");
            $("#id_qgtype_plane").attr("name", "qtype1");
            $("#id_qgtype_glider").parent().attr("style", "position: absolute; z-index: 4;");
            $("#id_qgtype_glider").attr("name", "qtype1");
            $("#id_qgtype_helico").parent().attr("style", "position: absolute; z-index: 3;");
            $("#id_qgtype_helico").attr("name", "qtype1");
            $("#id_qgtype_ulm").parent().attr("style", "position: absolute; z-index: 2;");
            $("#id_qgtype_ulm").attr("name", "qtype1");
            $("#id_qgtype_parachute").parent().attr("style", "position: absolute; z-index: 5;");
            $("#id_qgtype_parachute").attr("name", "qtype");
            break;
    }
}
