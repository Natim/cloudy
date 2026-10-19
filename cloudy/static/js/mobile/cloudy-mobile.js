(function() {
  var BalloonDgacLog, BalloonDgacLogbook, GliderDgacLog, GliderDgacLogbook, HelicopterDgacLog, HelicopterDgacLogbook, HomeController, Log, LogCollection, Logbook, LogbookCollection, LogbooksView, LoginView, LogsView, NewGliderDgacLogView, NewLogView, NewPlaneDgacLogView, NewUlmFfplumLogView, ParachuteCloudyLog, ParachuteCloudyLogbook, PlaneDgacLog, PlaneDgacLogbook, PlaneFcl1080Log, PlaneFcl1080Logbook, UlmFfplumLog, UlmFfplumLogbook, app;
  var __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
  app = {
    scrollerTimeArrayToMinutes: function(time_array) {
      if (time_array != null) {
        return parseInt(time_array[0]) * 60 + parseInt(time_array[1]);
      } else {
        return 0;
      }
    },
    scrollerDateArrayToMinutes: function(date_array) {
      if (date_array != null) {
        return parseInt(date_array[2]) + "-" + app.zeroPad(parseInt(date_array[0]) + 1, 2) + "-" + app.zeroPad(parseInt(date_array[1]), 2) + "T00:00:00Z";
      }
    },
    timeToMinutes: function(time_str) {
      var match;
      if (time_str || time_str === "") {
        return 0;
      }
      match = time_str.match(/^([01]\d|2[0-3]):([0-5]\d)$/);
      return match[1] * 60 + match[2];
    },
    minutesToTime: function(minutes) {
      var hour, minutes_left;
      minutes_left = minutes % 60;
      hour = Math.floor(minutes / 60);
      return app.zeroPad(hour, 2) + ":" + app.zeroPad(minutes_left, 2);
    },
    timestampToFormattedDate: function(timestamp) {
      var date;
      date = new Date(timestamp);
      return app.dateToFormattedDateIso(date);
    },
    dateToFormattedDate: function(date) {
      return app.zeroPad(date.getUTCDate(), 2) + "/" + app.zeroPad(date.getUTCMonth() + 1, 2) + "/" + date.getUTCFullYear();
    },
    dateStrToFormattedDate: function(date) {
      var arr;
      arr = date.split(/[-T :]/);
      date = new Date(arr[0], arr[1] - 1, arr[2], arr[3], arr[4], arr[5]);
      return app.dateToFormattedDate(date);
    },
    dateToFormattedDateIso: function(date) {
      return date.getUTCFullYear() + "-" + app.zeroPad(date.getUTCMonth() + 1, 2) + "-" + app.zeroPad(date.getUTCDate(), 2);
    },
    dateStrToFormattedDateIso: function(date) {
      var arr;
      arr = date.split(/[-T :]/);
      date = new Date(arr[0], arr[1] - 1, arr[2], arr[3], arr[4], arr[5]);
      return app.dateToFormattedDateIso(date);
    },
    dateStringToDateTimeIso: function(str_date) {
      return str_date + "T00:00:01";
    },
    ISODateString: function(d) {
      return d.getUTCFullYear() + "-" + app.zeroPad(d.getUTCMonth() + 1, 2) + "-" + app.zeroPad(d.getUTCDate(), 2) + "T" + app.zeroPad(d.getUTCHours(), 2) + ":" + app.zeroPad(d.getUTCMinutes(), 2) + ":" + app.zeroPad(d.getUTCSeconds(), 2);
    },
    switchCurrentPage: function(el) {
      $(".current-page").hide();
      $(".current-page").removeClass("current-page");
      el.addClass("current-page");
      return $(".current-page").show();
    },
    zeroPad: function(num, count) {
      var numZeropad;
      numZeropad = num + '';
      while (numZeropad.length < count) {
        numZeropad = "0" + numZeropad;
      }
      return numZeropad;
    },
    iScrollOptions: {
      useTransform: true,
      momentum: true,
      onBeforeScrollStart: function(e) {
        var target;
        target = e.target;
        while (target.nodeType !== 1) {
          target = target.parentNode;
        }
        if (target.tagName !== 'SELECT' && target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
          return e.preventDefault();
        }
      }
    },
    launchIScroll: function(scroller_id) {
      document.addEventListener('touchmove', function(e) {
        return e.preventDefault();
      }, false);
      return new iScroll(scroller_id, this.iScrollOptions);
    }
  };
  Logbook = (function() {
    __extends(Logbook, Backbone.Model);
    function Logbook(attributes, options) {
      Logbook.__super__.constructor.apply(this, arguments);
    }
    return Logbook;
  })();
  UlmFfplumLogbook = (function() {
    __extends(UlmFfplumLogbook, Logbook);
    function UlmFfplumLogbook() {
      UlmFfplumLogbook.__super__.constructor.apply(this, arguments);
    }
    UlmFfplumLogbook.prototype.getIcon = function() {
      return "/static/raw_css/images/v_ulm_ffplum.png";
    };
    return UlmFfplumLogbook;
  })();
  PlaneDgacLogbook = (function() {
    __extends(PlaneDgacLogbook, Logbook);
    function PlaneDgacLogbook() {
      PlaneDgacLogbook.__super__.constructor.apply(this, arguments);
    }
    PlaneDgacLogbook.prototype.getIcon = function() {
      return "/static/raw_css/images/v_plane_dgac.png";
    };
    return PlaneDgacLogbook;
  })();
  GliderDgacLogbook = (function() {
    __extends(GliderDgacLogbook, Logbook);
    function GliderDgacLogbook() {
      GliderDgacLogbook.__super__.constructor.apply(this, arguments);
    }
    GliderDgacLogbook.prototype.getIcon = function() {
      return "/static/raw_css/images/v_glider_dgac.png";
    };
    return GliderDgacLogbook;
  })();
  PlaneFcl1080Logbook = (function() {
    __extends(PlaneFcl1080Logbook, Logbook);
    function PlaneFcl1080Logbook() {
      PlaneFcl1080Logbook.__super__.constructor.apply(this, arguments);
    }
    PlaneFcl1080Logbook.prototype.getIcon = function() {
      return "/static/raw_css/images/v_plane_dgac.png";
    };
    return PlaneFcl1080Logbook;
  })();
  HelicopterDgacLogbook = (function() {
    __extends(HelicopterDgacLogbook, Logbook);
    function HelicopterDgacLogbook() {
      HelicopterDgacLogbook.__super__.constructor.apply(this, arguments);
    }
    HelicopterDgacLogbook.prototype.getIcon = function() {
      return "/static/raw_css/images/v_helicopter_dgac.png";
    };
    return HelicopterDgacLogbook;
  })();
  BalloonDgacLogbook = (function() {
    __extends(BalloonDgacLogbook, Logbook);
    function BalloonDgacLogbook() {
      BalloonDgacLogbook.__super__.constructor.apply(this, arguments);
    }
    BalloonDgacLogbook.prototype.getIcon = function() {
      return "/static/raw_css/images/icon-focus-baloon.png";
    };
    return BalloonDgacLogbook;
  })();
  ParachuteCloudyLogbook = (function() {
    __extends(ParachuteCloudyLogbook, Logbook);
    function ParachuteCloudyLogbook() {
      ParachuteCloudyLogbook.__super__.constructor.apply(this, arguments);
    }
    ParachuteCloudyLogbook.prototype.getIcon = function() {
      return "/static/raw_css/images/icon-focus-parachute.png";
    };
    return ParachuteCloudyLogbook;
  })();
  LogbookCollection = (function() {
    __extends(LogbookCollection, Backbone.Collection);
    LogbookCollection.prototype.model = function(attrs, options) {
      switch (attrs.cat) {
        case 'ulm_ffplum':
          return new UlmFfplumLogbook(attrs, options);
        case 'plane_dgac':
          return new PlaneDgacLogbook(attrs, options);
        case 'glider_dgac':
          return new GliderDgacLogbook(attrs, options);
        case 'plane_fcl1080':
          return new PlaneFcl1080Logbook(attrs, options);
        case 'helicopter_dgac':
          return new HelicopterDgacLogbook(attrs, options);
        case 'balloon_dgac':
          return new BalloonDgacLogbook(attrs, options);
        case 'parachute_cloudy':
          return new ParachuteCloudyLogbook(attrs, options);
      }
    };
    LogbookCollection.prototype.url = function() {
      return "/api/logbooks?k=" + $.cookie('api_key') + "&v=3";
    };
    function LogbookCollection() {
      this.logbookAdded = __bind(this.logbookAdded, this);      LogbookCollection.__super__.constructor.apply(this, arguments);
      this.bind('reset', this.logbookAdded);
    }
    LogbookCollection.prototype.parse = function(data) {
      return data.data;
    };
    LogbookCollection.prototype.logbookAdded = function() {
      return console.log("[LogbookCollection] logbooks fetched (reset event on the collection)");
    };
    return LogbookCollection;
  })();
  Log = (function() {
    __extends(Log, Backbone.Model);
    function Log(params) {
      this.getNotZeroAmong = __bind(this.getNotZeroAmong, this);
      this.getTimeAmist = __bind(this.getTimeAmist, this);
      this.getFlightTime = __bind(this.getFlightTime, this);
      this.getLabel = __bind(this.getLabel, this);      Log.__super__.constructor.call(this, params);
      if (params && params.options && params.options.logbook) {
        this.logbook = params.options.logbook;
        console.log("[Log] Constructor - logbook_id = " + this.logbook.id);
      }
    }
    Log.prototype.url = function() {
      if (this.isNew()) {
        return "/api/logbooks/" + this.logbook.get("id") + "?k=" + $.cookie('api_key') + "&v=3";
      } else {
        return "/api/logs/" + this.id + "?k=" + $.cookie('api_key') + "&v=3";
      }
    };
    Log.prototype.getLabel = function() {
      throw Error("Can't call getLabel on abstract class Log");
    };
    Log.prototype.getFlightTime = function() {
      throw Error("Can't call getFlightTime on abstract class Log");
    };
    Log.prototype.getTimeAmist = function(attr_array) {
      var attr, time, _i, _len;
      time = 0;
      for (_i = 0, _len = attr_array.length; _i < _len; _i++) {
        attr = attr_array[_i];
        if (this.get(attr) !== 0) {
          time = this.get(attr);
        }
      }
      return time;
    };
    Log.prototype.getNotZeroAmong = function(attr_array) {
      var attr, _i, _len;
      for (_i = 0, _len = attr_array.length; _i < _len; _i++) {
        attr = attr_array[_i];
        if (this.get(attr) !== 0) {
          return attr;
        }
      }
      return attr_array[0];
    };
    Log.prototype.validateLog = function(attrs, errors) {
      return null;
    };
    Log.prototype.validate = function(attrs) {
      var errors;
      console.log(attrs);
      errors = [];
      if (!(attrs.cdate != null) || (attrs.ok != null)) {
        if ((attrs.ok != null) && attrs.ok === false) {
          errors.push(attrs.data);
        } else {
          if ((attrs.ok != null) && attrs.ok === true) {
            return null;
          }
          this.validateLog(attrs, errors);
        }
      }
      if (_.any(errors)) {
        alert("Veuillez corriger les erreurs suivantes : \n\n" + errors.join("\n"));
      }
      if (!_.any(errors)) {
        console.log("Validation : pas d'erreur");
      }
      if (_.any(errors)) {
        return errors;
      } else {
        return null;
      }
    };
    return Log;
  })();
  UlmFfplumLog = (function() {
    __extends(UlmFfplumLog, Log);
    function UlmFfplumLog() {
      UlmFfplumLog.__super__.constructor.apply(this, arguments);
    }
    UlmFfplumLog.prototype.getLabel = function() {
      return this.get("ulm_imma");
    };
    UlmFfplumLog.prototype.getFlightTime = function() {
      return this.getTimeAmist(['flytime_cdb', 'flytime_dbl']);
    };
    UlmFfplumLog.prototype.defaults = {
      'date': app.ISODateString(new Date()),
      'flytime_dbl': 0,
      'flytime_cdb': 0,
      'obs': '',
      'cmmts': '',
      'nbrto': 0,
      'nbrla': 0
    };
    UlmFfplumLog.prototype.validateLog = function(attrs, errors) {
      var flytime;
      if (!(attrs.date != null) || attrs.date === "") {
        errors.push("Vous devez rentrer la date du vol");
      }
      if (!(attrs.ulm_imma != null) || attrs.ulm_imma === "") {
        errors.push("Vous devez rentrer l'immatriculation");
      }
      if (!(attrs.ulm_type != null) || attrs.ulm_type === "") {
        errors.push("Vous devez rentrer le type");
      }
      flytime = attrs.flytime_dbl !== 0 || attrs.flytime_cdb !== 0;
      if (flytime === false) {
        return errors.push("Vous devez entrer un temps de vol.");
      }
    };
    return UlmFfplumLog;
  })();
  PlaneDgacLog = (function() {
    __extends(PlaneDgacLog, Log);
    function PlaneDgacLog() {
      this.getInstruTime = __bind(this.getInstruTime, this);
      this.getMulTime = __bind(this.getMulTime, this);
      this.getMonoTime = __bind(this.getMonoTime, this);
      this.getMbrEqTime = __bind(this.getMbrEqTime, this);
      PlaneDgacLog.__super__.constructor.apply(this, arguments);
    }
    PlaneDgacLog.prototype.defaults = {
      'mbr_equipage_jour': 0,
      'mbr_equipage_nuit': 0,
      'mono_jdbl': 0,
      'mono_jcdb': 0,
      'mono_ndbl': 0,
      'mono_ncdb': 0,
      'mul_jdbl': 0,
      'mul_jcdb': 0,
      'mul_jcplt': 0,
      'mul_ndbl': 0,
      'mul_ncdb': 0,
      'mul_ncplt': 0,
      'vai_dbl': 0,
      'vai_plt': 0,
      'simu': 0,
      'ifr': 0,
      'obs': '',
      'cmmts': '',
      'nbrto': 0,
      'nbrla': 0,
      'date': app.ISODateString(new Date())
    };
    PlaneDgacLog.prototype.getLabel = function() {
      return this.get("aeronef_imma");
    };
    PlaneDgacLog.prototype.getFlightTime = function() {
      return this.getTimeAmist(['mono_jdbl', 'mono_jcdb', 'mono_ndbl', 'mono_ncdb', 'mul_jdbl', 'mul_jcdb', 'mul_jcplt', 'mul_ndbl', 'mul_ncdb', 'mul_ncplt']);
    };
    PlaneDgacLog.prototype.getMbrEqTime = function() {
      return this.getTimeAmist(['mbr_equipage_nuit', 'mbr_equipage_jour']);
    };
    PlaneDgacLog.prototype.getMonoTime = function() {
      return this.getTimeAmist(['mono_jdbl', 'mono_jcdb', 'mono_ndbl', 'mono_ncdb']);
    };
    PlaneDgacLog.prototype.getMulTime = function() {
      return this.getTimeAmist(['mul_jdbl', 'mul_jcdb', 'mul_jcplt', 'mul_ndbl', 'mul_ncdb', 'mul_ncplt']);
    };
    PlaneDgacLog.prototype.getInstruTime = function() {
      return this.getTimeAmist(['vai_dbl', 'vai_plt']);
    };
    PlaneDgacLog.prototype.validateLog = function(attrs, errors) {
      var mono, multi;
      if (!(attrs.date != null) || attrs.date === "") {
        errors.push("Vous devez rentrer la date du vol");
      }
      if (!(attrs.aeronef_imma != null) || attrs.aeronef_imma === "") {
        errors.push("Vous devez rentrer l'immatriculation");
      }
      if (!(attrs.aeronef_type != null) || attrs.aeronef_type === "") {
        errors.push("Vous devez rentrer le type");
      }
      if (!(attrs.natvol != null) || attrs.natvol === "") {
        errors.push("Vous devez rentrer la nature du vol");
      }
      mono = attrs.mono_jdbl !== 0 || attrs.mono_jcdb !== 0 || attrs.mono_ndbl !== 0 || attrs.mono_ncdb !== 0;
      multi = attrs.mul_jdbl !== 0 || attrs.mul_jcdb !== 0 || attrs.mul_jcplt !== 0 || attrs.mul_ndbl !== 0 || attrs.mul_ncdb !== 0 || attrs.mul_ncplt !== 0;
      if (mono === true && multi === true) {
        errors.push("Vous ne pouvez valider un vol monomoteur et multimoteur en même temps.");
      }
      if (mono === false && multi === false) {
        return errors.push("Vous devez renseigner au moins un vol monomoteur ou multimoteur.");
      }
    };
    return PlaneDgacLog;
  })();
  GliderDgacLog = (function() {
    __extends(GliderDgacLog, Log);
    function GliderDgacLog() {
      GliderDgacLog.__super__.constructor.apply(this, arguments);
    }
    GliderDgacLog.prototype.getLabel = function() {
      return this.get("glider_imma");
    };
    GliderDgacLog.prototype.getFlightTime = function() {
      return this.getTimeAmist(['flytime_cdb', 'flytime_dbl', 'flytime_ins']);
    };
    GliderDgacLog.prototype.defaults = {
      'date': app.ISODateString(new Date()),
      'flytime_dbl': 0,
      'flytime_cdb': 0,
      'flytime_ins': 0,
      'obs': '',
      'cmmts': '',
      'nbrto': 0,
      'nbrla': 0
    };
    GliderDgacLog.prototype.validateLog = function(attrs, errors) {
      var flytime;
      if (!(attrs.date != null) || attrs.date === "") {
        errors.push("Vous devez rentrer la date du vol");
      }
      if (!(attrs.glider_imma != null) || attrs.glider_imma === "") {
        errors.push("Vous devez rentrer l'immatriculation");
      }
      if (!(attrs.glider_type != null) || attrs.glider_type === "") {
        errors.push("Vous devez rentrer le type");
      }
      if (!(attrs.natvol != null) || attrs.natvol === "") {
        errors.push("Vous devez rentrer la nature du vol");
      }
      flytime = attrs.flytime_dbl !== 0 || attrs.flytime_cdb !== 0 || attrs.flytime_ins !== 0;
      if (flytime === false) {
        return errors.push("Vous devez entrer un temps de vol.");
      }
    };
    return GliderDgacLog;
  })();
  PlaneFcl1080Log = (function() {
    __extends(PlaneFcl1080Log, Log);
    function PlaneFcl1080Log() {
      PlaneFcl1080Log.__super__.constructor.apply(this, arguments);
    }
    PlaneFcl1080Log.prototype.getLabel = function() {
      return this.get("aeronef_imma");
    };
    return PlaneFcl1080Log;
  })();
  HelicopterDgacLog = (function() {
    __extends(HelicopterDgacLog, PlaneDgacLog);
    function HelicopterDgacLog() {
      HelicopterDgacLog.__super__.constructor.apply(this, arguments);
    }
    return HelicopterDgacLog;
  })();
  BalloonDgacLog = (function() {
    __extends(BalloonDgacLog, Log);
    function BalloonDgacLog() {
      BalloonDgacLog.__super__.constructor.apply(this, arguments);
    }
    BalloonDgacLog.prototype.getLabel = function() {
      return "NA";
    };
    return BalloonDgacLog;
  })();
  ParachuteCloudyLog = (function() {
    __extends(ParachuteCloudyLog, Log);
    function ParachuteCloudyLog() {
      ParachuteCloudyLog.__super__.constructor.apply(this, arguments);
    }
    ParachuteCloudyLog.prototype.getLabel = function() {
      return "NA";
    };
    return ParachuteCloudyLog;
  })();
  LogCollection = (function() {
    __extends(LogCollection, Backbone.Collection);
    LogCollection.prototype.model = function(attrs, options) {
      if (this.logbook) {
        switch (this.logbook.get('cat')) {
          case 'ulm_ffplum':
            return new UlmFfplumLog(attrs, options);
          case 'plane_dgac':
            return new PlaneDgacLog(attrs, options);
          case 'glider_dgac':
            return new GliderDgacLog(attrs, options);
          case 'plane_fcl1080':
            return new PlaneFcl1080Log(attrs, options);
          case 'helicopter_dgac':
            return new HelicopterDgacLog(attrs, options);
          case 'balloon_dgac':
            return new BalloonDgacLog(attrs, options);
          case 'parachute_cloudy':
            return new ParachuteCloudyLog(attrs, options);
          default:
            throw Error("Can't find subclass and Log is an abstract class");
        }
      } else {
        return new Log(attrs, options);
      }
    };
    LogCollection.prototype.url = function() {
      return "/api/logbooks/" + this.logbook.get("id") + "?k=" + $.cookie('api_key') + "&v=3";
    };
    function LogCollection(params) {
      this.logAdded = __bind(this.logAdded, this);
      this.logsFetched = __bind(this.logsFetched, this);
      this.model = __bind(this.model, this);      LogCollection.__super__.constructor.call(this, params);
      this.logbook = params.options.logbook;
      this.bind('reset', this.logsFetched);
      this.bind('add', this.logAdded);
    }
    LogCollection.prototype.parse = function(resp) {
      return resp.data;
    };
    LogCollection.prototype.logsFetched = function() {
      var that;
      console.log("[LogCollection] logs fetched (reset event on the collection)");
      that = this;
      return this.each(function(log) {
        return log.logbook = that.logbook;
      });
    };
    LogCollection.prototype.logAdded = function() {
      return console.log("[LogCollection] log added (add event on the collection)");
    };
    return LogCollection;
  })();
  LogbooksView = (function() {
    __extends(LogbooksView, Backbone.View);
    function LogbooksView() {
      this.close = __bind(this.close, this);
      this.render = __bind(this.render, this);
      this.logout = __bind(this.logout, this);      LogbooksView.__super__.constructor.apply(this, arguments);
      this.page_id = "logbooks-view";
      $("body").prepend(_.template($("#jquery-page-canvas").html(), {
        page_id: this.page_id
      }));
      this.el = $("#" + this.page_id);
      this.template = _.template($("#logbooks-view-template").html());
      this.template_header = _.template($("#logbooks-view-template-header").html());
      this.collection.bind('reset', this.render);
    }
    LogbooksView.prototype.logout = function() {
      var view_key;
      console.log("loging out");
      $.cookie('api_key', null);
      console.log(app.homeController._views);
      for (view_key in app.homeController._views) {
        app.homeController._views[view_key].close();
      }
      app.homeController._views = {};
      app.homeController.login();
      this.unbind();
      this.remove();
      return this.collection.unbind("reset", this.render);
    };
    LogbooksView.prototype.render = function() {
      var that;
      this.el.find('.cloudy-content').html(this.template({
        logbooks: this.collection
      }));
      this.el.find('.cloudy-header').html(this.template_header());
      this.el.find(".logout-button").bind("click", this.logout);
      app.switchCurrentPage(this.el);
      that = this;
      return app.launchIScroll('logbooks-view-content', false, {
        onScrollEnd: function() {
          if ($('#pullDown').hasClass('flip')) {
            $('#pullDown').addClass('loading');
            $('#pullDown').find('.pullDownLabel').html('Loading...');
            return that.collection.fetch();
          }
        }
      });
    };
    LogbooksView.prototype.close = function() {
      this.collection.unbind("reset", this.render);
      this.unbind();
      return this.remove();
    };
    return LogbooksView;
  })();
  LogsView = (function() {
    __extends(LogsView, Backbone.View);
    function LogsView(options) {
      this.close = __bind(this.close, this);
      this.render = __bind(this.render, this);      LogsView.__super__.constructor.apply(this, arguments);
      this.logbook = options.logbook;
      this.page_id = "logbook-" + this.logbook.id + "-logs-view";
      this.css_class_bg = "cloudy-background-mobile";
      $("body").prepend(_.template($("#jquery-page-canvas").html(), {
        page_id: this.page_id,
        css_class_bg: this.css_class_bg
      }));
      this.el = $("#" + this.page_id);
      this.template = _.template($("#logs-view-template").html());
      this.template_header = _.template($("#logs-view-template-header").html());
      this.collection.bind('reset', this.render);
    }
    LogsView.prototype.render = function() {
      var scroller, that;
      this.el.find('.cloudy-content').html(this.template({
        logs: this.collection
      }));
      this.el.find('.cloudy-header').html(this.template_header({
        logbook: this.logbook
      }));
      app.switchCurrentPage(this.el);
      scroller = this.page_id + '-content';
      that = this;
      return app.launchIScroll(scroller, false, {
        onScrollEnd: function() {
          if ($('#pullDown').hasClass('flip')) {
            $('#pullDown').addClass('loading');
            $('#pullDown').find('.pullDownLabel').html('Loading...');
            return that.collection.fetch();
          }
        }
      });
    };
    LogsView.prototype.close = function() {
      this.collection.unbind("reset", this.render);
      this.unbind();
      return this.remove();
    };
    return LogsView;
  })();
  NewLogView = (function() {
    __extends(NewLogView, Backbone.View);
    function NewLogView() {
      this.close = __bind(this.close, this);
      this.back = __bind(this.back, this);
      this.unsetUnusedAttributes = __bind(this.unsetUnusedAttributes, this);
      this.validateAndSaveLog = __bind(this.validateAndSaveLog, this);
      this.render = __bind(this.render, this);
      NewLogView.__super__.constructor.apply(this, arguments);
    }
    NewLogView.prototype.buildTemplate = function() {
      $("body").prepend(_.template($("#jquery-page-canvas").html(), {
        page_id: this.page_id
      }));
      this.el = $("#" + this.page_id);
      this.template = _.template($("#" + this.page_id + "-template").html());
      return this.template_header = _.template($("#" + this.page_id + "-template-header").html());
    };
    NewLogView.prototype.render = function() {
      var scroller;
      this.el.find('.cloudy-content').html(this.template({
        log: this.model
      }));
      this.el.find('.cloudy-header').html(this.template_header({
        logbook: this.logbook
      }));
      app.switchCurrentPage(this.el);
      this.el.find(".save-button").bind("click", this.saveLog);
      this.el.find(".back-button").bind("click", this.back);
      scroller = this.page_id + '-content';
      app.launchIScroll(scroller);
      $("input.time-scroller").scroller({
        theme: 'ios',
        preset: 'time',
        ampm: false,
        timeFormat: 'HH:ii',
        width: 80
      });
      $("input.date-scroller").scroller({
        theme: 'ios',
        preset: 'date',
        dateFormat: 'yyyy-mm-dd',
        width: 80
      });
      return $(".jquery-ui-radio").buttonset();
    };
    NewLogView.prototype.validateAndSaveLog = function() {
      var that;
      if (this.model.isValid() === true) {
        console.log("Log is valid => Saving it on the server");
        that = this;
        return this.model.save(null, {
          success: function(model, response) {
            console.log("Success ! Log saved !");
            app.homeController.logbookLogs(that.model.logbook.id, that.model.logbook.cat);
            app.homeController.navigate("logbooks-" + that.model.logbook.id + "-logs", false);
            return that.close();
          }
        });
      }
    };
    NewLogView.prototype.unsetUnusedAttributes = function() {
      this.model.unset('files', {
        silent: true
      });
      this.model.unset('visibl', {
        silent: true
      });
      this.model.unset('deleted', {
        silent: true
      });
      this.model.unset('optional_filter', {
        silent: true
      });
      this.model.unset('lbook', {
        silent: true
      });
      this.model.unset('cdate', {
        silent: true
      });
      return this.model.unset('udate', {
        silent: true
      });
    };
    NewLogView.prototype.back = function() {
      history.back();
      return this.close();
    };
    NewLogView.prototype.close = function() {
      this.unbind();
      this.remove();
      $("input.time-scroller").scroller('destroy');
      return $("input.date-scroller").scroller('destroy');
    };
    return NewLogView;
  })();
  NewPlaneDgacLogView = (function() {
    __extends(NewPlaneDgacLogView, NewLogView);
    function NewPlaneDgacLogView(options) {
      this.saveLog = __bind(this.saveLog, this);      NewPlaneDgacLogView.__super__.constructor.apply(this, arguments);
      this.logbook = options.logbook;
      this.page_id = "new-plane-dgac-log-view";
      this.buildTemplate();
      this.render();
    }
    NewPlaneDgacLogView.prototype.saveLog = function() {
      var current_instru, current_mbr_equipage, current_mono, current_mul, instru_dbl_or_plt, json, mono_dbl_or_cdb, mul_dbl_cplt_or_cdb;
      this.model.set({
        'mbr_equipage_nuit': 0,
        'mbr_equipage_jour': 0
      }, {
        silent: true
      });
      current_mbr_equipage = 'mbr_equipage_' + $('[name=mbr_eq_period]').val();
      console.log("Membre équipage Selected mode : " + current_mbr_equipage);
      json = {};
      json[current_mbr_equipage] = app.scrollerTimeArrayToMinutes($('[name=mbr_eq_time]').scroller('getValue'));
      this.model.set(json, {
        silent: true
      });
      this.model.set({
        'mono_jdbl': 0,
        'mono_jcdb': 0,
        'mono_ndbl': 0,
        'mono_ncdb': 0
      }, {
        silent: true
      });
      mono_dbl_or_cdb = $('[name=mono_dbl_or_cdb]:checked').val();
      current_mono = 'mono_' + $('[name=mono_period]').val() + mono_dbl_or_cdb;
      console.log("Pilote Monomoteur Selected mode : " + current_mono);
      if (mono_dbl_or_cdb !== void 0) {
        json = {};
        json[current_mono] = app.scrollerTimeArrayToMinutes($('[name=mono_time]').scroller('getValue'));
        this.model.set(json, {
          silent: true
        });
      }
      this.model.set({
        'mul_jdbl': 0,
        'mul_jcdb': 0,
        'mul_jcplt': 0,
        'mul_ndbl': 0,
        'mul_ncdb': 0,
        'mul_ncplt': 0
      }, {
        silent: true
      });
      mul_dbl_cplt_or_cdb = $('[name=mul_dbl_cplt_or_cdb]:checked').val();
      current_mul = 'mul_' + $('[name=mul_period]').val() + mul_dbl_cplt_or_cdb;
      console.log("Pilote Multimoteurs Selected mode : " + current_mul);
      if (mul_dbl_cplt_or_cdb !== void 0) {
        json = {};
        json[current_mul] = app.scrollerTimeArrayToMinutes($('[name=mul_time]').scroller('getValue'));
        this.model.set(json, {
          silent: true
        });
      }
      this.model.set({
        'vai_dbl': 0,
        'vai_plt': 0
      }, {
        silent: true
      });
      instru_dbl_or_plt = $('[name=instru_dbl_or_plt]:checked').val();
      console.log("Vol aux instruments Selected mode : " + 'vai_' + instru_dbl_or_plt);
      if (instru_dbl_or_plt !== void 0) {
        current_instru = 'vai_' + instru_dbl_or_plt;
        json = {};
        json[current_instru] = app.scrollerTimeArrayToMinutes($('[name=instru_time]').scroller('getValue'));
        this.model.set(json, {
          silent: true
        });
      }
      this.model.set({
        'aeronef_type': $('[name=aeronef_type]').val()
      }, {
        silent: true
      });
      this.model.set({
        'aeronef_imma': $('[name=aeronef_imma]').val()
      }, {
        silent: true
      });
      this.model.set({
        'natvol': $('[name=natvol]').val()
      }, {
        silent: true
      });
      this.model.set({
        'fctbrd': $('[name=fctbrd]').val()
      }, {
        silent: true
      });
      this.model.set({
        'simu': app.scrollerTimeArrayToMinutes($('[name=simu_time]').scroller('getValue'))
      }, {
        silent: true
      });
      this.model.set({
        'ifr': $('[name=ifr]').val() || 0
      }, {
        silent: true
      });
      this.model.set({
        'obs': $('[name=obs]').val()
      }, {
        silent: true
      });
      this.model.set({
        'date': app.scrollerDateArrayToMinutes($('[name=date]').scroller('getValue'))
      }, {
        silent: true
      });
      this.model.unset('airpar', {
        silent: true
      });
      this.model.unset('airpdep', {
        silent: true
      });
      this.model.unset('staffob', {
        silent: true
      });
      this.unsetUnusedAttributes();
      this.validateAndSaveLog();
      return false;
    };
    return NewPlaneDgacLogView;
  })();
  NewGliderDgacLogView = (function() {
    __extends(NewGliderDgacLogView, NewLogView);
    function NewGliderDgacLogView(options) {
      this.saveLog = __bind(this.saveLog, this);      NewGliderDgacLogView.__super__.constructor.apply(this, arguments);
      this.logbook = options.logbook;
      this.page_id = "new-glider-dgac-log-view";
      this.buildTemplate();
      this.render();
    }
    NewGliderDgacLogView.prototype.saveLog = function() {
      var current_instru, flytime_dbl_cdb_or_ins, json;
      this.model.set({
        'flytime_dbl': 0,
        'flytime_cdb': 0,
        'flytime_ins': 0
      }, {
        silent: true
      });
      flytime_dbl_cdb_or_ins = $('[name=flytime_dbl_cdb_or_ins]:checked').val();
      console.log("Flytime Selected mode : " + 'flytime_' + flytime_dbl_cdb_or_ins);
      if (flytime_dbl_cdb_or_ins !== void 0) {
        current_instru = 'flytime_' + flytime_dbl_cdb_or_ins;
        json = {};
        json[current_instru] = app.scrollerTimeArrayToMinutes($('[name=flytime_time]').scroller('getValue'));
        this.model.set(json, {
          silent: true
        });
      }
      this.model.set({
        'glider_type': $('[name=glider_type]').val()
      }, {
        silent: true
      });
      this.model.set({
        'glider_imma': $('[name=glider_imma]').val()
      }, {
        silent: true
      });
      this.model.set({
        'fctbrd': $('[name=fctbrd]').val()
      }, {
        silent: true
      });
      this.model.set({
        'natvol': $('[name=natvol]').val()
      }, {
        silent: true
      });
      this.model.set({
        'lmode': $('[name=lmode]').val()
      }, {
        silent: true
      });
      this.model.set({
        'obs': $('[name=obs]').val()
      }, {
        silent: true
      });
      this.model.set({
        'date': app.scrollerDateArrayToMinutes($('[name=date]').scroller('getValue'))
      }, {
        silent: true
      });
      this.model.unset('airpar', {
        silent: true
      });
      this.model.unset('airpdep', {
        silent: true
      });
      this.model.unset('staffob', {
        silent: true
      });
      this.model.unset('cmmts', {
        silent: true
      });
      this.unsetUnusedAttributes();
      this.validateAndSaveLog();
      return false;
    };
    return NewGliderDgacLogView;
  })();
  NewUlmFfplumLogView = (function() {
    __extends(NewUlmFfplumLogView, NewLogView);
    function NewUlmFfplumLogView(options) {
      this.saveLog = __bind(this.saveLog, this);      NewUlmFfplumLogView.__super__.constructor.apply(this, arguments);
      this.logbook = options.logbook;
      this.page_id = "new-ulm-ffplum-log-view";
      this.buildTemplate();
      this.render();
    }
    NewUlmFfplumLogView.prototype.saveLog = function() {
      var current_instru, flytime_dbl_or_cdb, json;
      this.model.set({
        'flytime_dbl': 0,
        'flytime_cdb': 0
      }, {
        silent: true
      });
      flytime_dbl_or_cdb = $('[name=flytime_dbl_or_cdb]:checked').val();
      console.log("Flytime Selected mode : " + 'flytime_' + flytime_dbl_or_cdb);
      if (flytime_dbl_or_cdb !== void 0) {
        current_instru = 'flytime_' + flytime_dbl_or_cdb;
        json = {};
        json[current_instru] = app.scrollerTimeArrayToMinutes($('[name=flytime_time]').scroller('getValue'));
        this.model.set(json, {
          silent: true
        });
      }
      this.model.set({
        'ulm_type': $('[name=ulm_type]').val()
      }, {
        silent: true
      });
      this.model.set({
        'ulm_imma': $('[name=ulm_imma]').val()
      }, {
        silent: true
      });
      this.model.set({
        'obs': $('[name=obs]').val()
      }, {
        silent: true
      });
      this.model.set({
        'date': app.scrollerDateArrayToMinutes($('[name=date]').scroller('getValue'))
      }, {
        silent: true
      });
      this.unsetUnusedAttributes();
      this.validateAndSaveLog();
      return false;
    };
    return NewUlmFfplumLogView;
  })();
  LoginView = (function() {
    __extends(LoginView, Backbone.View);
    function LoginView(options) {
      this.close = __bind(this.close, this);
      this.login = __bind(this.login, this);
      this.render = __bind(this.render, this);      LoginView.__super__.constructor.apply(this, arguments);
      this.page_id = "login-view";
      $("body").prepend(_.template($("#jquery-page-canvas-login").html(), {
        page_id: this.page_id
      }));
      this.el = $("#" + this.page_id);
      this.template = _.template($("#login-view-template").html());
      this.template_header = _.template($("#login-view-template-header").html());
      this.model.bind("change", this.render);
      this.render();
    }
    LoginView.prototype.render = function() {
      this.el.find('.cloudy-content').html(this.template({
        loginInfo: this.model
      }));
      this.el.find('.cloudy-header').html(this.template_header());
      this.el.find(".login-button").bind("click", this.login);
      return app.switchCurrentPage(this.el);
    };
    LoginView.prototype.login = function() {
      var that;
      console.log("Loging in");
      that = this;
      $.ajax({
        url: "/api/session?email=" + $('[name=email]').val() + "&pwd=" + $('[name=mdp]').val(),
        contentType: 'application/json',
        type: "GET",
        success: function(resp) {
          resp = $.parseJSON(resp);
          if (resp.ok === true) {
            console.log('Login success :', resp.ok);
            $.cookie('api_key', resp.data, {
              expires: 365
            });
            $.cookie('last_email', $('[name=email]').val());
            app.homeController.logbooksIndex();
            that.model.destroy();
            return that.remove();
          } else {
            console.log('Login error :', resp.ok);
            return that.model.set({
              email: $('[name=email]').val(),
              mdp: "",
              error: resp.data
            });
          }
        }
      });
      return false;
    };
    LoginView.prototype.close = function() {
      this.remove();
      return this.unbind();
    };
    return LoginView;
  })();
  HomeController = (function() {
    __extends(HomeController, Backbone.Router);
    HomeController.prototype.routes = {
      "login": "login",
      "logbooks-:id-logs": "logbookLogs",
      "logbooks-new": "newLogbook",
      "": "logbooksIndex",
      "logbook-:logbookid-logs-new": "newLog",
      "logbook-:logbookid-logs-:logid": "editLog"
    };
    function HomeController() {
      HomeController.__super__.constructor.apply(this, arguments);
      this._views = {};
      this.logs = [];
    }
    HomeController.prototype.user_logged_in = function() {
      if ($.cookie('api_key')) {
        return true;
      } else {
        this.login();
        return false;
      }
    };
    HomeController.prototype.login = function(error_msg) {
      console.log("==> Route to : Login, error = " + error_msg);
      return this._views['login'] = new LoginView({
        model: new Backbone.Model({
          email: $.cookie('last_email'),
          mdp: "",
          error: error_msg
        })
      });
    };
    HomeController.prototype.logbooksIndex = function() {
      console.log("==> Route to : Logbooks");
      if (this.user_logged_in()) {
        if (this._views['logbooks']) {
          return this.logbooks.fetch({
            error: function(model, error) {
              return app.homeController.login(error.statusText);
            }
          });
        } else {
          this.logbooks = new LogbookCollection();
          this._views['logbooks'] = new LogbooksView({
            collection: this.logbooks
          });
          return this.logbooks.fetch({
            error: function(model, error) {
              return app.homeController.login(error.statusText);
            }
          });
        }
      }
    };
    HomeController.prototype.logbookLogs = function(id) {
      var current_logbook;
      console.log("==> Route to : Logs of " + id);
      if (this.logbooks) {
        current_logbook = this.logbooks.get(id);
      } else {
        app.homeController.navigate("", true);
      }
      if (this._views["logbooks-" + id + "-logs"]) {
        return this.logs[id].fetch({
          error: function(model, error) {
            return app.homeController.login(error.statusText);
          }
        });
      } else {
        this.logs[id] = new LogCollection({
          models: [],
          options: {
            logbook: current_logbook
          }
        });
        this._views["logbooks-" + id + "-logs"] = new LogsView({
          collection: this.logs[id],
          logbook: current_logbook
        });
        return this.logs[id].fetch({
          error: function(model, error) {
            return app.homeController.login(error.statusText);
          }
        });
      }
    };
    HomeController.prototype.newLogbook = function() {
      console.log("==> Route to new Logbook");
      return this._views["logbooks-new"] = new NewLogbookView({
        model: new Logbook()
      });
    };
    HomeController.prototype.newLog = function(logbookid) {
      var current_logbook, glider_dgac_log, plane_dgac_log, ulm_ffplum_log;
      console.log("==> Route to : new Log of " + logbookid);
      if (this.logbooks) {
        current_logbook = this.logbooks.get(logbookid);
      } else {
        app.homeController.navigate("", true);
      }
      return this._views["logbook-" + logbookid + "-logs-new"] = (function() {
        switch (current_logbook.get('cat')) {
          case 'ulm_ffplum':
            ulm_ffplum_log = new UlmFfplumLog();
            ulm_ffplum_log.logbook = current_logbook;
            return new NewUlmFfplumLogView({
              model: ulm_ffplum_log,
              options: {
                logbook: current_logbook
              }
            });
          case 'plane_dgac':
            plane_dgac_log = new PlaneDgacLog();
            plane_dgac_log.logbook = current_logbook;
            return new NewPlaneDgacLogView({
              model: plane_dgac_log,
              options: {
                logbook: current_logbook
              }
            });
          case 'glider_dgac':
            glider_dgac_log = new GliderDgacLog();
            glider_dgac_log.logbook = current_logbook;
            return new NewGliderDgacLogView({
              model: glider_dgac_log,
              options: {
                logbook: current_logbook
              }
            });
          case 'plane_fcl1080':
            return new PlaneFcl1080Log(attrs, options);
          case 'helicopter_dgac':
            plane_dgac_log = new PlaneDgacLog();
            plane_dgac_log.logbook = current_logbook;
            return new NewPlaneDgacLogView({
              model: plane_dgac_log,
              options: {
                logbook: current_logbook
              }
            });
          case 'balloon_dgac':
            return new BalloonDgacLog(attrs, options);
          case 'parachute_cloudy':
            return new ParachuteCloudyLog(attrs, options);
        }
      })();
    };
    HomeController.prototype.editLog = function(logbookid, logid) {
      var current_log, current_logbook;
      console.log("==> Route to : edit Log " + logid + " of " + logbookid);
      if (this.logbooks) {
        current_logbook = this.logbooks.get(logbookid);
      } else {
        app.homeController.navigate("", true);
      }
      current_log = this.logs[logbookid].get(logid);
      return this._views["logbook-" + logbookid + "-logs-" + logid + "-edit"] = (function() {
        switch (current_logbook.get('cat')) {
          case 'ulm_ffplum':
            return new NewUlmFfplumLogView({
              model: current_log,
              options: {
                logbook: current_logbook
              }
            });
          case 'plane_dgac':
            return new NewPlaneDgacLogView({
              model: current_log,
              options: {
                logbook: current_logbook
              }
            });
          case 'glider_dgac':
            return new NewGliderDgacLogView({
              model: current_log,
              options: {
                logbook: current_logbook
              }
            });
          case 'plane_fcl1080':
            return new PlaneFcl1080Log(attrs, options);
          case 'helicopter_dgac':
            return new NewPlaneDgacLogView({
              model: current_log,
              options: {
                logbook: current_logbook
              }
            });
          case 'balloon_dgac':
            return new BalloonDgacLog(attrs, options);
          case 'parachute_cloudy':
            return new ParachuteCloudyLog(attrs, options);
        }
      })();
    };
    return HomeController;
  })();
  app.homeController = new HomeController();
  $(document).ready(function() {
    Backbone.emulateJSON = true;
    return Backbone.history.start();
  });
  this.app = app;
}).call(this);
