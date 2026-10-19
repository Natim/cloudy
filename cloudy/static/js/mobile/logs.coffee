#
# Log class
#
class Log extends Backbone.Model
  # Set the logbook_id correponding to this log collection
  # Params = { models: [...], options: {} }
  constructor: (params) ->
    super(params)
    if params && params.options && params.options.logbook
      this.logbook = params.options.logbook
      console.log("[Log] Constructor - logbook_id = " + this.logbook.id )

  url: ->
    if (this.isNew())
      return "/api/logbooks/" + this.logbook.get("id") + "?k=" + $.cookie('api_key') + "&v=3"
    else
      return "/api/logs/" + this.id + "?k=" + $.cookie('api_key') + "&v=3"

  getLabel: => throw Error("Can't call getLabel on abstract class Log")
  getFlightTime: => throw Error("Can't call getFlightTime on abstract class Log")

  getTimeAmist: (attr_array) =>
    time = 0 # defaut
    for attr in attr_array
      time  =  @get(attr) if @get(attr) != 0
    return time

  getNotZeroAmong: (attr_array) =>
    for attr in attr_array
      return attr if @get(attr) != 0
    return attr_array[0] # the first by defaut...

  validateLog: (attrs, errors) ->
    return null

  validate: (attrs) ->
    console.log(attrs)
    errors = []

    if not attrs.cdate? or attrs.ok?
      # Server side validation error
      if (attrs.ok? && attrs.ok == false)
         errors.push(attrs.data)
      else
        # Model is updated with the response from the server so validation fails...
        # => skip this case
        if (attrs.ok? && attrs.ok == true)
           return null

        @validateLog(attrs, errors)

    if _.any(errors)
      alert("Veuillez corriger les erreurs suivantes : \n\n" + errors.join("\n"))
    if not _.any(errors) then console.log("Validation : pas d'erreur")
    return if _.any(errors) then errors else null


#
# Log sub classes
#
class UlmFfplumLog extends Log
  getLabel: -> @get("ulm_imma")
  getFlightTime: -> @getTimeAmist (['flytime_cdb', 'flytime_dbl'])

  defaults:
    'date': app.ISODateString(new Date()),
    'flytime_dbl': 0, 'flytime_cdb': 0
    'obs': '','cmmts': '', 'nbrto': 0, 'nbrla': 0,

  validateLog: (attrs, errors) ->
    if (not attrs.date? || attrs.date == "")
        errors.push("Vous devez rentrer la date du vol")
      if (not attrs.ulm_imma? || attrs.ulm_imma == "")
        errors.push("Vous devez rentrer l'immatriculation")
      if (not attrs.ulm_type? || attrs.ulm_type == "")
        errors.push("Vous devez rentrer le type")

      flytime = attrs.flytime_dbl != 0 || attrs.flytime_cdb != 0
      if (flytime == false)
        errors.push("Vous devez entrer un temps de vol.")


class PlaneDgacLog extends Log
  defaults:
    'mbr_equipage_jour': 0, 'mbr_equipage_nuit': 0,
    'mono_jdbl': 0, 'mono_jcdb': 0, 'mono_ndbl': 0,'mono_ncdb': 0,
    'mul_jdbl': 0, 'mul_jcdb': 0, 'mul_jcplt': 0, 'mul_ndbl': 0, 'mul_ncdb': 0, 'mul_ncplt': 0,
    'vai_dbl': 0, 'vai_plt': 0,
    'simu': 0, 'ifr': 0, 'obs': '','cmmts': '', 'nbrto': 0, 'nbrla': 0,
    'date': app.ISODateString(new Date()),

  getLabel: -> @get("aeronef_imma")
  getFlightTime: -> @getTimeAmist (['mono_jdbl', 'mono_jcdb', 'mono_ndbl', 'mono_ncdb', 'mul_jdbl', 'mul_jcdb', 'mul_jcplt', 'mul_ndbl', 'mul_ncdb', 'mul_ncplt'])

  getMbrEqTime: => @getTimeAmist (['mbr_equipage_nuit', 'mbr_equipage_jour'])
  getMonoTime: => @getTimeAmist (['mono_jdbl', 'mono_jcdb', 'mono_ndbl', 'mono_ncdb'])
  getMulTime: => @getTimeAmist (['mul_jdbl', 'mul_jcdb', 'mul_jcplt', 'mul_ndbl', 'mul_ncdb', 'mul_ncplt'])
  getInstruTime: => @getTimeAmist (['vai_dbl', 'vai_plt'])

  validateLog: (attrs, errors) ->
    # Client side validation error
    if (not attrs.date? || attrs.date == "")
      errors.push("Vous devez rentrer la date du vol")
    if (not attrs.aeronef_imma? || attrs.aeronef_imma == "")
      errors.push("Vous devez rentrer l'immatriculation")
    if (not attrs.aeronef_type? || attrs.aeronef_type == "")
      errors.push("Vous devez rentrer le type")
    if (not attrs.natvol? || attrs.natvol == "")
      errors.push("Vous devez rentrer la nature du vol")

    mono = attrs.mono_jdbl != 0 || attrs.mono_jcdb != 0 || attrs.mono_ndbl != 0 || attrs.mono_ncdb != 0
    multi = attrs.mul_jdbl != 0 || attrs.mul_jcdb != 0 || attrs.mul_jcplt != 0 || attrs.mul_ndbl != 0 || attrs.mul_ncdb != 0 || attrs.mul_ncplt != 0
    if (mono == true && multi == true)
      errors.push("Vous ne pouvez valider un vol monomoteur et multimoteur en même temps.")
    if (mono == false && multi == false)
      errors.push("Vous devez renseigner au moins un vol monomoteur ou multimoteur.")


class GliderDgacLog extends Log
  getLabel: -> @get("glider_imma")
  getFlightTime: -> @getTimeAmist (['flytime_cdb', 'flytime_dbl', 'flytime_ins'])

  defaults:
    'date': app.ISODateString(new Date()),
    'flytime_dbl': 0, 'flytime_cdb': 0, 'flytime_ins': 0
    'obs': '','cmmts': '', 'nbrto': 0, 'nbrla': 0,

  validateLog: (attrs, errors) ->
    if (not attrs.date? || attrs.date == "")
        errors.push("Vous devez rentrer la date du vol")
      if (not attrs.glider_imma? || attrs.glider_imma == "")
        errors.push("Vous devez rentrer l'immatriculation")
      if (not attrs.glider_type? || attrs.glider_type == "")
        errors.push("Vous devez rentrer le type")
      if (not attrs.natvol? || attrs.natvol == "")
        errors.push("Vous devez rentrer la nature du vol")

      flytime = attrs.flytime_dbl != 0 || attrs.flytime_cdb != 0 || attrs.flytime_ins != 0
      if (flytime == false)
        errors.push("Vous devez entrer un temps de vol.")


class PlaneFcl1080Log extends Log
  getLabel: -> @get("aeronef_imma")

class HelicopterDgacLog extends PlaneDgacLog


class BalloonDgacLog extends Log
  getLabel: -> "NA"

class ParachuteCloudyLog extends Log
  getLabel: -> "NA"
