# Positionnement autonome avec calibration PID

Ce projet fonctionne sans ordinateur apres son installation. Les boutons de la
micro:bit commandent la calibration, les essais PID, la distance et le depart.

## Installation initiale

Depuis la racine du depot :

```sh
make install PROJECT=position_1m
```

Debranchez ensuite le cable USB. Le robot fonctionne avec les batteries de la
Maqueen.

## Commandes des boutons

### Au repos

- `A` : lancer le parcours avec la distance memorisee.
- `B` : choisir une distance entre 10 cm et 500 cm, par pas de 10 cm.
- `A+B` : ouvrir le menu calibration.

### Choix de distance

- `A` : ajouter 10 cm.
- `B` : sauvegarder et revenir au repos.

### Menu calibration

- `A` : commencer la mesure manuelle des ticks sur exactement 1 metre.
- `B` : ouvrir le mode de calibration PID.

### Mesure manuelle des ticks

1. Placez le robot au debut d'une distance mesuree de exactement 1 metre.
2. Au repos, appuyez sur `A+B`, puis sur `A`.
3. Faites rouler manuellement le robot jusqu'au repere de 1 metre, sans le
   soulever.
4. Appuyez sur `B` a l'arrivee.

Le robot sauvegarde la moyenne absolue des deux encodeurs comme
`ticks_per_meter`, puis ouvre automatiquement le mode de calibration PID.

### Calibration PID par essais

1. Replacez manuellement le robot au depart.
2. Appuyez sur `A` pour lancer un essai motorise.
3. Le robot parcourt la distance memorisee, s'arrete, mesure son depassement et
   l'ecart entre les roues, ajuste les gains puis les sauvegarde.
4. Replacez-le au depart et appuyez de nouveau sur `A`.
5. Repetez plusieurs fois, puis appuyez sur `B` pour terminer.

Pendant tout mouvement, `A+B` provoque un arret d'urgence.

## Parametres memorises

Le fichier `position_config.txt` est sauvegarde dans la micro:bit :

```text
ticks_per_meter
calibrated
distance_cm
kp_position
ki_position
kd_position
kp_heading
kd_heading
pid_trials
```

Pour recuperer ces valeurs apres avoir reconnecte le cable USB :

```sh
make read-config PROJECT=position_1m
```

Le fichier est alors copie dans `position_1m/position_config.txt`.

## Adaptation PID utilisee

Il n'existe pas de formule permettant de calculer exactement les gains PID a
partir d'un seul parcours manuel. Le parcours manuel calibre uniquement les
ticks par metre.

Chaque essai motorise mesure ensuite :

```text
depassement = position_finale - position_cible
erreur_direction = encodeur_gauche - encodeur_droit
```

- Si le robot depasse, `Kd_position` augmente et `Kp_position` diminue
  legerement.
- S'il s'arrete trop tot, `Kp_position` augmente.
- S'il derive, les gains de correction de direction augmentent.
- Les nouvelles valeurs sont sauvegardees apres chaque essai.

`Ki_position` reste initialement nul pour eviter l'accumulation d'erreur et le
depassement. Il ne doit etre ajoute qu'apres observation d'une erreur
persistante.

## Limites physiques

Les encodeurs mesurent la rotation des roues, pas la position absolue sur le
sol. Un glissement, un deplacement du robot en le soulevant ou une roue bloquee
fausse la position.

Pour une garantie physique stricte du point d'arrivee, il faudra ajouter un
repere externe, par exemple une ligne au sol detectee par les capteurs de la
Maqueen.
