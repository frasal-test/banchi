"""Modello minimo: un intervento d'Aula agganciato a un atto.

Il resoconto stenografico si considera definitivo a prescindere da quando è
stato prelevato: nessuno degli endpoint ufficiali espone lo stato editoriale
(vedi docs/decisioni.md, 2026-09-03).
"""

from dataclasses import dataclass


@dataclass
class Intervento:
    ancora: str            # id univoco nel resoconto, es. sed0677.stenografico.tit00040.int00210
    id_seduta: str          # es. "0677"
    data: str               # AAAAMMGG
    deputato_uri: str | None
    deputato_nome: str | None
    gruppo_sigla: str | None
    gruppo_uri: str | None = None
    oratore: str = ""        # come compare in Aula (es. "PRESIDENTE" se presiede)
    ruolo: str = ""
    presidenza: bool = False
    pubblicato_in_calce: bool = False  # testo depositato, autorizzato in calce: non pronunciato in Aula
    testo: str = ""
    trovato: bool = False    # False se l'ancora LOD non ha un turno corrispondente nel resoconto
    dedotto: bool = False    # True se il turno non ha un nodo LOD proprio: attribuito all'atto per inferenza (stesso blocco tit/sub di un turno confermato), non dichiarato da Camera
