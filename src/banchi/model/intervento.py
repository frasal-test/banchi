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
    oratore: str = ""        # come compare in Aula (es. "PRESIDENTE" se presiede)
    ruolo: str = ""
    presidenza: bool = False
    testo: str = ""
    trovato: bool = False    # False se l'ancora LOD non ha un turno corrispondente nel resoconto
