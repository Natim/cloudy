
$(document).ready(function(){


    var mapping = {
        'custom': "Date personalisées",
        'lifetime': "La totalité",
        '6months': "Les 6 derniers mois",
        '2months': "Les 2 derniers mois",
        '3months': "Les 3 derniers mois",
        '1year': "La dernière année"
    }

    /* Make them look like date inputs */
    var date_config = {
        format: 'yyyy/mm/dd',
        selectors: true,
        yearRange: "-80:+01"
    };

//    $("#selector_begin_date").dateinput(date_config);
//    $("#selector_end_date").dateinput(date_config);

    var begin_date_api = $('#selector_begin_date').data('dateinput');
    var end_date_api = $('#selector_end_date').data('dateinput');


    $('.icon-calendar-begin').click(function(){
        begin_date_api.show();
        return false;
    });

    $('.icon-calendar-end').click(function(){
        end_date_api.show();
        return false;
    });


    var select_value = $.getUrlVar('select');

    $('#filter option').attr('selected', '');
    $('#filter option[value="'+select_value+'"]').attr('selected', 'selected');
    $.uniform.update("#filter option");
    $.uniform.update("#filter");

    $('#customrangeselector').hide();


    /* Update the title */
    var begin_date = $.getUrlVar('begin_date');
    var end_date = $.getUrlVar('end_date');


    if (begin_date == undefined && end_date == undefined) {
        $("#date_place_whole").hide();
    }
    else {

        if (begin_date == undefined) {
            $("#begin_date_place").html("Votre premier vol");
        }
        else {
            $("#begin_date_place").html(begin_date);
        }

        if (end_date == undefined) {
            $("#end_date_place").html("Aujourd'hui");
        }
        else {
            var html = end_date;
            if (select_value === 'custom') {
                html += " <a href='' id='change-date'>Changer les dates</a>"
            }
            $("#end_date_place").html(html);
        }

    }

    var s = select_value;
    if (s == undefined) {
        s = "2months";
        // auto select list on 2 months
        $('#filter option[value="2months"]').attr('selected', 'selected');
        $.uniform.update("#filter option");
        $.uniform.update("#filter");
    }

    $("#date_range_place").html(mapping[s]);

    var ovrConf = {
        effect: 'drop',
        api: true,
        mask: {
            color: '#000',
            loadSpeed: 0,
            opacity: 0.4
        },
        top: 300,
        closeOnClick: true,
        load: false
    };
    var custom_api = $('#customrangeselector').overlay(ovrConf);
    $("#change-date").click(function(event) {
        $("#selector_begin_date").val(begin_date);
        $("#selector_end_date").val(end_date);
       custom_api.load();
       return false;
    });

    $('#filter').bind("change select",  function(event){
        var v = $(this).val();
        var url_args = 'none';
        switch(v) {
            case 'lifetime':
                url_args = 'select=lifetime';
                break;
            case '6months':
                var newdate = Date.today().addMonths(-6);
                url_args = 'select=6months&begin_date='+newdate.toString("yyyy/MM/dd");
                break;

            case '3months':
                var newdate = Date.today().addMonths(-3);
                url_args = 'select=3months&begin_date='+newdate.toString("yyyy/MM/dd");
                break;

            case '2months':
                var newdate = Date.today().addMonths(-2);
                url_args = 'select=2months&begin_date='+newdate.toString("yyyy/MM/dd");
                break;

            case '1year':
                var newdate = Date.today().addYears(-1);
                url_args = 'select=1year&begin_date='+newdate.toString("yyyy/MM/dd");
                break;

            case 'custom':
                custom_api.load();
                var select_value = $.getUrlVar('select');

                $('#filter option[value="'+select_value+'"]').attr('selected', 'selected');
                $.uniform.update("#filter option");
                $.uniform.update("#filter");
                // -> return to avoid the window location changed
                return 0;
                break;

            default:
                break;
        }
        window.location = './?' + url_args;
    });



    $('#selector_submit').click(function(){
        var begin_date = $('#selector_begin_date').val();
        var end_date = $('#selector_end_date').val();
        window.location = './?select=custom&'+'begin_date='+begin_date+'&end_date='+end_date;
    });



});
