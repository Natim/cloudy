/*JSHINT */
/*global $: true, Chart: true, two_months_before_now: true, format_time: true,
drawHistogram: true, drawPieChart: true */

var cloudyStats = {};

/* Get start/end date form selection & URL vars */
cloudyStats.getBeginEndSelectDateRange = function () {
    var result = {};
    var selected = $.getUrlVar('select');
    var begin_date = $.getUrlVar('begin_date');
    if (begin_date === undefined) begin_date = two_months_before_now();
    if (selected  ===  "lifetime") begin_date = "none";
    var end_date = $.getUrlVar('end_date');
    if (end_date  ===  undefined) end_date = "none";
    result.end_date = end_date;
    result.begin_date = begin_date;
    return result;
};

/* Map */
cloudyStats.map = function (result_id) {
    var payload = {
      begin_date: this.beginDate,
      end_date: this.endDate,
      logbook_id: this.logbookId
    };

    var json_payload = JSON.stringify(payload);

    $.ajax({
        url: '/graphs/map/',
        data: {payload: json_payload},
        dataType: 'json',
        success: function(json_data){

            if (!json_data || json_data.length === 0) {
                $("#"+result_id).html("<p>Aucune des entrées dans votre carnet sur cette période ne contient d'informations de localisation.</p>");
                return 1;
            }

            var map = L.map('map').setView([46.5, 2], 6);

            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                referrerPolicy: 'origin'
            }).addTo(map);

            for (index in json_data) {
                var el = json_data[index];
                var lat = parseFloat(el[0]);
                var lng = parseFloat(el[1]);
                if (isNaN(lat) || isNaN(lng)) {
                    continue;
                }
                var marker = L.marker([lat, lng]).addTo(map);
                marker.bindTooltip(el[2], {permanent: false, direction: 'right'});
            }
        }
    });
}


/* Top 5 Aeronefs  */
cloudyStats.top5Aeronefs = function (totalStr, groupByStr) {
    var payload = {
      begin_date: this.beginDate,
      end_date: this.endDate,
      total: totalStr,
      logbook_id: this.logbookId,
      group_by: groupByStr,
      max: 5
    };
    var myJSONPayload = JSON.stringify(payload);
    $.ajax({
        url: '/graphs/count_foo/',
        data: {payload:myJSONPayload},
        dataType: "json",
        success: function(json_data){
            if (json_data.length > 5) {
                json_data = json_data.slice(0,5);
            }
            for (var index in json_data) {
                var el = json_data[index];
                var time = parseInt(el[1], 10);
                var i = parseInt(index, 10)+1;
                var f = format_time(time);
                // todo: use mustache for rendering or Backbone js one day.
                var classy = "";
                if (i % 2 == 1) {
                    classy = "class='blue-cycle'";
                }
                $("#topaeronef").append("<tr><td "+classy+"><span class='number'>"+i+".</span> "+el[0]+" <span class='hour'>("+f+")</span></td></tr>");
            }

            if (json_data.length < 5) {
                for (var j = 0; j < 5 - json_data.length; j++){
                    var n = json_data.length + j + 1;
                    $("#topaeronef").append("<tr><td><span class='number'>"+n+".</span> --- </td></tr>");
                }
            }
        },
        error: function(){
            $("#topaeronef").append("<tr><td><span class='number'>1.</span> --- </td></tr>");
            $("#topaeronef").append("<tr><td><span class='number'>2.</span> --- </td></tr>");
            $("#topaeronef").append("<tr><td><span class='number'>3.</span> --- </td></tr>");
            $("#topaeronef").append("<tr><td><span class='number'>4.</span> --- </td></tr>");
            $("#topaeronef").append("<tr><td><span class='number'>5.</span> --- </td></tr>");
        }
    });
};

/* Top 5 Airports */

cloudyStats.top5Airports = function () {
   var payload = {
     begin_date: this.beginDate,
     end_date: this.endDate,
     logbook_id: this.logbookId
   };
   var myJSONPayload = JSON.stringify(payload);
   $.ajax({
      url: '/graphs/count_airports/',
      data: {payload:myJSONPayload},
      dataType: "json",
      success: function(json_data){
          var d = json_data;
          for (var index in d) {
              var el = d[index];
              var n = el[1];
              var label = el[0];
              var i = parseInt(index, 10)+1;

              var classy = "";

              if (i % 2 == 1) {
                  classy = "class='blue-cycle'";
              }
              $("#topairports").append("<tr><td "+classy+"><span class='number'>"+i+".</span> "+label+" <span class='hour'>("+n+")</span></td></tr>");
          }

          if (d.length < 5) {
              for (var i = 0; i < 5 - d.length; i++){
                  var n = d.length + i + 1;
                  $("#topairports").append("<tr><td><span class='number'>"+n+".</span> --- </td></tr>");
              }
          }
      },
      error: function(){
          $("#topairports").append("<tr><td><span class='number'>1.</span> --- </td></tr>");
          $("#topairports").append("<tr><td><span class='number'>2.</span> --- </td></tr>");
          $("#topairports").append("<tr><td><span class='number'>3.</span> --- </td></tr>");
          $("#topairports").append("<tr><td><span class='number'>4.</span> --- </td></tr>");
          $("#topairports").append("<tr><td><span class='number'>5.</span> --- </td></tr>");
      }
  });
};


/* Total flight time group by foo */
cloudyStats.FlyTimeBarGraph = function (totalStr, groupByStr) {
   var payload = {
     begin_date: this.beginDate,
     end_date: this.endDate,
     total: totalStr,
     logbook_id: this.logbookId,
     group_by: groupByStr
   };

   var myJSONPayload = JSON.stringify(payload);

    $.ajax({
        url: '/graphs/data/',
        data: {payload:myJSONPayload},
        dataType: "json",
        success: function(json_data) {
            var slot_names = json_data.slices_name;

            var core_data = json_data.data;

             if (core_data.length === 0) {
                $("#placeholdermultiple").html("Aucune donnée à afficher pour le moment.");
                $("#placeholderbars").hide();
                $("#placeholderbars").after("<div class='graph'><p class='text'>Aucune donnée à afficher pour le moment.</p></div>");
                return false;
            }
            drawHistogram("placeholdermultiple", core_data, slot_names, true);

            },
        error: function(){
            $("#placeholdermultiple").html("Aucune donnée à afficher pour le moment.");
        }
    });
};

/* Totals Pie chart */
cloudyStats.TotalsPieChart = function (targetContainer, map, totalsList, filtersList) {
     var payload = {
       begin_date: this.beginDate,
       end_date: this.endDate,
       total: totalsList,
       logbook_id: this.logbookId
      };
     var myJSONPayload = JSON.stringify(payload);

     $.ajax({
          url: '/graphs/data/',
          data: {payload:myJSONPayload},
          dataType: "json",
          success: function(json_data){
              var allEmpty = true;
              $.each(json_data, function(i, val) {
                  if (val!==0) {
                    allEmpty = false;
                  }
              });
              if (allEmpty === true)  {
                  $("#" + targetContainer).html("Aucune donnée à afficher pour le moment.");
                  return false;
              }
              var pieData = [];
              $.each(json_data, function(i, item) {
                  pieData[i]= [map[item.label], item.data];
              });
              drawPieChart(targetContainer, pieData);
          },

          error: function(){
              $("#" + targetContainer).html("Aucune donnée à afficher pour le moment.");
          }
    });
};

/* Group by Pie Chart, instead of aggregating several totals we aggregate unique
values of a given field */

cloudyStats.FieldGroupbyPieChart = function (targetContainer, totalStr, groupByStr, no_format) {
    var do_time_format = true;
    if (no_format == true) {
      do_time_format = false;
    }

   var payload = {
      begin_date: this.beginDate,
      end_date: this.endDate,
      total: totalStr,
      logbook_id: this.logbookId,
      group_by: groupByStr
    };
    var myJSONPayload = JSON.stringify(payload);
    $.ajax({
        url: '/graphs/count_foo/',
        data: {payload:myJSONPayload},
        dataType: "json",
        success: function(json_data){
            drawPieChart(targetContainer, json_data, !do_time_format);
        },
        error: function(){
              $("#" + targetContainer).html("Aucune donnée à afficher pour le moment.");
        }
    });
};

/* Filtered Bar graph */

cloudyStats.FilteredFlyTimeBarGraph = function (targetContainer, total, filtersList) {
    var payload = {
     begin_date: this.beginDate,
     end_date: this.endDate,
     total: total,
     logbook_id: this.logbookId,
     filters: filtersList
    };
    var myJSONPayload = JSON.stringify(payload);
    $("#"+targetContainer).html("Chargement...");

    $.ajax({
        url: '/graphs/data/',
        data: {payload:myJSONPayload},
        dataType: "json",
        success: function(json_data){
            var slot_names = json_data['slices_name'];
            var core_data = json_data['data'];
            $("#reminder-total-hdv").html(format_time(json_data['total']));

            // Show total near title
              if (core_data.length === 0) {
                $("#"+targetContainer).html("Aucune donnée à afficher pour le moment.");
                $("#"+targetContainer).hide();
                $("#"+targetContainer).after("<div class='graph'>Aucune donnée à afficher pour le moment.</div>");
                return false;
            }
             drawHistogram(targetContainer, core_data, slot_names, false);
        },
        error: function(){
            $("#"+targetContainer).html("Aucune donnée à afficher pour le moment.");
        }
    });
};

/* Filtered Bar graph for non time data (parachute) */

cloudyStats.FilteredIntBarGraph = function (targetContainer, total, filtersList) {
    var payload = {
     begin_date: this.beginDate,
     end_date: this.endDate,
     total: total,
     logbook_id: this.logbookId,
     filters: filtersList
    };
    var myJSONPayload = JSON.stringify(payload);
    $("#"+targetContainer).html("Chargement...");

    $.ajax({
        url: '/graphs/data/',
        data: {payload:myJSONPayload},
        dataType: "json",
        success: function(json_data){
            var slot_names = json_data['slices_name'];
            var core_data = json_data['data'];
            $("#reminder-total-hdv").html(json_data['total']);

            // Show total near title
              if (core_data.length === 0) {
                $("#"+targetContainer).html("Aucune donnée à afficher pour le moment.");
                $("#"+targetContainer).hide();
                $("#"+targetContainer).after("<div class='graph'>Aucune donnée à afficher pour le moment.</div>");
                return false;
            }
             drawHistogram(targetContainer, core_data, slot_names, false, true, "Nombre de sauts");
        },
        error: function(){
            $("#"+targetContainer).html("Aucune donnée à afficher pour le moment.");
        }
    });
};

/* Fetch filter choices from mode fields */
cloudyStats.getFilterChoices = function (fieldsList) {
    var payload = {
      begin_date: this.beginDate,
      end_date: this.endDate,
      logbook_id: this.logbookId,
      fields: fieldsList
    };
    var myJSONPayload = JSON.stringify(payload);
    $.ajax({
          url: '/graphs/get_choices/',
          data: {payload:myJSONPayload},
          dataType: "json",
          success: function(json_data){
              for (var index in json_data) {
                  var select = $("select[target-field="+index+"]");
                  select.html("");
                  select.append("<option value='__all__'>Tous</option>");
                  $.uniform.update(select);
                  for (var index2 in json_data[index]) {
                      var v = json_data[index][index2];
                      select.append("<option value='"+v+"'>"+v+"</option>");
                      $.uniform.update(select);
                  }
              }
          },
          error: function(){
              //console.log("err");
          }
      });

};




function format_time(strtime) {
    var time = parseInt(strtime);
    return time_formatting.output(time);
}

/*
 * Return the date from two months before.
 */
function two_months_before_now() {
    var newdate = Date.today().addMonths(-2);
    return newdate.toString("yyyy/MM/dd");
}

/*
 * Format the axis time using our format_time function.
 */
var CHART_BAR_COLORS = ['#2b4664', '#9b1b1f', '#33537a'];
var CHART_PIE_COLORS = ['#2b4664', '#7bbbc9', '#9b1b1f', '#33537a'];
var STATS_CHROME_BG = '/static/img/stats_chrome.png';

function destroyCloudyChart(container_id) {
    var $el = $('#' + container_id);
    var chart = $el.data('cloudyChart');
    if (chart) {
        chart.destroy();
        $el.removeData('cloudyChart');
    }
}

function chartCanvasContext(container_id) {
    var $el = $('#' + container_id);
    $el.css('position', 'relative');
    destroyCloudyChart(container_id);
    $el.empty();
    var canvas = $('<canvas></canvas>');
    $el.append(canvas);
    return canvas[0].getContext('2d');
}

function drawHistogram(container_id, plot_data, slot_names, show_legend, no_format, y_legend) {
   var do_time_format = true;
   var y_legend_str =  'Heures de vol ('+time_formatting.legend+')';
   if (y_legend != undefined) {
     y_legend_str = y_legend;
   }
   if (no_format === true) {
     do_time_format = false;
   }
   var data = plot_data.slice(0, 5);
   var datasets = [];
   $.each(data, function(index, value) {
     datasets.push({
        label: value.label,
        data: value.data,
        backgroundColor: CHART_BAR_COLORS[index % CHART_BAR_COLORS.length],
        borderWidth: 0
     });
   });

   var ctx = chartCanvasContext(container_id);
   var chart = new Chart(ctx, {
      type: 'bar',
      data: {
         labels: slot_names,
         datasets: datasets
      },
      options: {
         animation: false,
         responsive: true,
         maintainAspectRatio: false,
         plugins: {
            legend: {
               display: show_legend,
               position: 'top',
               align: 'start'
            },
            title: {
               display: false
            },
            tooltip: {
               callbacks: {
                  label: function(context) {
                     var val = context.parsed.y;
                     if (do_time_format) {
                        return context.dataset.label + ': ' + format_time(val);
                     }
                     return context.dataset.label + ': ' + val;
                  }
               }
            }
         },
         scales: {
            x: {
               ticks: {
                  color: '#888',
                  maxRotation: 50,
                  minRotation: 50
               }
            },
            y: {
               min: 0,
               title: {
                  display: true,
                  text: y_legend_str
               },
               ticks: {
                  callback: function(value) {
                     if (do_time_format) {
                        return format_time(value);
                     }
                     return value;
                  }
               }
            }
         }
      }
   });
   $('#' + container_id).data('cloudyChart', chart);
}

var pieInsideLabelsPlugin = {
   id: 'pieInsideLabels',
   afterDraw: function(chart) {
      if (chart.config.type !== 'pie') {
         return;
      }
      var ctx = chart.ctx;
      var meta = chart.getDatasetMeta(0);
      ctx.save();
      ctx.fillStyle = 'white';
      ctx.font = 'normal 15px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      meta.data.forEach(function(arc, i) {
         var label = chart.data.labels[i];
         if (!label) {
            return;
         }
         var pos = arc.tooltipPosition();
         ctx.fillText(label, pos.x, pos.y);
      });
      ctx.restore();
   }
};

var pieChromeBackgroundPlugin = {
   id: 'pieChromeBackground',
   beforeDraw: function(chart) {
      if (chart.config.type !== 'pie' || !chart.pieChromeImage) {
         return;
      }
      var img = chart.pieChromeImage;
      if (!img.complete) {
         return;
      }
      var ctx = chart.ctx;
      var chartArea = chart.chartArea;
      var size = Math.min(chartArea.width, chartArea.height) * 0.85;
      var x = (chartArea.left + chartArea.right) / 2 - size / 2;
      var y = (chartArea.top + chartArea.bottom) / 2 - size / 2;
      ctx.drawImage(img, x, y, size, size);
   }
};

function drawPieChart(container_id, data, no_format) {
    var do_time_format = true;
    if (no_format == true) {
      do_time_format = false;
    }
    var cleaned_data = [];
     $.each(data, function(i, item) {
         if (data[i][1] !== 0) {
             cleaned_data.push(item);
         }
      });

    var labels = [];
    var values = [];
    $.each(cleaned_data, function(i, item) {
        labels.push(item[0]);
        values.push(item[1]);
    });

    var ctx = chartCanvasContext(container_id);
    var chromeImg = new Image();
    chromeImg.src = STATS_CHROME_BG;

    var chart = new Chart(ctx, {
        type: 'pie',
        data: {
           labels: labels,
           datasets: [{
              data: values,
              backgroundColor: CHART_PIE_COLORS.slice(0, values.length),
              borderWidth: 1,
              borderColor: '#000000'
           }]
        },
        plugins: [pieInsideLabelsPlugin, pieChromeBackgroundPlugin],
        options: {
           animation: false,
           responsive: true,
           maintainAspectRatio: true,
           plugins: {
              legend: {
                 display: false
              },
              tooltip: {
                 callbacks: {
                    label: function(context) {
                       var name = context.label;
                       var val = context.parsed;
                       if (do_time_format) {
                          return name + ': ' + format_time(val);
                       }
                       return name + ': ' + val;
                    }
                 }
              }
           }
        }
    });
    chart.pieChromeImage = chromeImg;
    chromeImg.onload = function() {
        chart.draw();
    };
    $('#' + container_id).data('cloudyChart', chart);
}
