# --- Edit me if you want to ---

# Achievement_date
# 1 ------- n autofill
# 0 no validation
# -1 ------ manual input

LICENSES = {
    "medical": {  # Certificates medicaux
        "full": "Certificates medicaux",
        "list": {
            "M1": {
                "full": "Certificate Médical de Classe 1",
                "duration": "-1",
            },
            "M2": {
                "full": "Certificate Médical de Classe 2",
                "duration": "-1",
            },
        },
    },
    "qualifications": {
        "Avion": {
            "wo_expiry": {  # Licences et qualifications sans date d'expiration
                "full": "Licences et qualifications sans date d'expiration",
                "list": {},
            },
            "w_expiry": {  # Qualifications avec date d'expiration
                "full": "Qualifications avec date d'expiration",
                "list": {},
            },
            "class_type": {  # Qualifications de classe et de type
                "full": "Qualifications de classe et de type",
                "list": {},
            },
        },
        "Planeur": {},
        "Helico": {},
        "Ulm": {},
        "Ballon": {},
        "Parachute": {},
    },
}
