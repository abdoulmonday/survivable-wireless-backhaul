# Guide pédagogique et préparation jury — versions 0.1 → 0.3

## 1. Comment présenter le projet en 60 secondes

« J'ai implémenté en Python un modèle de dimensionnement de liaisons de backhaul sans fil inspiré de Raayatpanah et al. (2023). Le but est de choisir des capacités radio au moindre coût en préservant des demandes de trafic après la panne d'un relais et en imposant un seuil de fiabilité sous hypothèse d'indépendance. J'ai d'abord programmé un MILP monolithique, puis séparé les choix de capacité et les flux avec Benders et un sous-problème LP de faisabilité. Enfin, j'ai ajouté des coupes nécessaires de capacité sur des ensembles de nœuds, pour éliminer certaines mauvaises configurations plus tôt. Mes tests comparent les objectifs optimaux sur de petits graphes synthétiques. Je ne prétends pas encore reproduire le solveur accéléré complet ni les benchmarks SNDlib du papier. »

## 2. Vocabulaire réseau

- **Backhaul** : transport entre réseau d'accès et réseau central.
- **Nœud** : station/équipement de commutation, non un terminal utilisateur.
- **Arc orienté** `(u,v)` : liaison de capacité installable, en Mbit/s.
- **Fiabilité** : probabilité que les capacités conçues soient réalisables malgré les fluctuations radio, **pas** disponibilité annuelle mesurée.
- **Survivabilité** : capacité de conserver une fraction du trafic sous des pannes explicites.
- **Diversification** : imposer plusieurs chemins disjoints via la fraction maximale `sigma` en fonctionnement intact.
- **Réservation** : dimensionner assez de capacité pour le trafic rerouté après panne, pilotée par `alpha`.

## 3. V0.1 : MILP direct — pourquoi et comment

La version initiale construisait directement `solve(...)` avec deux familles de variables : les binaires `y[e,j]` pour la configuration radio et les réelles positives `x[h,k,e]` pour les flux par demande et scénario. Le solveur SciPy/HiGHS `milp` optimise tout simultanément. **Pourquoi ?** C'est la formulation de référence pour valider toute décomposition plus compliquée.

**Variables** : `y=1` si le choix radio `j` est activé sur l'arc `e`; `x=10` signifie 10 Mbit/s de la demande `k` empruntent `e` lorsque le scénario `h` survient.

**Objectif** : `min sum_{e,j} cost_j y[e,j]` ; le trafic lui-même ne coûte pas dans cette fonction objectif.

**Conservation** : à la source, débit sortant moins entrant égal à la demande préservée ; à la destination l'opposé ; à un relais, zéro. La demande préservée est `d` avant panne et `alpha*d` après panne.

**Capacité** : `sum_k x[h,k,e] <= sum_j B_j y[e,j]` dans chaque scénario opérationnel.

**Radio** : `sum_j y[e,j] <= 1` empêche de choisir plusieurs configurations du même arc.

**Fiabilité** : `sum_{e,j} log(rho_j) y[e,j] >= log(1-epsilon)` suppose l'indépendance des liaisons et la probabilité cumulative `rho` d'une capacité au moins égale à celle conçue. Une liaison absente contribue un facteur 1 au produit.

**Diversification** : flux d'une demande sur chaque arc et somme des flux sortants de tout nœud intermédiaire `<= sigma*d` dans le scénario intact. Un réseau avec `sigma=0.5` exige un partage suffisant du trafic et généralement au moins deux chemins disjoints.

**Limite** : le nombre de variables `x` augmente avec nœuds, demandes et scénarios ; le MILP entier peut devenir coûteux.

## 4. V0.2 : structure réelle du code

### `model.py`

`@dataclass(frozen=True)` définit `Demand(source,target,rate)` et `Option(bandwidth,efficiency,probability,cost)` : ces objets de données ne sont pas modifiés après création. `Option.capacity` multiplie MHz × bit/s/Hz pour donner Mbit/s. `Instance` stocke la topologie, les demandes, les options radio, `sigma`, `alpha`, `epsilon` et la liste des relais protégés.

`self.scenarios = [None] + protect_nodes` : `None` signifie « aucune panne ». Une panne retire un relais et tous les arcs incidents. Les demandes dont une extrémité tombe en panne sont ignorées pour ce scénario.

`self.ykeys` énumère toutes les décisions binaires `(arc, option)` et `self.yindex` donne l'indice numérique dans le vecteur d'optimisation. `self.xkeys` et `self.xindex` font la même chose pour `(panne, demande, arc)`. Pourquoi des dictionnaires d'indices ? Les solveurs attendent des vecteurs/matrices numériques ; les clés nommées restent lisibles pour nous.

`flow_matrices()` assemble des matrices `Aeq, beq, Aub, d, B` sous la forme `Aeq*x=beq`, `Aub*x <= d+B*y`. La première encode le bilan des flux. La seconde regroupe diversification et capacité, où `B*y` indique les capacités installées. `master(cuts)` impose les contraintes sur `y` uniquement. `solve_monolithic()` assemble le système joint `y,x` et appelle `scipy.optimize.milp`.

### `benders.py`

`elastic_oracle(inst, y)` fixe la conception radio et crée un LP dont les variables sont `[x, s_plus, s_minus, r]`. Les slacks `s_plus, s_minus` relâchent les bilans de flux, et `r` relâche les contraintes de type `<=`; leur somme est minimisée. L'objectif optimal `theta(y)=0` signifie qu'aucune violation n'est nécessaire : le flux est faisable.

Les `marginals` HiGHS représentent la sensibilité de l'objectif LP aux seconds membres. `gradient = lp.ineqlin.marginals @ B` donne un sous-gradient de `theta` par rapport à `y`. On en déduit une coupe nécessaire pour tout design faisable : `gradient @ y <= gradient @ yhat - theta(yhat)`.

`solve_benders()` répète : (a) résoudre le problème maître MILP, (b) interroger l'oracle, (c) retourner la solution si violation nulle, sinon (d) ajouter la coupe. Un maître optimal fournit une borne inférieure sur le coût, et une conception faisable de coût égal est optimale.

**Question jury : pourquoi ne pas simplement interdire le `yhat` non faisable ?** Une coupe issue des duales exclut potentiellement beaucoup de designs inadéquats simultanément : elle exploite la structure du problème.

## 5. V0.3 : `cutsets.py` et `accelerated.py`

### Pourquoi les coupes de capacité sont valides

Choisissons un ensemble `S` de nœuds qui fonctionnent. Toute demande ayant sa source dans `S` et sa destination hors de `S` doit traverser au moins une liaison **sortante** de `S`. Par conservation des flots, la capacité totale des arcs sortants doit donc être au moins égale à la somme de ces demandes. Les demandes dans l'autre sens n'enlèvent rien à cette obligation sur les arcs sortants du graphe orienté.

Exemple : demande `A→D` de 30 Mbit/s. Si `S={A,B,C}`, les seules sorties pertinentes sont `B→D` et `C→D` ; il faut `capacity(B,D)+capacity(C,D)>=30`. Si B tombe en panne, il faut `capacity(C,D)>=alpha*30`. Cette inégalité est **nécessaire**, pas suffisante pour toutes les demandes simultanément.

### `generate_cutsets(inst, max_nodes=12)`

`combinations(live,size)` énumère tous les sous-ensembles propres et non vides `S` des nœuds encore actifs dans un scénario. Pour chaque demande de `S` vers l'extérieur, elle additionne le débit intact ou préservé. Elle construit un vecteur `coeff` qui vaut `-capacity(option)` sur les décisions des arcs sortants de `S`, puis rend la contrainte `coeff @ y <= -required_traffic`. Les signes négatifs servent seulement à correspondre au format `<=` du maître.

**Complexité :** jusqu'à `2^n-2` sous-ensembles par scénario, donc croissance exponentielle. Ce séparateur est limité volontairement à de petits graphes. Il ne remplace pas la procédure de séparation avancée de l'article.

### `separate_cutsets(inst,y)`

Teste les inégalités sur la conception actuelle `y`, calcule les violations `coeff@y-rhs`, retire celles non violées, garde la version la plus forte lorsque des inégalités ont les mêmes coefficients, puis trie et renvoie les plus violées, dans la limite demandée.

### `solve_accelerated(inst)`

À chaque tour, résout `inst.master(cuts)`. Avant l'oracle LP, appelle `separate_cutsets`. S'il existe des coupes violées, les ajoute, enregistre les statistiques et repart au maître. Sinon appelle l'oracle Benders habituel. S'il confirme la faisabilité, termine ; sinon ajoute la coupe duale. Il suit `cutset_cuts`, `benders_cuts`, `oracle_calls`, `iterations`, ainsi que l'historique d'optimisation.

**Pourquoi cela peut accélérer ?** Les coupes de capacité sont faciles à interpréter et peuvent éliminer des configurations défaillantes avant une résolution LP. **Pourquoi pas forcément ?** Leur énumération exhaustive est chère ; beaucoup de coupes peuvent ne rien apporter, et le MILP lui-même est optimisé par HiGHS.

## 6. Exemple à faire au tableau

Topologie : A→B→D et A→C→D ; demande A→D = 30 Mbit/s ; panne possible de B et de C ; `alpha=1` ; `sigma=.5`.

1. Avant panne : au maximum `sigma*d=15` Mbit/s sur un arc du chemin. Il faut répartir la demande sur les deux chemins (15 + 15).
2. Après panne de B : seul A→C→D subsiste, donc chacun des arcs A→C et C→D doit disposer d'au moins 30 Mbit/s.
3. Après panne de C : même raisonnement pour A→B et B→D.
4. Quatre liens équipés de l'option (14 MHz, efficacité 3.6) fournissent chacun `14*3.6=50.4` Mbit/s. Le coût synthétique est `4*14=56`.
5. Avec probabilité .999 par lien et indépendance, la fiabilité conjointe = `.999**4` ≈ .9960, supérieure à .95.

Ne pas confondre `50.4 Mbit/s de capacité installée` et `15 Mbit/s de flux utilisé avant panne`.

## 7. Questions d'un jury — réponses courtes

1. **Pourquoi MILP ?** Variables binaires de configuration plus flux continus avec objectif/contraintes linéaires.
2. **Pourquoi un graphe orienté ?** Les capacités et flux sont modélisés séparément par direction.
3. **Pourquoi la fonction log ?** Pour transformer le produit des probabilités indépendantes en somme linéaire sous choix binaire exclusif.
4. **Comment calculez-vous la capacité ?** MHz × bit/s/Hz = Mbit/s dans notre modèle simplifié.
5. **Que représente `epsilon` ?** Tolérance probabiliste aux contraintes de capacité, pas un taux de panne observé sur une année.
6. **Différence `alpha`/`sigma` ?** `alpha` contrôle le débit à garantir après panne ; `sigma` limite la fraction pouvant traverser un chemin/intermédiaire avant panne.
7. **Pourquoi Benders ?** Séparer décisions entières de conception et routage continu, obtenir des coupes depuis un oracle LP.
8. **Pourquoi des variables d'écart dans l'oracle ?** Convertir un problème de faisabilité en minimisation LP toujours soluble, pour calculer une violation et une coupe duale.
9. **Une coupe est-elle une solution ?** Non, c'est une condition nécessaire imposée au problème maître.
10. **Pourquoi les cutsets sont-elles valides ?** Le trafic qui quitte une région doit traverser sa frontière sortante ; conservation des flux.
11. **Les cutsets suffisent-elles à garantir la faisabilité ?** Non, surtout pour plusieurs demandes qui se concurrencent ; l'oracle LP reste indispensable.
12. **Vos résultats reproduisent-ils le papier ?** Non. Nous reproduisons des principes de modélisation et des mécanismes d'optimisation sur des données synthétiques.
13. **Benders est-il toujours plus rapide ?** Non, le nombre d'itérations et le coût de l'oracle peuvent dépasser la résolution monolithique.
14. **Pourquoi ne pas optimiser la puissance radio ?** Notre modèle fixe des options bande passante/efficacité ; puissance et interférence sont hors du périmètre.
15. **Quelles seraient les meilleures extensions ?** Probabilités calibrées par canal, corrélations météo, grosses topologies, coupes avancées et mesures répétées.
16. **Pourquoi des tests de comparaison ?** Ils détectent des divergences de formulation/implémentation entre méthodes censées résoudre le même problème.
17. **Quelle limite principale du séparateur v0.3 ?** Son enumeration `O(2^n)` de toutes les partitions des nœuds.
18. **Comment justifier l'optimalité annoncée ?** Maître optimal et conception faisable validée par l'oracle ; vérifier que HiGHS a réellement conclu à l'optimalité.

## 8. Questions de code à préparer oralement

- Que contiennent exactement `ykeys`, `xkeys`, `yindex` et `xindex` ?
- Pourquoi construire `Aeq` et `Aub` séparément ?
- Pourquoi le signe négatif des capacités dans une coupe `coeff@y <= rhs` ?
- Que signifie une valeur marginale duale dans `linprog` ?
- Pourquoi un tableau NumPy pour les matrices et un dictionnaire Python pour le référencement ?
- Que se passe-t-il si une demande a sa destination au nœud défaillant ?
- Comment détecter une incohérence entre résultats MILP et Benders ?

**Conseil scientifique :** distingue toujours « ce que le papier démontre », « ce que notre code implémente », et « ce que nos expériences ont réellement mesuré ».
