from django.dispatch import Signal

# paid_registration_complete = Signal(providing_args=['user']) # TODO
# free_registration_complete = Signal(providing_args=[])
# upgrade_plan_complete = Signal(providing_args=['user'])
paid_registration_complete = Signal()
free_registration_complete = Signal()
upgrade_plan_complete = Signal()
