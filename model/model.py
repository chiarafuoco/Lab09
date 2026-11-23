from copy import deepcopy

from database import punto_interesse_DAO
from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO

import copy

from model.escursione import Escursione


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        self.max_giorni = 0 #inizializzo il max giorni dato in input, ovvero il numero di giorni indicati per l'esperienza
        self.max_budget = 0 #inizializzo il max budget dato in input, ovvero il budget totale indicato per l'intera esperienza
        self.lista_escursioni_parco = []

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        lista_relazioni =  EscursioneDAO.get_escursioni_punti_interesse() #richiamo la lista di dizionari creata nel dao,
        #la quale restituisce tutte le relazioni

        for i in range(len(lista_relazioni)):
            # ogni escursione è un oggetto che appartiene al dizionario escursioni_map, la cui chiave è l'id dell'escursione.
            # ciclando su ogni relazione che collega escursione a punto di interesse, aggiungo l'oggetto del punto di interesse
            # al set che è presente come attributo dell'oggetto escursione. La generica escursione su cui itero è
            # self.escursioni_map[lista_relazioni[i]["id_escursione"]]
            self.escursioni_map[lista_relazioni[i]["id_escursione"]].punti_interesse.add(self.punti_interesse_map[lista_relazioni[i]["id_punto_interesse"]])

            # ogni punto di interesse è un oggetto che appartiene al dizionario punti_interesse_map, la cui chiave è l'id del punto di interesse.
            # ciclando su ogni relazione che collega escursione a punto di interesse, aggiungo l'oggetto dell'escursione
            # al set che è presente come attributo dell'oggetto punto_interesse. Il generico punto_interesse su cui itero è
            # self.punti_interesse_map[lista_relazioni[i]["id_punto_interesse"]]
            self.punti_interesse_map[lista_relazioni[i]["id_punto_interesse"]].escursioni.add(self.escursioni_map[lista_relazioni[i]["id_escursione"]])





    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        self.max_giorni = max_giorni # salva come attributi dell'oggetto il numero massimo di giorni e il budget massimo
        # disponibili per l'itinerario, in modo che siano accessibili anche dentro la ricorsione
        self.max_budget = max_budget

        lista_escursioni_parco = [] # creo una lista vuota in cui inserirò solo le escursioni che appartengono a quel determinato parco (quello selezionato dal textfield presente nell'interfaccia)
        for escursione in self.escursioni_map: #ciclo sulle chiavi del dizionario (id escursioni)
            if self.escursioni_map[escursione].id_parco == id_parco: # controllo se l'oggetto escursione associato a quella chiave appartiene al parco selezionato (id_parco)
                lista_escursioni_parco.append(self.escursioni_map[escursione]) # se il risultato risulta True, dunque che appartiene al parco
                #aggiunge l'oggetto alla lista filtrata

        self.lista_escursioni_parco = lista_escursioni_parco # salvo la lista appena filtrata come attributo, rendendola disponibile per la ricorsione, dunque più accessibile




        self._ricorsione(0,[],0,0,0,set()) #richiamo la ricorsione passando i valori inziali
        #il primo 0 indica l'indice di partenza, [] lista vuota che conterrà la sequenza di escursioni scelte fino a quel momento, 3 contatori iniziali azzerati)


        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float,
                    valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""
        # se non è ancora stata trovata alcuna soluzione (valore_ottimo == -1) o il punteggio del pacchetto attuale supera
        # il miglior punteggio trovato finora
        if self._valore_ottimo == -1 or self._valore_ottimo < valore_corrente:
            self._pacchetto_ottimo = pacchetto_parziale.copy()  # faccio una copia per evitare che quando uso .pop() venga modificata
            self._costo = costo_corrente #aggiorno il costo
            self._valore_ottimo = valore_corrente #aggiorno il valore

        if start_index >= len(self.lista_escursioni_parco): #condizione di terminazione,se l'indice di partenza ha raggiunto o
            # superato la lunghezza della lista, non ci sono più escursioni da esplorare in questo percorso, si interrompe la ricorsione
            return

        for escursione in self.lista_escursioni_parco[start_index:len(self.lista_escursioni_parco)]: #ciclo sulle escursioni disponibili partendo da start_index fino alla fine della lista
            if escursione.punti_interesse.intersection(punti_usati) == set(): #controllo se l'interserzione tra i punti di interesse dell'escursione in questione e quelli
                # già visitati (punti usati) sia vuota, nel caso non ci sono sovrapposizioni

                nuovi_punti_usati = punti_usati.union(escursione.punti_interesse) #creo un nuovo set unendo i punti già usati con quelli
                # della nuova escursione
                nuova_durata = durata_corrente + escursione.durata_giorni #sommo i giorni
                nuovo_costo = costo_corrente + escursione.costo #sommo i costi

                if ((self.max_giorni is None or nuova_durata <= self.max_giorni) #verifico che i giorni non superino max_giorni (se dichiarato)
                        and (self.max_budget is None or nuovo_costo <= self.max_budget)): #verifico che il costo non superi il max_budget (se dichiarato)
                    valore_escursione = 0
                    for punto_interesse in escursione.punti_interesse:
                        valore_escursione = valore_escursione+ punto_interesse.voto_visitatori #sommo i voti dei visitatori di tutti i punti di interesse toccati dall'escursione totale

                    nuovo_valore = valore_corrente + valore_escursione #aggiorno il valore totale del pacchetto
                    pacchetto_parziale.append(escursione) #aggiungo l'escursione al pacchetto parziale

                    self._ricorsione(start_index + 1, pacchetto_parziale, nuova_durata, nuovo_costo, nuovo_valore, nuovi_punti_usati)
                    pacchetto_parziale.pop()  # elimino l'ultimo elemento per poter proseguire e provare con un'escursione diversa





