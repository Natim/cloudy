/*JSHINT */
/*global $: true, cloudy: true */

function checkVoucher(val, orignPrice) {
    var url = "/coupons/" + val + "/check/percent/";
    $.getJSON(url, function(data) {

        if (data.success === true) {
            if (data.data.hasOwnProperty('discount')) {
                $("span#code-status span.discount").html("- " + data.data.discount + " %");
                var newPrice = orignPrice - (orignPrice*(parseInt(data.data.discount,10)/100));
                $("#code-status").show();
                $("div.price span.value").html(Math.round(newPrice/0.5)*0.5);
                // show payment div
                $("div.payment-cont").show();
                $("input#id_pack").val("1");
            }
        }
    });
}

$(document).ready(function() {
        $("a.packbutton#free").click(function(){
            $(this).addClass('hover');
            $("a.packbutton#pay").removeClass('hover');
        });
        $("a.packbutton#pay").click(function(){
            $(this).addClass('hover');
            $("a.packbutton#free").removeClass('hover');
        });

        /* Signup submit */
        $('form#signup-form, form#recharge-fc-form').submit(function(){
            $('p.submit button', this).attr('disabled', 'disabled');
            $("#red-plane").show()
                 .animate({"left": "+=710px"}, 7000, 'linear');
        });

        /* CGVU popup */

        $("a#gcu_link[rel]").overlay({
             api: true,
            mask: {
                color: '#000',
                loadSpeed: 0,
                opacity: 0.4
            },
            top: 300,
            onLoad: function() {
                // get the data
                $.get('/data/cgvu/', function(data) {
                    $('div#gcu-popup.popup textarea').html(data);
                });
            }
        });

});
