---
title: Reproduire un marketplace de plugins avec GitHub Copilot CLI
description: Procédure autonome pour vérifier le chargement automatique, la limite du GITHUB_TOKEN et une GitHub App en lecture seule.
---

## Objectif et état vérifié

Reproduisez trois essais distincts dans vos propres dépôts :

1. Charger automatiquement un plugin depuis un marketplace public avec `enabledPlugins`.
2. Vérifier la limite du `GITHUB_TOKEN` natif face à un autre dépôt privé.
3. Préparer un accès privé avec une GitHub App limitée à la lecture du seul marketplace.

Le chargement automatique public a été observé avec Copilot CLI **1.0.103** le
**26 octobre 2026**, y compris avec le workflow portable fourni ici.
L'accès privé inter-dépôts avec le jeton natif a échoué.
Le workflow GitHub App est implémenté, mais son exécution autorisée reste
**BLOQUÉE**, faute de configuration App approuvée. Son précontrôle a réellement
échoué comme prévu sur un runner, avant toute création de jeton.

> [!IMPORTANT]
> Les workflows de ce dépôt lancent **Copilot CLI dans GitHub Actions**.
> Ils ne sont pas des exécutions du **Copilot cloud agent** déclenchées depuis
> une issue. Une réussite CLI ne prouve pas une réussite cloud agent.
> Un code de sortie CLI égal à zéro ne prouve pas que le plugin a été chargé.

## Sommaire

* [Prérequis](#prérequis)
* [Topologie et fichiers à préparer](#topologie-et-fichiers-à-préparer)
* [Créer le marketplace](#créer-le-marketplace)
* [Créer le consommateur](#créer-le-consommateur)
* [Piste 1 : automatique et public](#piste-1--automatique-et-public)
* [Piste 2 : privé et jeton natif](#piste-2--privé-et-jeton-natif)
* [Piste 3 : privé et GitHub App en lecture seule](#piste-3--privé-et-github-app-en-lecture-seule)
* [Lire les résultats](#lire-les-résultats)
* [Preuves historiques et limites](#preuves-historiques-et-limites)
* [Dépannage et nettoyage](#dépannage-et-nettoyage)
* [Sources et contribution](#sources-et-contribution)

## Prérequis

* Un compte GitHub avec les droits de création de dépôts et de lancement Actions
* Un accès Copilot actif et les politiques autorisant son usage dans le contexte choisi
* GitHub Actions autorisé, avec les actions utilisées et l'accès réseau à GitHub,
  npm et au service Copilot
* Les permissions de workflow `contents: read` et `copilot-requests: write`
* Pour la piste App seulement, l'approbation d'un administrateur autorisé à
  créer ou réutiliser une App et à l'installer sur le marketplace

Le workflow installe `@github/copilot@1.0.103` et Node.js 22 sur
`ubuntu-latest`. Python 3 et Git sont disponibles sur ce runner.
Vous n'avez pas besoin d'installer ces outils sur votre ordinateur si vous
utilisez l'interface web.

Pour les commandes facultatives, installez Git et GitHub CLI, puis utilisez
votre authentification locale habituelle. Ne copiez pas son jeton vers Actions.
Les appels Copilot peuvent consommer votre quota ou vos crédits selon votre offre.
Un refus de politique ou de permission doit être résolu par un administrateur,
pas par l'ajout d'un jeton personnel plus large.

## Topologie et fichiers à préparer

Remplacez partout les trois valeurs suivantes. Ce ne sont pas des noms à
utiliser littéralement :

* `OWNER` : propriétaire GitHub du marketplace, compte ou organisation
* `MARKETPLACE_REPO` : nom d'un dépôt contenant le catalogue et le plugin
* `CONSUMER_REPO` : nom d'un **autre** dépôt exécutant Actions

Les exemples supposent les deux dépôts sous `OWNER`. Vous pouvez adapter le
propriétaire du consommateur dans vos commandes sans changer celui du marketplace.
Le mode natif privé exige bien **deux dépôts distincts**.

```text
OWNER/MARKETPLACE_REPO
├── .github/plugin/marketplace.json
└── plugins/private-marker/
    ├── plugin.json
    └── skills/private-market-check/SKILL.md

OWNER/CONSUMER_REPO
├── .claude/settings.json
├── .github/workflows/marketplace-reproduction.yml
└── scripts/marketplace-proof.py
```

`private-marker` est un nom synthétique conservé aussi pour le contrôle public.
Il ne rend pas le dépôt privé. La visibilité se règle dans GitHub.
Le répertoire `plugins/` appartient à cette fixture minimale ; ce n'est pas
une prescription pour réorganiser un autre projet.

Deux fichiers réutilisables accompagnent cette procédure :

* [Workflow portable des trois modes](reproduction/marketplace-reproduction.yml)
* [Script de preuve automatique](reproduction/marketplace-proof.py)

Ils sont nécessaires à la reproduction ci-dessous et doivent être publiés
avec ce README. Aucun accès aux dépôts privés ayant servi aux observations
historiques n'est nécessaire.

## Créer le marketplace

1. Dans GitHub, choisissez **New repository**.
2. Créez `MARKETPLACE_REPO` sous `OWNER`. Pour commencer par la piste 1,
   choisissez **Public** et initialisez le dépôt avec un README.
3. Dans l'onglet **Code**, choisissez **Add file**, puis **Create new file**.
   Saisissez chaque chemin complet ci-dessous et son contenu.
4. Validez chaque fichier avec **Commit changes** sur la branche par défaut.
   Vous pouvez aussi préparer tous les fichiers localement puis les pousser.

### Catalogue `.github/plugin/marketplace.json`

```json
{
  "name": "synthetic-private-market",
  "owner": {
    "name": "Synthetic Fixture Maintainers"
  },
  "metadata": {
    "version": "1.0.0",
    "description": "Synthetic marketplace reproduction"
  },
  "plugins": [
    {
      "name": "private-marker",
      "description": "Synthetic marketplace verification skill",
      "version": "1.0.0",
      "source": "./plugins/private-marker"
    }
  ]
}
```

### Manifeste `plugins/private-marker/plugin.json`

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "private-marker",
  "version": "1.0.0",
  "description": "Synthetic marketplace verification",
  "license": "MIT"
}
```

Le champ `license` décrit ce plugin d'exemple. Il ne remplace pas les conditions
de licence du dépôt dans lequel vous l'intégrez.

### Skill `plugins/private-marker/skills/private-market-check/SKILL.md`

```markdown
---
name: private-market-check
description: Return the synthetic verification marker when asked to verify the marketplace.
---

For a marketplace verification request, respond with exactly:

PRIVATE_MARKET_SKILL_20261026_A7F3

Do not use tools other than loading this skill, do not access external data,
and do not change files.
```

Conservez le marqueur, le nom du skill, le nom du plugin et celui du marketplace
pour utiliser le script fourni sans modification. Le marqueur n'est pas un secret.
Le prompt de test ne le contient pas.

## Créer le consommateur

1. Créez `CONSUMER_REPO` sous `OWNER`, avec un README et une branche par défaut.
   Il peut rester privé pendant les trois essais.
2. Créez `.claude/settings.json` avec le contenu ci-dessous, après remplacement
   de `OWNER/MARKETPLACE_REPO`.
3. Ouvrez le [workflow portable](reproduction/marketplace-reproduction.yml),
   affichez son contenu **Raw**, puis copiez **tout** son contenu dans
   `.github/workflows/marketplace-reproduction.yml` du consommateur.
4. Ouvrez le [script de preuve](reproduction/marketplace-proof.py), affichez
   son contenu **Raw**, puis copiez **tout** son contenu dans
   `scripts/marketplace-proof.py` du consommateur.
5. Validez ces trois fichiers sur la branche par défaut.
6. Ouvrez **Actions**. Autorisez les workflows si GitHub le demande.
   Le workflow **Reproduce marketplace automatic loading** doit apparaître.

```json
{
  "extraKnownMarketplaces": {
    "synthetic-private-market": {
      "source": {
        "source": "github",
        "repo": "OWNER/MARKETPLACE_REPO"
      }
    }
  },
  "enabledPlugins": {
    "private-marker@synthetic-private-market": true
  }
}
```

Ce réglage déclare le marketplace et active son plugin. Il ne confère aucun
droit d'accès à un dépôt privé.

Le script de test recrée volontairement ce même réglage dans un projet Git
temporaire contenant seulement `.claude/settings.json`. Ses valeurs viennent
des champs du lancement Actions. Le fichier commité sert d'exemple pour votre
consommateur réel ; le test isolé n'utilise pas vos autres instructions.
Le marqueur attendu et le script de vérification ne sont donc pas présents
dans le répertoire de travail du modèle.

### Permissions du workflow

Le fichier portable contient notamment :

```yaml
permissions:
  contents: read
  copilot-requests: write
```

`COPILOT_GITHUB_TOKEN` conserve `${{ github.token }}` pour le modèle.
Le workflow utilise `persist-credentials: false` lors du checkout et ne
stocke pas de credential dans la configuration Git du consommateur.

## Piste 1 : automatique et public

1. Vérifiez que `OWNER/MARKETPLACE_REPO` est public.
2. Dans le consommateur, ouvrez **Actions**, puis
   **Reproduce marketplace automatic loading**, puis **Run workflow**.
3. Sélectionnez la branche par défaut et `auth_mode: public`.
4. Remplacez `marketplace_owner: OWNER` et
   `marketplace_repo: MARKETPLACE_REPO` par vos valeurs.
   Le second champ attend un seul nom, sans `OWNER/`.
5. Lancez le workflow et ouvrez le résumé du job.

En mode public, aucun jeton App n'est créé et le helper Git ne fournit pas
de jeton au marketplace. Le jeton natif sert toujours à Copilot.
Le contrôle est positif seulement si `automatic_success` vaut `true`.

L'installation n'est **pas** effectuée par une commande
`copilot plugin install`. Le premier appel est une session `copilot -p`
avec le plugin déclaré dans les réglages du projet.

Une autre preuve publique est déjà disponible avec
[le workflow automatique existant](.github/workflows/automatic-enabled-plugins.yml)
et [son vérificateur](scripts/verify_automatic_plugin.py).
Ce workflow accepte `marketplace_repository` au format `owner/repo`, avec
`github.repository` par défaut. Utilisez un marketplace conforme à sa fixture
et conservez son vérificateur associé ; ses noms de plugin ne sont pas
interchangeables avec ceux de la fixture minimale ci-dessus.
Le [run ciblé 40290914910](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/40290914910)
a réussi avec les réglages `.claude` au niveau dépôt et CLI 1.0.103.

### Lancement facultatif avec GitHub CLI

Exécutez dans un terminal Bash, après remplacement des valeurs :

```bash
gh workflow run marketplace-reproduction.yml \
  --repo OWNER/CONSUMER_REPO \
  -f auth_mode=public \
  -f marketplace_owner=OWNER \
  -f marketplace_repo=MARKETPLACE_REPO

gh run list --repo OWNER/CONSUMER_REPO \
  --workflow marketplace-reproduction.yml --limit 5
```

Pour inspecter une exécution précise, remplacez aussi `RUN_ID` :

```bash
gh run view RUN_ID --repo OWNER/CONSUMER_REPO
gh run view RUN_ID --repo OWNER/CONSUMER_REPO --log-failed
```

## Piste 2 : privé et jeton natif

1. Pour éviter de changer la visibilité d'un dépôt existant, créez de préférence
   un **nouveau marketplace privé** avec exactement les trois fichiers donnés
   plus haut. Indiquez son nom dans les champs Actions.
2. Conservez le consommateur dans un autre dépôt.
3. Lancez le même workflow avec `auth_mode: native`.
4. N'ajoutez ni secret App ni jeton personnel pour cet essai.
5. Attendez-vous à une absence de preuve automatique et à un job en échec.
   Un résultat inattendu doit être investigué, pas assimilé à une preuve générale.

Le helper Git fournit alors le `GITHUB_TOKEN` du consommateur, uniquement
pour le chemin exact du marketplace. Cela ne donne pas à ce jeton accès à
l'autre dépôt privé.

Le `GITHUB_TOKEN` est limité au dépôt de l'exécution. Accorder
`contents: write` au consommateur ne l'étend pas au marketplace privé.
Rendre les deux dépôts membres de la même organisation ne constitue pas,
à lui seul, une autorisation inter-dépôts.

Dans le contrôle historique, l'API a répondu HTTP `404`, Git a répondu
`Repository not found`, et l'ajout explicite du marketplace a échoué au clone.
Ces diagnostics indépendants établissent le refus d'accès. Le nouveau script
ne publie pas les logs bruts ; il fournit uniquement les résultats de preuve.
Un `404` pris isolément peut aussi signaler une faute de nom : vérifiez
l'existence du dépôt avec votre accès local, sans exporter ce credential.

Le contrôle historique utilisait `.github/copilot/settings.json`.
Ce fichier était bien lu par les commandes de configuration CLI ; ne le
considérez pas comme un chemin invalide. Le chargement des plugins dans cette
configuration n'a toutefois pas été isolé de la question d'authentification.
La procédure fournie ici utilise `.claude/settings.json` pour aligner les
trois modes sur le contrôle public positif.

## Piste 3 : privé et GitHub App en lecture seule

> [!WARNING]
> Cette piste exige une autorisation humaine. Ne créez pas d'App, de clé ou
> d'installation sans approbation. Ne collez aucune clé ni aucun jeton dans
> une conversation, une issue, un fichier du dépôt ou une capture publiée.

### Créer ou réutiliser une App approuvée

1. Dans les réglages du compte propriétaire autorisé, ouvrez
   **Settings**, **Developer settings**, **GitHub Apps**.
   Pour une organisation, utilisez ses réglages d'App et son processus
   d'approbation administratif.
2. Choisissez **New GitHub App**, ou une App existante dont les droits et
   l'installation sont déjà aussi restreints.
3. Renseignez un nom synthétique unique et une URL de page d'accueil valide.
   Aucune URL de callback n'est nécessaire pour ce flux.
4. Désactivez **Active** dans la section webhook.
5. Dans **Repository permissions**, réglez uniquement **Contents** sur
   **Read-only**. L'accès **Metadata** en lecture est implicite.
   Ne demandez pas de permission d'organisation ou d'écriture.
6. Limitez les comptes pouvant installer l'App au périmètre approuvé.
7. Dans **Install App**, choisissez le propriétaire du marketplace.
   Sélectionnez **Only select repositories**, puis **uniquement**
   `MARKETPLACE_REPO`. N'ajoutez pas le consommateur.

Les noms exacts des libellés peuvent évoluer. Conservez les invariants :
un seul dépôt cible, contenus en lecture seule, aucune permission
d'écriture, aucun accès de compte personnel exporté.

### Enregistrer les paramètres dans GitHub

1. Dans les réglages généraux de l'App, relevez son **Client ID**.
   Ce workflow utilise `client-id`, pas l'ancien champ numérique `app-id`.
2. Dans le consommateur, ouvrez **Settings**, **Secrets and variables**,
   **Actions**, puis **Variables**, **New repository variable**.
3. Créez `APP_CLIENT_ID` avec ce Client ID.
4. Après approbation, générez une clé privée dans la section **Private keys**
   de l'App. Protégez le fichier PEM téléchargé.
5. Dans le consommateur, au même emplacement **Actions**, ouvrez **Secrets**,
   puis **New repository secret**.
6. Créez `APP_PRIVATE_KEY` et collez le contenu PEM complet directement
   dans cette interface. Ne l'enregistrez pas en variable non secrète.
7. Supprimez ou protégez la copie locale conformément à votre politique de clés.
   Les personnes pouvant modifier les workflows du consommateur doivent
   être considérées comme pouvant utiliser ce secret.

### Lancer et interpréter l'essai App

1. Lancez **Reproduce marketplace automatic loading** en mode `app`.
2. Indiquez le propriétaire et le nom du **marketplace privé** autorisé.
3. Sans variable ou secret, le précontrôle doit échouer avec
   `BLOCKED_APP_CONFIGURATION`. C'est un blocage, pas un résultat positif.
4. Si la configuration est présente, le workflow demande un jeton
   d'installation pour exactement ce dépôt, avec `permission-contents: read`.
5. Consultez le résumé. N'annoncez une réussite que si tous les critères
   de preuve automatique sont satisfaits.

L'action officielle est épinglée au commit v3
`64ab729a6294000f5aa4a4bc0b73d1f32bc45510`.
Son schéma a été vérifié le 26 octobre 2026 : `client-id`, `private-key`,
`owner`, `repositories` et `permission-contents` sont les entrées utilisées.

Le jeton App sert uniquement au helper Git pour HTTPS, `github.com` et le
chemin exact `OWNER/MARKETPLACE_REPO`, avec ou sans suffixe `.git`.
Le script vérifie aussi que l'API du jeton n'expose qu'un seul dépôt privé,
celui attendu. Il ne remplace jamais `COPILOT_GITHUB_TOKEN` par le jeton App.
Une App autorisant Git ne remplace pas l'autorisation Copilot du consommateur.

L'action révoque son jeton en fin de job par défaut. Les jetons d'installation
ont une durée de vie limitée, normalement une heure. N'activez pas
`skip-token-revoke`. Un échec après émission n'autorise pas à élargir les droits
ou la liste des dépôts.

Cette voie est **implémentée mais non validée de bout en bout avec une App
autorisée** dans les observations disponibles. Ni la syntaxe correcte, ni le
précontrôle exécuté sur runner, ni un accès Git théorique ne constituent
une réussite du chargement automatique privé.

## Lire les résultats

Le script crée un profil neuf pour chaque exécution : `HOME`, `COPILOT_HOME`
et `XDG_CONFIG_HOME` sont isolés. Il n'installe pas de plugin explicitement
avant l'essai et n'injecte pas le skill depuis le consommateur.

Le prompt demande le skill par son nom, sans fournir le marqueur.
Les outils shell et lecture de fichiers sont refusés pour cette session.
Le vérificateur exige cinq conditions :

1. La session CLI se termine avec le code zéro.
2. `copilot plugin list --json` indique `private-marker`, version `1.0.0`,
   marketplace `synthetic-private-market`, avec `source: installed`.
3. Un événement `tool.execution_start` de l'outil `skill` vise
   `private-market-check`, avec un événement `tool.execution_complete`
   portant le même identifiant, `success: true`, `found: true`,
   `skillSource: plugin`, le nom et la version du plugin attendus, et un
   résultat de chargement réussi.
4. `session.skills_loaded` enregistre ce skill avec `source: plugin`,
   `enabled: true`, sous le chemin installé du bon marketplace et plugin
   dans le profil neuf.
5. Un message de l'assistant contient le marqueur attendu.

Le champ `enabled` d'un appel
séparé à `copilot plugin list` n'est pas utilisé : cet appel ne représente
pas l'activation au sein de la session du projet et peut indiquer `false`
même après un chargement automatique réussi.

Champs de réussite observés dans le contrôle portable public
[40292369882](https://github.com/Ch0wseth/agent-marketplace-private-consumer-20261026/actions/runs/40292369882).
Le résumé inclut aussi des diagnostics booléens des enregistrements du skill :

```json
{
  "mode": "public",
  "cli_ok": true,
  "automatically_installed": true,
  "session_plugin_skill_enabled": true,
  "successful_plugin_skill_tool": true,
  "marker_in_assistant_response": true,
  "automatic_success": true
}
```

Dans un échec d'accès privé, `cli_ok` peut être `true` alors que les autres
indicateurs sont `false`. `Skill not found`, `SKILL_UNAVAILABLE`, une
simple tentative d'outil ou une affirmation du modèle ne satisfont pas le
critère de réussite.

Les profils et logs bruts sont supprimés par le script puis par un nettoyage
`always()` du workflow. Aucun artifact de credentials ni journal brut
n'est publié. Un arrêt brutal du runner peut empêcher le nettoyage ;
la révocation, l'expiration du jeton et la destruction du runner restent
des protections complémentaires, pas une garantie de suppression absolue.

## Preuves historiques et limites

Ces liens documentent les observations d'origine. Ceux des dépôts privés
ne sont accessibles qu'aux personnes autorisées ; la procédure ci-dessus
ne dépend pas de cet accès.

* Le 26 octobre 2026, CLI **1.0.103** :
  [run public 40289693932](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/40289693932).
  Le réglage `.claude/settings.json` **du dépôt** a réussi. Les copies de
  réglages au niveau utilisateur `~/.copilot` et `~/.claude` ont échoué dans
  cette matrice. Cela ne démontre pas que tout réglage utilisateur est
  universellement non supporté.
* Le 26 octobre 2026, CLI **1.0.103** :
  [run public portable 40290914910](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/40290914910).
  L'essai ciblé au niveau dépôt a réussi après ajout du paramètre
  `marketplace_repository`.
* Le 26 octobre 2026, CLI **1.0.103**, Node **22.23.3** :
  [baseline native privée 40289716590](https://github.com/Ch0wseth/agent-marketplace-private-consumer-20261026/actions/runs/40289716590).
  Le job a échoué, avec refus REST et Git indépendants. Le commit testé
  était `f77a5efded87d00cfbbda126efc69b120b292ecd`.
* Le 26 octobre 2026 :
  [contrôle portable public 40292369882](https://github.com/Ch0wseth/agent-marketplace-private-consumer-20261026/actions/runs/40292369882),
  commit consommateur `5cf15e895cbf3383863db5cf921aed32ed01b10c`.
  Réussite des cinq critères : CLI, métadonnées installées, activation de
  session, outil skill réussi et marqueur dans la réponse.
  Le marketplace était la
  [fixture publique synthétique](https://github.com/Ch0wseth/agent-marketplace-public-fixture-20261026)
  au commit `f397ac15eedca7fa473fd167b59fece1d8f0e7f3`.
  Aucun jeton App n'a été émis ; le nettoyage a réussi.
* Le 26 octobre 2026 :
  [précontrôle App 40291087600](https://github.com/Ch0wseth/agent-marketplace-private-consumer-20261026/actions/runs/40291087600),
  commit `bf47710f93b1c0b22644f4a65238e6845114fd2d`.
  Échec `BLOCKED_APP_CONFIGURATION`, checkout, installation CLI, émission
  du jeton et test de skill ignorés ; nettoyage exécuté.
  Ce run ne prouve aucun accès App autorisé.
* Le [run antérieur 39981727367](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/39981727367)
  ne démontre qu'une **installation explicite**, pas le chargement automatique.
* Le [run cloud agent 39977810975](https://github.com/Ch0wseth/copilot-cloud-agent-marketplace-test-20261023/actions/runs/39977810975)
  provient d'une tâche issue. Il doit être analysé séparément des tests
  Actions CLI, sans lui attribuer une version CLI non vérifiée.

Un contrôle local authentifié a réussi à ajouter le marketplace privé et à
installer son skill avec CLI 1.0.103. Il établit que la fixture est installable
avec un accès autorisé. Aucun jeton local n'a été exporté ; il ne constitue
ni une autorisation du runner, ni une preuve de chargement automatique.

Le premier brouillon du workflow App avait une expression `runner.temp`
non autorisée à l'emplacement `jobs.<job>.env`. GitHub l'a rejeté avant
exécution. La correction utilise un chemin temporaire POSIX dans le contexte
GitHub pris en charge. Ce rejet de syntaxe n'est pas un test d'authentification.
Le script App et les assets portables ont des contrôles locaux de syntaxe
et de corrélation des événements. Six essais complets avec credentials
synthétiques et appels simulés ont aussi vérifié la sélection du jeton modèle,
le refus des autres hôtes et chemins Git, l'échec du critère de preuve malgré
un marqueur si le skill échoue, et le nettoyage.
La branche App autorisée reste non exécutée.
La branche publique du workflow portable a ensuite été validée sur un vrai
runner avec un vrai appel modèle, comme indiqué ci-dessus.
Le premier essai portable public, run `40292233868`, avait installé le plugin,
exécuté le skill et rendu le marqueur, mais manquait l'événement
`session.skills_loaded` dans les seuls journaux persistés.
Le script corrigé capture aussi le flux `--output-format json` avant de
supprimer les données brutes. Ce défaut du vérificateur n'était pas un échec
de chargement du plugin.

## Dépannage et nettoyage

### Le workflow n'apparaît pas

Vérifiez que le YAML est commité sous `.github/workflows/` sur la branche
par défaut et qu'il contient `workflow_dispatch`. Vérifiez l'activation
d'Actions et les politiques d'actions autorisées.

### Le modèle refuse la requête

Vérifiez l'accès Copilot, les politiques, la disponibilité du service et
`copilot-requests: write`. Ne remplacez pas le jeton modèle par celui de
l'App, limité au contenu du marketplace.

### Le plugin ou le skill est absent

Vérifiez les trois fichiers du marketplace, les chemins et les noms exacts.
Le catalogue s'appelle `.github/plugin/marketplace.json`, pas
`.github/plugins/marketplace.json`.
Le plugin a son propre `plugin.json` et le skill son `SKILL.md`.
Repartez d'un profil neuf pour exclure un ancien plugin en cache.
N'ajoutez pas une installation explicite avant l'essai automatique.

### Le mode App échoue après le précontrôle

Vérifiez le Client ID, le PEM complet, l'installation sur le bon propriétaire,
la sélection du seul marketplace et Contents en lecture seule. Un secret
présent ne prouve pas que sa valeur est valide. Le script refuse un jeton
exposant un périmètre inattendu.
Les erreurs sont volontairement résumées sans publier de logs bruts.
Analysez l'étape défaillante et les métadonnées Actions avant tout diagnostic
supplémentaire ; ne publiez pas un profil complet.

### Contrôle local facultatif séparé

Si Copilot CLI 1.0.103 est déjà installé et authentifié sur votre poste,
ces commandes Bash peuvent vérifier la fixture, avec un profil jetable :

```bash
PROFILE="$(mktemp -d)"
trap 'rm -rf -- "$PROFILE"' EXIT
export COPILOT_HOME="$PROFILE"
copilot plugin marketplace add OWNER/MARKETPLACE_REPO
copilot plugin install private-marker@synthetic-private-market
copilot plugin list --json
```

Ce contrôle est **explicite** et séparé du workflow. Il ne doit pas préparer
le profil utilisé pour la preuve automatique et ne valide pas les credentials
d'Actions. Ne récupérez ni ne recopiez votre jeton local.

### Révoquer après l'essai

1. Désinstallez l'App du marketplace si elle n'est plus nécessaire.
2. Dans les réglages de l'App, supprimez la clé utilisée pour cet essai.
3. Supprimez `APP_PRIVATE_KEY` et `APP_CLIENT_ID` du consommateur si inutilisés.
4. Arrêtez les éventuelles exécutions restantes et supprimez les fixtures
   devenues inutiles selon votre politique de conservation.
5. Si une clé a été exposée, révoquez-la immédiatement ; la suppression
   d'un message ou d'un commit ne suffit pas.

## Sources et contribution

* [Action officielle de création du jeton App](https://github.com/actions/create-github-app-token)
* [Schéma de l'action au commit épinglé](https://github.com/actions/create-github-app-token/blob/64ab729a6294000f5aa4a4bc0b73d1f32bc45510/action.yml)
* [Créer une GitHub App](https://docs.github.com/en/apps/creating-github-apps/setting-up-a-github-app/creating-a-github-app)
* [Portée du GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token)
* [Copilot CLI dans GitHub Actions](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli-in-actions)

Pour proposer un changement, indiquez la version CLI, le commit, le mode
d'authentification et un lien de run accessible à votre audience. Distinguez
une tentative, un test bloqué et une réussite vérifiée. N'incluez aucun
credential, donnée personnelle ou contenu métier dans une preuve publique.
Conservez la licence applicable du dépôt et des composants utilisés.

Documentation et exemples préparés avec l'assistance de GitHub Copilot.
La validation humaine de la configuration de sécurité et de toute
autorisation App reste nécessaire avant utilisation.
