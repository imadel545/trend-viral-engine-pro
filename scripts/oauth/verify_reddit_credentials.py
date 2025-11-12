#!/usr/bin/env python3
"""
VÉRIFICATION FINALE des credentials Reddit
Comparez visuellement avec votre screenshot !
"""

print("=" * 70)
print("🔍 VÉRIFICATION CREDENTIALS REDDIT")
print("=" * 70)

print("\n📋 Credentials actuels dans .env :")
print("-" * 70)

from src.core.config import settings

client_id = settings.reddit_client_id
client_secret = settings.reddit_client_secret

print(f"\nCLIENT_ID:")
print(f"  Valeur: {client_id}")
print(f"  Longueur: {len(client_id)} caractères")
print(f"  Caractères: {', '.join(client_id)}")

print(f"\nCLIENT_SECRET:")
print(f"  Valeur: {client_secret}")
print(f"  Longueur: {len(client_secret)} caractères")

print("\n" + "=" * 70)
print("⚠️  COMPAREZ AVEC VOTRE SCREENSHOT Reddit !")
print("=" * 70)

print("""
Sur https://www.reddit.com/prefs/apps, vérifiez :

1. App "marruecosstore" :
   ├─ CLIENT_ID (petite ligne SOUS le nom)
   │  └─ Doit être : jxUYVxqPDnIImsx9Z_Fobg
   │     (exactement 22 caractères)
   │
   └─ SECRET (ligne après "secret")
      └─ Doit être : gXZZCxWJuQpi_XP7ZZpmGjsICrTnfQ
         (exactement 30 caractères)

2. Si les credentials sont DIFFÉRENTS :
   ├─ Copiez-les EXACTEMENT depuis Reddit
   └─ Mettez à jour .env avec les bonnes valeurs

3. Si les credentials sont IDENTIQUES :
   └─ L'app n'est probablement pas encore activée
      (attendre 15-20 minutes après création)
""")

print("=" * 70)
print("🚨 ACTION REQUISE")
print("=" * 70)
print("""
Vérifiez sur Reddit et dites-moi :

A) Les credentials sont DIFFÉRENTS
   → Partagez les NOUVEAUX credentials

B) Les credentials sont IDENTIQUES
   → Attendons 15 min que Reddit active l'app

C) Vous n'êtes pas sûr
   → Partagez un nouveau screenshot de l'app
""")
