# Hooks where we can set call redis for our future Dashboard

from django.core.mail import mail_managers


def post_payed_registration(sender, user, **kwargs):
    title = "Nouvel utilisateur [PAYANT] - New [PAYED] user"
    body = "Enregistrement d'un nouvel utilisateur [First Class] : {name}\nAdresse mail : {mail}\n\nNew [PAYED] user signed up: {name}\nMail: {mail}".format(
        name=user.get_full_name(), mail=user.email
    )
    mail_managers(title, body, fail_silently=True)


def post_free_registration(sender, **kwargs):
    title = "Nouvel utilisateur [GRATUIT] - New [FREE] user"
    body = "Enregistrement d'un nouvel utilisateur [Economy Class] : {name}\nAdresse mail : {mail}\n\nNew [FREE] user signed up: {name}\nMail: {mail}".format(
        name=sender.get_full_name(), mail=sender.email
    )
    mail_managers(title, body, fail_silently=True)


def post_payed_upgrade(sender, user, **kwargs):
    title = "Mise a jour [PAYANT] d'un utilisateur - New [PAYED UPGRADE] user"
    body = "Mise a jour [PAYANT] d'un utilisateur : {name}\nAdresse mail : {mail}\n\nNew [PAYED UPGRADE] user: {name}\nMail: {mail}".format(
        name=user.get_full_name(), mail=user.email
    )
    mail_managers(title, body, fail_silently=True)
