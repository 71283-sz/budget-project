import calendar
import csv
import os
import shutil
from datetime import date

FICHIER = "budget.csv"
FICHIER_SAUVEGARDE = "budget_sauvegarde.csv"
FICHIER_LIMITES = "limites.csv"
CATEGORIES_DEPENSES = ["activité", "nourriture", "vêtements", "makeup/soin",
                       "abonnement", "autres"]
CATEGORIES_REVENUS = ["salaire", "job étudiant", "aide de la famille", "autre"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
LIBELLES = {"revenu": "entrée", "depense": "dépense", "economie": "épargne",
            "debut": "début", "fin": "fin"}


# ---------- Mois et jours ----------

def mois_actuel():
    aujourdhui = date.today()
    return f"{aujourdhui.year}-{aujourdhui.month:02d}"


def mois_precedent(mois):
    annee, numero = (int(x) for x in mois.split("-"))
    numero -= 1
    if numero == 0:
        numero = 12
        annee -= 1
    return f"{annee}-{numero:02d}"


def nom_du_mois(mois):
    annee, numero = mois.split("-")
    return f"{MOIS[int(numero) - 1]} {annee}"


def formater_date(mois, jour):
    numero = mois.split("-")[1]
    return f"{jour:02d}/{numero}"


def demander_mois(consigne, mois_par_defaut):
    while True:
        reponse = input(consigne).strip()
        if reponse == "":
            return mois_par_defaut
        try:
            numero, annee = reponse.split("/")
            numero, annee = int(numero), int(annee)
            if 1 <= numero <= 12 and 2000 <= annee <= 2100:
                return f"{annee}-{numero:02d}"
        except ValueError:
            pass
        print("Je n'ai pas compris. Écris le mois comme ceci : 11/2026.")


def demander_jour(mois):
    annee, numero = (int(x) for x in mois.split("-"))
    nombre_de_jours = calendar.monthrange(annee, numero)[1]

    # "Aujourd'hui" n'a de sens que si on est dans le mois en cours
    aujourdhui = date.today().day if mois == mois_actuel() else None

    if aujourdhui:
        consigne = f"Quel jour ? (Entrée = aujourd'hui, le {aujourdhui}) : "
    else:
        consigne = f"Quel jour du mois (1 à {nombre_de_jours}) ? "

    while True:
        reponse = input(consigne).strip()
        if reponse == "" and aujourdhui:
            return aujourdhui
        if reponse.isdigit() and 1 <= int(reponse) <= nombre_de_jours:
            return int(reponse)
        print(f"Tape un jour entre 1 et {nombre_de_jours}.")


# ---------- Questions à l'utilisateur ----------

def demander_categorie(question, categories):
    print(f"\n{question}")
    for i, nom in enumerate(categories, start=1):
        print(f"  {i}. {nom}")

    while True:
        reponse = input("Ton choix (numéro) : ")
        if reponse.isdigit() and 1 <= int(reponse) <= len(categories):
            return categories[int(reponse) - 1]
        print(f"Tape un numéro entre 1 et {len(categories)}.")


def demander_montant(question, autoriser_zero=False, autoriser_negatif=False):
    while True:
        reponse = input(question).replace(",", ".")
        try:
            montant = float(reponse)
        except ValueError:
            print("Je n'ai pas compris. Tape un nombre, par exemple 12.50.")
            continue
        if montant < 0 and not autoriser_negatif:
            print("Le montant ne peut pas être négatif.")
            continue
        if montant == 0 and not (autoriser_zero or autoriser_negatif):
            print("Le montant doit être plus grand que 0.")
            continue
        return montant


# ---------- Fichiers ----------

def enregistrer(mois, type_operation, categorie, montant, jour=""):
    with open(FICHIER, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([mois, type_operation, categorie, montant, jour])


def lire_operations(mois):
    """Renvoie une liste de (type, catégorie, montant, jour). Le jour vaut None s'il n'est pas noté."""
    operations = []
    if os.path.exists(FICHIER):
        with open(FICHIER, newline="", encoding="utf-8") as f:
            for ligne in csv.reader(f):
                if ligne[0] == mois:
                    jour = None
                    if len(ligne) > 4 and ligne[4] != "":
                        jour = int(ligne[4])
                    operations.append((ligne[1], ligne[2], float(ligne[3]), jour))
    return operations


def lire_toutes_les_lignes():
    lignes = []
    if os.path.exists(FICHIER):
        with open(FICHIER, newline="", encoding="utf-8") as f:
            lignes = [ligne for ligne in csv.reader(f) if ligne]
    return lignes


def ecrire_toutes_les_lignes(lignes):
    # Copie de sécurité avant de modifier le fichier
    if os.path.exists(FICHIER):
        shutil.copy(FICHIER, FICHIER_SAUVEGARDE)
    with open(FICHIER, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(lignes)


def lire_limites():
    limites = {}
    if os.path.exists(FICHIER_LIMITES):
        with open(FICHIER_LIMITES, newline="", encoding="utf-8") as f:
            for ligne in csv.reader(f):
                limites[ligne[0]] = float(ligne[1])
    return limites


def sauver_limites(limites):
    with open(FICHIER_LIMITES, "w", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        for categorie, limite in limites.items():
            ecrivain.writerow([categorie, limite])


# ---------- Calculs ----------

def calculer_bilan(mois):
    operations = lire_operations(mois)

    debut = None
    fin = None
    revenus = 0
    economies = 0
    depenses = {}

    for type_operation, categorie, montant, jour in operations:
        if type_operation == "debut":
            debut = montant          # si on le note deux fois, le dernier gagne
        elif type_operation == "fin":
            fin = montant
        elif type_operation == "revenu":
            revenus += montant
        elif type_operation == "economie":
            economies += montant
        elif type_operation == "depense":
            depenses[categorie] = depenses.get(categorie, 0) + montant

    total_depenses = sum(depenses.values())
    disponible = (debut or 0) + revenus
    reste = disponible - total_depenses - economies

    ecart = None
    if debut is not None and fin is not None:
        ecart = fin - reste

    return {
        "vide": not operations,
        "debut": debut,
        "fin": fin,
        "revenus": revenus,
        "economies": economies,
        "depenses": depenses,
        "total_depenses": total_depenses,
        "disponible": disponible,
        "reste": reste,
        "ecart": ecart,
    }


# ---------- Actions ----------

def ajouter_revenu(mois):
    categorie = demander_categorie("D'où vient cet argent ?", CATEGORIES_REVENUS)
    montant = demander_montant("Combien as-tu reçu (en €) ? ")
    jour = demander_jour(mois)
    enregistrer(mois, "revenu", categorie, montant, jour)
    print(f"\n✔ C'est noté : +{montant:.2f} € ({categorie}) le {formater_date(mois, jour)}.")


def ajouter_depense(mois):
    categorie = demander_categorie("Dans quelle catégorie ?", CATEGORIES_DEPENSES)
    montant = demander_montant("Combien as-tu dépensé (en €) ? ")
    jour = demander_jour(mois)
    enregistrer(mois, "depense", categorie, montant, jour)
    print(f"\n✔ C'est noté : -{montant:.2f} € ({categorie}) le {formater_date(mois, jour)}.")
    verifier_limite(mois, categorie)


def ajouter_economie(mois):
    montant = demander_montant("Combien mets-tu de côté (en €) ? ")
    jour = demander_jour(mois)
    enregistrer(mois, "economie", "épargne", montant, jour)
    print(f"\n✔ C'est noté : {montant:.2f} € mis de côté le {formater_date(mois, jour)}.")


def indiquer_solde(mois):
    choix = demander_categorie(
        "Quel montant veux-tu noter ?",
        ["Ce que j'ai au début du mois", "Ce que j'ai à la fin du mois"])

    if choix.startswith("Ce que j'ai au début"):
        precedent = calculer_bilan(mois_precedent(mois))["fin"]
        if precedent is not None:
            reponse = input(f"\nÀ la fin du mois dernier, tu avais {precedent:.2f} €. "
                            "Reprendre ce montant ? (o/n) : ").strip().lower()
            if reponse == "o":
                enregistrer(mois, "debut", "solde", precedent)
                print(f"\n✔ C'est noté : tu commences le mois avec {precedent:.2f} €.")
                return
        montant = demander_montant(
            "\nCombien as-tu au début du mois (en €, sans compter ton épargne) ? ",
            autoriser_zero=True, autoriser_negatif=True)
        enregistrer(mois, "debut", "solde", montant)
        print(f"\n✔ C'est noté : tu commences le mois avec {montant:.2f} €.")
    else:
        montant = demander_montant(
            "\nCombien as-tu à la fin du mois (en €, sans compter ton épargne) ? ",
            autoriser_zero=True, autoriser_negatif=True)
        enregistrer(mois, "fin", "solde", montant)
        print(f"\n✔ C'est noté : tu finis le mois avec {montant:.2f} €.")


def verifier_limite(mois, categorie):
    limites = lire_limites()
    if categorie not in limites:
        return
    depense = calculer_bilan(mois)["depenses"].get(categorie, 0)
    reste = limites[categorie] - depense
    if reste >= 0:
        print(f"  Il te reste {reste:.2f} € pour « {categorie} » ce mois-ci.")
    else:
        print(f"  ⚠ Tu as dépassé ta limite « {categorie} » de {-reste:.2f} €.")


def gerer_limites():
    limites = lire_limites()

    print("\n--- Tes limites par mois ---")
    for categorie in CATEGORIES_DEPENSES:
        if categorie in limites:
            print(f"  {categorie:<16} {limites[categorie]:>8.2f} €")
        else:
            print(f"  {categorie:<16} (pas de limite)")

    categorie = demander_categorie(
        "Pour quelle catégorie veux-tu changer la limite ?", CATEGORIES_DEPENSES)
    limite = demander_montant(
        f"Limite par mois pour « {categorie} » en € (0 pour l'enlever) : ",
        autoriser_zero=True)

    if limite == 0:
        limites.pop(categorie, None)
        print(f"\n✔ Plus de limite pour « {categorie} ».")
    else:
        limites[categorie] = limite
        print(f"\n✔ Limite de {limite:.2f} € par mois pour « {categorie} ».")
    sauver_limites(limites)


def afficher_liste(mois):
    types_a_afficher = ("revenu", "depense", "economie")
    operations = [o for o in lire_operations(mois) if o[0] in types_a_afficher]

    if not operations:
        print(f"\nAucune opération notée pour {nom_du_mois(mois)}.")
        return

    # Tri par jour (les opérations sans jour, notées avant la v6, passent en premier)
    operations.sort(key=lambda o: o[3] or 0)

    print(f"\n--- Opérations de {nom_du_mois(mois)} ---")
    for type_operation, categorie, montant, jour in operations:
        date_texte = formater_date(mois, jour) if jour else "  ?  "
        if type_operation == "revenu":
            signe = "+"
        elif type_operation == "depense":
            signe = "-"
        else:
            signe = "→"
        print(f"  {date_texte}  {signe} {montant:>8.2f} €  {categorie}")


def corriger_operation(mois):
    lignes = lire_toutes_les_lignes()
    indices = [i for i, ligne in enumerate(lignes) if ligne[0] == mois]

    if not indices:
        print(f"\nAucune opération notée pour {nom_du_mois(mois)}.")
        return

    print(f"\n--- Opérations de {nom_du_mois(mois)} (dans l'ordre où tu les as notées) ---")
    for numero, i in enumerate(indices, start=1):
        ligne = lignes[i]
        jour = int(ligne[4]) if len(ligne) > 4 and ligne[4] != "" else None
        date_texte = formater_date(mois, jour) if jour else "  -  "
        print(f"  {numero:>2}. {date_texte}  {LIBELLES[ligne[1]]:<8}"
              f"{float(ligne[3]):>9.2f} €  {ligne[2]}")

    while True:
        reponse = input("\nNuméro de l'opération à corriger (Entrée pour annuler) : ").strip()
        if reponse == "":
            return
        if reponse.isdigit() and 1 <= int(reponse) <= len(indices):
            break
        print(f"Tape un numéro entre 1 et {len(indices)}.")

    position = indices[int(reponse) - 1]
    ligne = lignes[position]
    while len(ligne) < 5:
        ligne.append("")
    type_operation = ligne[1]

    actions = ["Supprimer cette opération", "Changer le montant"]
    if type_operation in ("revenu", "depense"):
        actions.append("Changer la catégorie")
    if type_operation in ("revenu", "depense", "economie"):
        actions.append("Changer le jour")
    actions.append("Annuler")

    choix = demander_categorie("Que veux-tu faire ?", actions)

    if choix == "Annuler":
        print("\nRien n'a été changé.")
        return

    if choix == "Supprimer cette opération":
        confirmation = input("Sûr de vouloir la supprimer ? (o/n) : ").strip().lower()
        if confirmation != "o":
            print("\nRien n'a été changé.")
            return
        del lignes[position]
        message = "✔ L'opération est supprimée."
    elif choix == "Changer le montant":
        solde = type_operation in ("debut", "fin")
        ligne[3] = demander_montant("Nouveau montant (en €) : ",
                                    autoriser_zero=solde, autoriser_negatif=solde)
        message = "✔ Le montant est corrigé."
    elif choix == "Changer la catégorie":
        if type_operation == "revenu":
            categories = CATEGORIES_REVENUS
        else:
            categories = CATEGORIES_DEPENSES
        ligne[2] = demander_categorie("Nouvelle catégorie ?", categories)
        message = "✔ La catégorie est corrigée."
    else:
        ligne[4] = demander_jour(mois)
        message = "✔ Le jour est corrigé."

    ecrire_toutes_les_lignes(lignes)
    print(f"\n{message}")
    print(f"(Une copie de l'ancienne version est dans {FICHIER_SAUVEGARDE}.)")


def afficher_bilan(mois):
    bilan = calculer_bilan(mois)
    if bilan["vide"]:
        print(f"\nRien de noté pour {nom_du_mois(mois)}.")
        return

    limites = lire_limites()
    depenses = bilan["depenses"]
    economies = bilan["economies"]
    total_depenses = bilan["total_depenses"]
    reste = bilan["reste"]

    print(f"\n=== Bilan de {nom_du_mois(mois)} ===")
    if bilan["debut"] is not None:
        print(f"Argent au début    {bilan['debut']:>10.2f} €")
    print(f"Argent reçu        {bilan['revenus']:>10.2f} €")

    print("\nDépenses :")
    categories = set(depenses) | set(limites)
    if categories:
        for categorie in sorted(categories, key=lambda c: depenses.get(c, 0), reverse=True):
            total = depenses.get(categorie, 0)
            ligne = f"  {categorie:<16} {total:>8.2f} €"
            if categorie in limites:
                ligne += f"  (limite : {limites[categorie]:.2f} €)"
                if total > limites[categorie]:
                    ligne += "  ⚠ dépassée"
            print(ligne)
    else:
        print("  (aucune)")
    print(f"Total dépensé      {total_depenses:>10.2f} €")

    print(f"\nMis de côté        {economies:>10.2f} €")
    print("-" * 32)
    if bilan["fin"] is not None:
        print(f"Reste prévu        {reste:>10.2f} €")
        print(f"Argent à la fin    {bilan['fin']:>10.2f} €")
    else:
        print(f"Reste disponible   {reste:>10.2f} €")

    # Les comptes tombent-ils juste ?
    ecart = bilan["ecart"]
    if ecart is not None:
        if abs(ecart) < 0.005:
            print("\n✔ Les comptes tombent juste : tout est bien noté.")
        elif ecart < 0:
            print(f"\n⚠ Il te manque {-ecart:.2f} € : une dépense n'est peut-être pas notée.")
        else:
            print(f"\n⚠ Tu as {ecart:.2f} € de plus que prévu : "
                  "une entrée d'argent n'est peut-être pas notée.")
    elif bilan["fin"] is not None:
        print("\nNote ce que tu avais au début du mois pour vérifier que les comptes tombent juste.")

    # Phrase de résumé
    disponible = bilan["disponible"]
    if reste < 0:
        print("\n⚠ Attention : tu as dépensé et épargné plus que l'argent dont tu disposais.")
    elif disponible > 0:
        print(f"\nCe mois-ci, tu as dépensé {total_depenses / disponible * 100:.0f} % "
              f"et mis de côté {economies / disponible * 100:.0f} % de l'argent dont tu disposais.")


def comparer_mois(mois):
    precedent = mois_precedent(mois)
    autre = demander_mois(
        f"\nAvec quel mois comparer ? (ex. 10/2026, Entrée pour {nom_du_mois(precedent)}) : ",
        precedent)

    if autre == mois:
        print("C'est le même mois, il n'y a rien à comparer.")
        return

    a = calculer_bilan(mois)
    b = calculer_bilan(autre)
    if b["vide"]:
        print(f"\nRien de noté pour {nom_du_mois(autre)}.")
        return

    nom_a, nom_b = nom_du_mois(mois), nom_du_mois(autre)
    print(f"\n=== {nom_a} comparé à {nom_b} (en €) ===")
    print(f"{'':<18}{nom_a:>16}{nom_b:>16}{'Différence':>12}")

    lignes = []
    if a["debut"] is not None and b["debut"] is not None:
        lignes.append(("Argent au début", a["debut"], b["debut"]))
    lignes += [
        ("Argent reçu", a["revenus"], b["revenus"]),
        ("Total dépensé", a["total_depenses"], b["total_depenses"]),
        ("Mis de côté", a["economies"], b["economies"]),
        ("Reste", a["reste"], b["reste"]),
    ]
    if a["fin"] is not None and b["fin"] is not None:
        lignes.append(("Argent à la fin", a["fin"], b["fin"]))

    for libelle, valeur_a, valeur_b in lignes:
        print(f"{libelle:<18}{valeur_a:>16.2f}{valeur_b:>16.2f}{valeur_a - valeur_b:>+12.2f}")

    categories = sorted(set(a["depenses"]) | set(b["depenses"]))
    if categories:
        print("\nDépenses par catégorie :")
        for categorie in categories:
            valeur_a = a["depenses"].get(categorie, 0)
            valeur_b = b["depenses"].get(categorie, 0)
            print(f"  {categorie:<16}{valeur_a:>16.2f}{valeur_b:>16.2f}{valeur_a - valeur_b:>+12.2f}")

    print(f"\nDifférence = {nom_a} moins {nom_b}.")


# ---------- Menu ----------

def menu():
    mois = mois_actuel()
    while True:
        print(f"\n=== MON BUDGET : {nom_du_mois(mois)} ===")
        print("  1. Noter une entrée d'argent")
        print("  2. Noter une dépense")
        print("  3. Mettre de l'argent de côté")
        print("  4. Noter ce que j'ai au début / à la fin du mois")
        print("  5. Voir le bilan du mois")
        print("  6. Voir la liste des opérations du mois")
        print("  7. Gérer mes limites par catégorie")
        print("  8. Comparer avec un autre mois")
        print("  9. Changer de mois")
        print("  10. Corriger ou supprimer une opération")
        print("  11. Quitter")
        choix = input("Ton choix : ")

        if choix == "1":
            ajouter_revenu(mois)
        elif choix == "2":
            ajouter_depense(mois)
        elif choix == "3":
            ajouter_economie(mois)
        elif choix == "4":
            indiquer_solde(mois)
        elif choix == "5":
            afficher_bilan(mois)
        elif choix == "6":
            afficher_liste(mois)
        elif choix == "7":
            gerer_limites()
        elif choix == "8":
            comparer_mois(mois)
        elif choix == "9":
            print(f"\nTu es sur : {nom_du_mois(mois)}")
            mois = demander_mois(
                "Nouveau mois (ex. 11/2026) ou Entrée pour ne pas changer : ", mois)
        elif choix == "10":
            corriger_operation(mois)
        elif choix == "11":
            print("À bientôt !")
            break
        else:
            print("Tape un numéro entre 1 et 11.")


menu()
