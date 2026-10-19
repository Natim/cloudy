/*JSHINT */
/*global $: true */

var cloudy = {
    share: function(service, values) {
        if (service == "twitter") {
            window.open('http://twitter.com/home?status='+ encodeURIComponent(values.tweet), 'sharer', 'toolbar=0, status=0, width=860 height=550');
        }
        if (service == "facebook") {
            var leftVal =(screen.width) / 2;
            var topVal = (screen.height) / 2;
            window.open('https://www.facebook.com/sharer.php?u='+ encodeURIComponent(values.url)+
                '&t='+encodeURIComponent(values.title), 'sharer', 'toolbar=0, status=0, width=626, height=436');
        }
    },

    /* Show pending flash messages */
    show_pending_flash: function() {

      $("div#top-notif").css({zIndex:99,  top: "20px"}).delay(5000).fadeOut("fast");

      /* Flash messages */
      /*
      $("div#top-notif").animate({
        top: "20px"
      }, 500 ).css({zIndex:99}).delay(5000).animate({
        top: "-60px"
      }, 100 ).fadeOut("fast")*/
    },

    /* Create a flash message */
    create_flash: function(msg, type) {
       $("div#top-notif").remove();
       $("div#wrap").append("<div id='top-notif'></div>");
       $("div#top-notif").append("<div class='notif " + type + "'>" + msg + "</div>");
       $('html, body').animate({scrollTop:0}, 'fast');

    },

    /* Reset form */
    reset_form: function(form_target) {
        // Use a whitelist of fields to minimize unintended side effects.
      $(':text, :password, :file', form_target).val('');
      // De-select any checkboxes, radios and drop-down menus
      $(':input', '#myFormId').removeAttr('checked').removeAttr('selected');

    },

    /* Textare char counts */
    update_count_chars_message:  function(textarea, counter, max) {
      var chars_left = max - textarea.val().length;
      if (chars_left < 0) {
          counter.addClass("error-message");
      } else {
          counter.removeClass("error-message");
      }
      counter.html(chars_left);
    }




};

/* JQUERY TOOL POPUPS */
$(function() {

  // loading animation
  $.tools.overlay.addEffect("drop", function(css, done) {
       // use Overlay API to gain access to crucial elements
       var conf = this.getConf(),
       overlay = this.getOverlay();

       // position the overlay and show it
       overlay.css(css).show();
       overlay.css({left: '50%'});
       // begin animating with our custom easing
       overlay.animate({ opacity: 1}, 0);

       /* closing animation */
       }, function(done) {
          this.getOverlay().animate({top:'-=55', opacity:0}, 0, function() {
             $(this).hide();
             done.call();
          });
       }
    );

    $("div#video-cont a[rel]").overlay({
        // one configuration property
        effect: 'drop',
        mask: {
            color: '#000',
            loadSpeed: 200,
            opacity: 0.5
        },
        top: 300,

        onClose: function() {
            // for reaload of video iframe (ie8)
            var vsrc = $('#vimeo-iframe').html();
            $('#vimeo-iframe iframe').remove();
            $('#vimeo-iframe').html(vsrc);
         }
    });



    // First class only Popup for unavailable links when user
    // has an eco pack
    var overlay_conf = {
        effect: 'drop',
        mask: {
            color: '#000',
            loadSpeed: 200,
            opacity: 0.5,
        },
        top: 300,
    };

    $("#fc-only-popup").overlay(overlay_conf);
    $("#fc-only-popup-stats").overlay(overlay_conf);

    $("#top-bar .hidden").overlay(overlay_conf);
    $("#zendesk_button").overlay(overlay_conf);


    $("a.unavailable#galertes").overlay(overlay_conf);
    $("a.unavailable#logb-stats").overlay(overlay_conf);


});


$(document).ready(function() {


    /* Login form on header */
    $("#wrap-top-head #form-login").validate({
        focusCleanup: true,
        onkeyup: false,
        onsubmit: true,
        errorPlacement: function(error, element) {
             element.addClass("error");
        },
        rules: {
               password: "required",
               username: {
                   required: true,
                   email: true
               }
      }
    });


  cloudy.show_pending_flash();


    $("#wrap-top-head #form-login #email-input").focus(function() {
        if (this.value === 'email') {
             this.value = '';
             $(this).removeClass('default');
        }
    });



    if ( $.browser.msie ) {
       $("select, input:file, input:text").uniform();
    }
    else {
        $("select, input:checkbox, input:radio, input:file, input:text").uniform();
    }
    /* Notices messages */
    $("div.notice a.close").click(function() {
        $(this).parent().fadeOut("fast");
    });

});
