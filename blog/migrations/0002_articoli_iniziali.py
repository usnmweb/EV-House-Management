"""Otto articoli di partenza per il Giornale.

Sono contenuti, non struttura: stanno in una migration e non in una fixture
perche' cosi' arrivano da soli su ogni ambiente — compreso Render, dove il
deploy lancia le migration e nessuno lancia `loaddata`.

Due avvertenze per chi li legge dopo.

La prima: le copertine puntano a fotografie che sono gia' in `media/`, cioe'
scatti degli immobili in gestione. Sono immagini vere e dell'azienda, ma non
sono immagini *editoriali*: quando ci saranno foto fatte per gli articoli, si
sostituiscono dall'amministrazione senza toccare questo file.

La seconda: nessun articolo contiene numeri commerciali scritti a mano. Quelli
della stagione arrivano da `settings.py` attraverso `mostra_stagione`, gli
stessi della home. Dove un numero servirebbe ma non ce l'abbiamo — le rese di
un immobile, per dirne una — il testo dice come si ottiene invece di inventarlo.
"""

from django.db import migrations

FOTO = "properties/2026/08/"

ARTICOLI = [
    {
        "titolo": "La stagione 2026 in numeri",
        "slug": "stagione-2026-in-numeri",
        "categoria": "novita",
        "pubblicato_il": "2026-08-20",
        "in_evidenza": True,
        "mostra_stagione": True,
        "copertina": FOTO + "villa-ginepro-jacuzzi-e-vista-mare-1.jpg",
        "copertina_alt": "La spiaggia di La Caletta vista dall'alto, in una giornata di agosto",
        "tag": "stagione, occupazione, rendiconto",
        "sottotitolo": "Cosa dicono i dati della settimana di punta, e cosa non dicono.",
        "estratto": "L'occupazione della settimana centrale di agosto, le notti "
                    "vendute sul totale disponibile e il numero di immobili gestiti. "
                    "Con la premessa che un numero solo non racconta una stagione.",
        "citazione": "Una settimana piena ad agosto la fa chiunque. La differenza "
                     "fra una casa che rende e una che non rende si vede a giugno "
                     "e a settembre.",
        "corpo": """La settimana centrale di agosto è quella in cui la costa orientale lavora al massimo: chi ha una casa in Baronia o in Gallura, in quei sette giorni, la riempie quasi certamente. Per questo il dato di occupazione di quella settimana, preso da solo, dice poco sul valore di una gestione — e per questo lo pubblichiamo insieme al resto.

## Cosa c'è dietro la percentuale

L'occupazione è il rapporto fra le notti effettivamente vendute e quelle che erano disponibili alla vendita. Sono due numeri diversi da quelli che si sentono di solito: «sempre pieno» non è una misura, e «tutto prenotato» dipende da quante notti si erano messe a calendario.

Il denominatore conta quanto il numeratore. Una casa tenuta fuori mercato per due settimane a luglio ha un denominatore più basso, e un'occupazione più alta. Non è un imbroglio, ma va detto: la percentuale va sempre letta accanto al numero di notti.

## Quello che i numeri non dicono

Non dicono la tariffa media, che è l'altra metà del ricavo. Non dicono quante di quelle notti sono state vendute con settimane di anticipo e quante all'ultimo momento, che è la differenza fra una casa che si vende da sola e una che va spinta. Non dicono il costo della gestione.

Sono tutte cose che stanno nel rendiconto mensile che riceve ogni proprietario, e che nessuna pagina pubblica può riassumere onestamente in una cifra.

## Perché li pubblichiamo lo stesso

Perché la domanda che ci fanno i proprietari alla prima telefonata è quasi sempre la stessa: «quanti ne avete, e come vanno». Rispondere con un aggettivo non è rispondere.

I numeri qui sopra sono quelli dichiarati dalla gestione e aggiornati a mano, non una statistica calcolata da questo sito. Se ne vuoi una sul tuo immobile — con la tua zona, il tuo numero di posti letto e i tuoi mesi di disponibilità — quella la facciamo in sopralluogo, e non è un numero che si può scrivere su una pagina uguale per tutti.""",
    },
    {
        "titolo": "CIN, CIR e le altre sigle: cosa serve davvero per affittare",
        "slug": "cin-cir-adempimenti-affitti-brevi",
        "categoria": "proprietari",
        "pubblicato_il": "2026-07-28",
        "copertina": FOTO + "domo-antiga-new-apt-centro-storico-siniscola-1.jpg",
        "copertina_alt": "Il soggiorno di un appartamento nel centro storico di Siniscola",
        "tag": "adempimenti, CIN, normativa, locazioni brevi",
        "sottotitolo": "Una mappa delle sigle, per capire quali ti riguardano prima di ricevere il primo ospite.",
        "estratto": "Codice nazionale, codice regionale, comunicazione degli alloggiati, "
                    "tassa di soggiorno, requisiti di sicurezza. Cosa sono, a chi tocca, "
                    "e cosa cambia se manca.",
        "corpo": """Chi affitta per la prima volta scopre in fretta che il problema non è trovare gli ospiti: è capire quali adempimenti lo riguardano. Le sigle sono poche, ma si somigliano tutte.

## Il CIN

È il Codice Identificativo Nazionale, introdotto per dare un identificativo unico a ogni unità destinata alla locazione breve o turistica. Si richiede attraverso la banca dati nazionale del Ministero del Turismo, ed è legato all'immobile, non a chi lo gestisce.

Una volta ottenuto, va esposto: negli annunci — quindi in ogni portale su cui la casa è pubblicata — e all'esterno dell'immobile. Un annuncio senza CIN è un annuncio irregolare, e le piattaforme lo rimuovono.

## Il CIR

È il codice regionale, che in Sardegna esisteva già prima del CIN. Il nazionale non lo sostituisce: convivono, e in genere il CIN si richiede indicando il codice regionale già assegnato. Se hai affittato negli anni scorsi, il CIR ce l'hai già — spesso in un vecchio scambio di email con il comune.

## La comunicazione degli alloggiati

Ogni ospite che dorme in casa va comunicato alla Questura attraverso il portale Alloggiati Web, entro le ventiquattro ore dall'arrivo. Non è una formalità: è l'adempimento su cui si concentrano i controlli, perché è l'unico che lascia una traccia verificabile giorno per giorno.

Serve un'utenza, che si richiede una volta sola, e serve che qualcuno la usi a ogni arrivo. È la parte della gestione che i proprietari sottovalutano di più, ed è anche quella che pesa di più quando si è lontani.

## La tassa di soggiorno

Non c'è ovunque: la decide il comune. Dove c'è, si incassa dall'ospite, si versa al comune con la periodicità stabilita e si rendiconta. Cambia da comune a comune — importo, esenzioni, numero massimo di notti — quindi l'unica risposta seria è: guarda il regolamento del tuo.

## La sicurezza

La normativa nazionale sulle locazioni brevi chiede requisiti minimi: estintore, rilevatore di gas e di monossido di carbonio, impianti a norma con le relative certificazioni. Sono cose che si sistemano in un pomeriggio, ma vanno fatte prima del primo ospite, non dopo la prima verifica.

## Cosa facciamo noi e cosa resta a te

Il CIN e il CIR sono legati all'immobile e li richiede il proprietario: possiamo seguirlo passo passo, ma la domanda la fa chi ha il titolo sulla casa. Tutto il resto — comunicazione degli alloggiati a ogni arrivo, tassa di soggiorno, rendicontazione — lo gestiamo noi.

Questa pagina è una mappa, non una consulenza: le norme cambiano e i regolamenti comunali sono diversi l'uno dall'altro. Per la tua situazione, sentiamoci.""",
    },
    {
        "titolo": "La Caletta, spiegata a chi ci arriva per la prima volta",
        "slug": "la-caletta-guida",
        "categoria": "localita",
        "pubblicato_il": "2026-07-10",
        "copertina": FOTO + "5-min-dal-mare-app-nuovo-con-veranda-1.jpg",
        "copertina_alt": "La Caletta vista dall'alto: il paese basso, la spiaggia e il mare aperto",
        "tag": "La Caletta, Siniscola, spiagge, Baronia",
        "sottotitolo": "Dieci chilometri di sabbia, un porto e una pineta. Come funziona il paese, e quando conviene esserci.",
        "estratto": "È la frazione di mare di Siniscola: sabbia chiara, fondale basso "
                    "e un lungomare che si percorre a piedi. Cosa c'è, dove si parcheggia, "
                    "e cosa cambia fra giugno e agosto.",
        "corpo": """La Caletta è la frazione costiera di Siniscola, sulla costa orientale della Sardegna. Chi ci arriva la prima volta di solito la attraversa senza accorgersene: il paese è basso, lungo e parallelo al mare, e la parte che conta si percorre tutta a piedi.

## La spiaggia

È una striscia di sabbia chiara che parte dal porto e continua verso nord per chilometri, con la pineta alle spalle per buona parte del percorso. Il fondale resta basso a lungo, ed è la ragione per cui è la spiaggia che consigliamo alle famiglie con bambini piccoli.

Più ci si allontana dal porto, più si dirada. In agosto la differenza fra il primo tratto e il quarto chilometro è di un ombrellone ogni due metri contro un ombrellone ogni venti.

## Il porto e il lungomare

Il porto turistico segna l'estremità sud. Attorno si concentrano i ristoranti, il passeggio della sera e i pochi negozi aperti fino a tardi. È l'unico punto del paese dove serve mettere in conto di cercare parcheggio in agosto.

Il lungomare che parte da lì è pianeggiante e continuo: in bicicletta si fa tutto, ed è il modo più sensato di muoversi se si alloggia in centro.

## Dove si dorme

Le case si dividono in tre fasce. Quelle dietro al porto, a piedi da tutto, che pagano la comodità con un po' di rumore serale. Quelle lungo la pineta, a cinque minuti a piedi dalla sabbia e molto più silenziose. E quelle nella parte residenziale verso l'interno, dove serve l'auto per la spiaggia ma il parcheggio è sotto casa.

Non c'è una fascia migliore: dipende da quanto si conta di stare in casa.

## Quando venire

Giugno e settembre sono i mesi in cui il rapporto fra clima e affollamento è migliore: l'acqua è già — o ancora — buona, e la spiaggia è vuota. Luglio è pieno ma gestibile. Agosto, e in particolare la settimana centrale, è la settimana in cui l'intera costa lavora al massimo: bellissima se si cerca movimento, faticosa se si cerca il contrario.

## Cosa c'è intorno

Mezz'ora verso nord porta a Budoni e Porto Ottiolu; mezz'ora verso sud a Posada, con il castello che si vede da tutta la piana. Verso l'interno, in poco più di un'ora, si è a Orgosolo e nel Supramonte, che è un'altra Sardegna e vale una giornata.""",
    },
    {
        "titolo": "Quanto rende una casa in Baronia",
        "slug": "quanto-rende-casa-baronia",
        "categoria": "proprietari",
        "pubblicato_il": "2026-06-22",
        "copertina": FOTO + "sozzastru-villa-a-300-metri-dal-mare-1.jpg",
        "copertina_alt": "L'esterno di una villa a trecento metri dal mare, in Baronia",
        "tag": "rendita, revenue, Baronia, valutazione",
        "sottotitolo": "Le cinque variabili che decidono il ricavo, e perché non esiste una risposta valida per tutti.",
        "estratto": "La domanda arriva alla prima telefonata. La risposta onesta non è "
                    "una percentuale: sono cinque variabili, e come si combinano sulla "
                    "tua casa in particolare.",
        "citazione": "Chi ti dà una percentuale al telefono, senza aver visto la casa, "
                     "ti sta dando un numero che ha inventato.",
        "citazione_fonte": "La regola che seguiamo in sopralluogo",
        "corpo": """«Quanto rende?» è la prima domanda di ogni proprietario, ed è quella a cui è più facile rispondere male. Una percentuale detta al telefono è un numero inventato: non abbiamo visto la casa, non sappiamo quante notti la vuoi tenere per te, e non sappiamo cosa c'è nel raggio di cinque minuti a piedi.

Quello che si può dire in generale è da cosa dipende. Sono cinque cose.

## 1. La distanza dal mare, misurata a piedi

Non in chilometri: in minuti di cammino. Sotto i dieci minuti a piedi il mercato cambia categoria, perché si rivolge anche a chi arriva senza auto o vuole lasciarla parcheggiata. Fra i dieci e i venti si compete con molte più case. Oltre, la casa si vende su altro — lo spazio, il verde, il silenzio — e va raccontata diversamente.

## 2. I posti letto veri

Veri, cioè letti in cui un adulto dorme volentieri per una settimana. Un divano letto in soggiorno aggiunge due posti sull'annuncio e toglie una stella nelle recensioni. In Baronia il salto di prezzo più netto è fra quattro e sei posti: è il passaggio dalla coppia con bambino alla famiglia allargata, e sono due mercati con budget diversi.

## 3. Lo spazio esterno

Veranda, terrazza, giardino, in quest'ordine di resa per metro quadro. Una veranda ombreggiata e arredata vale, in tariffa, più di una stanza in più: è il posto dove si passano le ore centrali della giornata quando dalla spiaggia si torna.

## 4. La finestra di disponibilità

Una casa disponibile solo a luglio e agosto lavora due mesi. La stessa casa disponibile da maggio a ottobre ne lavora sei, con tariffe più basse nei mesi laterali ma con costi fissi spalmati su molte più notti. È la variabile che il proprietario controlla di più, ed è quella che sposta di più il totale a fine anno.

## 5. Come è presentata

Le fotografie e il testo dell'annuncio non cambiano la casa, cambiano quanti la aprono. A parità di immobile, un servizio fotografico fatto bene sposta il numero di visualizzazioni in modo che si misura. È anche la variabile più economica da sistemare.

## Come si arriva a un numero

Si guarda la casa, si contano i posti letto veri, si stabilisce la finestra di disponibilità e si confronta con l'andamento reale di immobili simili nella stessa zona. Da lì esce una stima con un intervallo, non una cifra secca, e con le ipotesi scritte accanto.

Il sopralluogo e la stima non costano nulla e non impegnano a niente. Se il numero non ti convince, è un'informazione utile lo stesso.""",
    },
    {
        "titolo": "Cosa mettere in valigia per la costa orientale",
        "slug": "valigia-costa-orientale",
        "categoria": "ospiti",
        "pubblicato_il": "2026-06-05",
        "copertina": FOTO + "cala-luna-family-house-verande-4min-dal-mare-1.jpg",
        "copertina_alt": "Una camera con asciugamani piegati sul letto, pronta per gli ospiti",
        "tag": "valigia, consigli, spiagge, famiglie",
        "sottotitolo": "Quello che serve davvero, e le tre cose che quasi tutti dimenticano.",
        "estratto": "Non è una lista lunga. Ma tre o quattro cose fanno la differenza "
                    "fra una settimana comoda e mezza giornata persa a cercare un negozio "
                    "aperto a ferragosto.",
        "corpo": """Nelle case che gestiamo trovi già biancheria da letto, asciugamani, phon, e in cucina tutto quello che serve per cucinare davvero. Quindi questa non è la lista di cosa manca: è la lista delle cose che qui servono più che altrove, e che è scomodo comprare sul posto.

## Le scarpe da scoglio

La prima. Molte delle cale più belle della costa orientale non hanno sabbia: hanno ciottoli, o roccia che entra in acqua. Con le scarpe da scoglio ci si sta un giorno intero, senza si sta venti minuti. Costano poco e occupano niente.

## Una borsa termica piccola

La seconda. Le spiagge lunghe qui sono lunghe davvero: dal posto dove si parcheggia al posto dove ci si sistema possono esserci dieci minuti di cammino, e i chioschi non ci sono ovunque. Acqua fresca a metà pomeriggio cambia la giornata, soprattutto con i bambini.

## Una felpa

La terza, ed è quella che sorprende. Da fine agosto la sera in riva al mare rinfresca, e il vento di maestrale può abbassare la temperatura percepita di parecchi gradi anche in pieno luglio. Una felpa a testa, sempre.

## Il resto, in breve

Crema solare alta: il sole qui è più forte di quanto sembri con il vento addosso. Un cappello. Un adattatore non serve, le prese sono quelle italiane. Un telo mare leggero in più oltre agli asciugamani di casa, perché quelli non vanno in spiaggia.

Se viaggi con bambini piccoli, dicci prima di arrivare quanti anni hanno: culla e seggiolone li abbiamo in diverse case, e si preparano prima del tuo arrivo invece di cercarli il giorno stesso.

## Cosa lasciare a casa

Il phon, che c'è. Il bagnoschiuma in formato grande, che si trova ovunque. E il piano preciso di tutte le giornate: qui il tempo e il vento decidono in quale spiaggia si sta bene oggi, e la cosa più utile che puoi portare è la disponibilità a cambiare idea la mattina.""",
    },
    {
        "titolo": "Golfo Aranci fuori dalle ore di punta",
        "slug": "golfo-aranci-fuori-orario",
        "categoria": "localita",
        "pubblicato_il": "2026-05-18",
        "copertina": FOTO + "baia-caddinas-1.jpg",
        "copertina_alt": "La costa di Golfo Aranci vista dagli immobili di Baia Caddinas",
        "tag": "Golfo Aranci, Gallura, spiagge, traghetti",
        "sottotitolo": "Un porto, cinque spiagge numerate e i delfini. Come evitare le due ore in cui il paese si riempie.",
        "estratto": "Golfo Aranci è il paese dei traghetti, e questo ne detta il ritmo. "
                    "Sapere a che ora arrivano cambia completamente come si vive la giornata.",
        "corpo": """Golfo Aranci sta sulla punta nord-orientale del golfo di Olbia, ed è prima di tutto un porto: da qui partono e arrivano i traghetti per la penisola. Questo dettaglio, che sembra logistico, è la cosa che più condiziona come si vive il paese.

## Il ritmo del porto

Nelle ore attorno agli arrivi e alle partenze il traffico sull'unica strada principale si concentra tutto insieme, e il paese sembra molto più affollato di quanto sia. Un'ora dopo torna tranquillo.

Non serve consultare gli orari: basta sapere che esistono. Se vai a fare la spesa o a cena e trovi coda, quasi sempre stai capitando in una di quelle finestre, e mezz'ora dopo non c'è più.

## Le spiagge numerate

Le spiagge principali sul lato est sono indicate con i numeri, dalla prima alla quinta, lungo la strada che costeggia il promontorio. Sono piccole, sabbiose e riparate, e più si sale di numero più si cammina per arrivarci — con il risultato prevedibile che la prima è piena e la quinta è comoda.

Sul lato opposto, verso Marinella, la costa cambia: cale più larghe, ventose quando soffia il maestrale, ottime nelle giornate calme.

## Cala Moresca e Capo Figari

Cala Moresca è alla base del promontorio di Capo Figari e vale la mattinata. Da lì parte il sentiero che sale al capo: non è impegnativo, ma va fatto presto, perché ombra non ce n'è. Dall'alto si vede Tavolara di fronte, che è il motivo per cui ci si va.

## I delfini

Nel golfo c'è una popolazione stabile di tursiopi, e le uscite in barca per avvistarli partono dal porto. È una delle poche attività organizzate della zona che vale davvero per i bambini.

## Quando conviene esserci

Maggio e ottobre sono i mesi migliori per camminare: Capo Figari a luglio a mezzogiorno è una cattiva idea. Giugno e settembre per il mare senza folla. Agosto è pieno, ma il paese resta più vivibile della Costa Smeralda a venti minuti di distanza — che è poi la ragione per cui molte famiglie scelgono di dormire qui e spostarsi.""",
    },
    {
        "titolo": "Il check-in che non fa perdere il primo pomeriggio",
        "slug": "check-in-senza-attese",
        "categoria": "ospiti",
        "pubblicato_il": "2026-05-02",
        "copertina": FOTO + "new-apt-la-caletta-comfort-e-veranda-vista-mare-1.jpg",
        "copertina_alt": "Un tavolo apparecchiato sulla veranda di una casa appena consegnata agli ospiti",
        "tag": "check-in, arrivo, documenti, ospiti",
        "sottotitolo": "Come funziona l'arrivo, cosa serve avere sottomano e cosa fare se il traghetto ritarda.",
        "estratto": "Il primo pomeriggio di una vacanza è il più facile da sprecare. "
                    "Ecco come funziona l'arrivo nelle nostre case, e le due cose da "
                    "fare prima di partire.",
        "corpo": """La prima giornata è quella che si ricorda peggio: si arriva stanchi, spesso nell'ora più calda, e qualsiasi attesa pesa il doppio. L'arrivo è la parte della gestione su cui lavoriamo di più, e funziona così.

## Prima di partire: due cose

La prima è mandarci i documenti di tutti gli ospiti. Non è una richiesta nostra: la comunicazione alla Questura è obbligatoria entro ventiquattro ore dall'arrivo, e se i dati arrivano prima, all'arrivo non c'è nulla da compilare. Bastano le foto dei documenti.

La seconda è dirci a che ora pensi di arrivare, anche approssimativamente. Non serve la precisione al minuto: serve sapere se sei atteso alle sedici o alle ventitré, perché sono due arrivi diversi da organizzare.

## L'orario

Il check-in è dalle 15:00. È l'orario in cui la casa è pronta: prima ci sono le pulizie, e non è un margine che si può comprimere senza che si veda.

Se arrivi prima, quasi sempre possiamo tenerti i bagagli, così vai al mare invece di aspettare in auto. Chiedilo il giorno prima e non il giorno stesso.

## L'arrivo tardi

Gli arrivi in tarda serata sono normali qui: i traghetti sbarcano quando sbarcano. Avvisaci e l'arrivo si organizza, senza costi aggiuntivi e senza che nessuno ti aspetti al buio in un parcheggio.

Se il traghetto o il volo ritarda mentre sei in viaggio, scrivici: è più utile un messaggio dal porto che una spiegazione all'arrivo.

## Cosa trovi in casa

Biancheria da letto e asciugamani già pronti. Un kit di prima necessità in bagno e in cucina, per non dover cercare un supermercato aperto la prima sera. E un foglio con i numeri utili, la rete wifi e le indicazioni pratiche — dove si parcheggia, come funziona il condizionatore, dove si buttano i rifiuti e in che giorni.

## Se qualcosa non va

C'è un numero, risponde una persona, e nella stagione risponde anche di domenica. La maggior parte delle cose che si rompono in una casa al mare si risolvono in mezza giornata se qualcuno lo sa; diventano una vacanza rovinata se nessuno lo sa fino al check-out.""",
    },
    {
        "titolo": "Casa Rudalza entra in gestione",
        "slug": "casa-rudalza-entra-in-gestione",
        "categoria": "novita",
        "pubblicato_il": "2026-04-14",
        "copertina": FOTO + "casa-rudalza-1.jpg",
        "copertina_alt": "Il soggiorno di Casa Rudalza, a Golfo Aranci",
        "tag": "nuovo immobile, Golfo Aranci, Rudalza",
        "sottotitolo": "Quattro posti letto a Rudalza, fra Golfo Aranci e Porto Rotondo.",
        "estratto": "Un nuovo immobile in gestione sul golfo: com'è fatto, cosa abbiamo "
                    "sistemato prima di pubblicarlo e perché abbiamo aspettato ad aprirlo.",
        "corpo": """Casa Rudalza è entrata in gestione questa primavera. Sta nella zona di Rudalza, sul tratto di costa fra Golfo Aranci e Porto Rotondo: una delle porzioni di golfo più riparate, con il mare a pochi minuti e senza il traffico della strada principale.

## Com'è

Quattro posti letto, due camere, un bagno. Spazio esterno vivibile, che da queste parti conta quanto una stanza in più, e parcheggio dentro la proprietà — dettaglio che in agosto vale più di quanto sembri a gennaio.

## Cosa abbiamo fatto prima di pubblicarla

Un servizio fotografico, che è la cosa che cambia di più il numero di persone che aprono l'annuncio. La verifica degli impianti e delle dotazioni di sicurezza. La sistemazione della dotazione di cucina, che è la voce su cui le recensioni sono più severe e su cui si spende meno.

E il tempo di aspettare che tutto fosse pronto prima di aprire il calendario. È una scelta che costa qualche settimana di disponibilità, ma le prime recensioni di una casa nuova pesano su tutta la stagione successiva: aprire con la casa a metà è un risparmio che si paga per un anno.

## Perché ne parliamo

Perché la domanda che ci fa un proprietario indeciso è quasi sempre «quanto ci vuole». La risposta, per una casa già in ordine come questa, è qualche settimana fra il sopralluogo e il primo ospite. Per una casa da sistemare dipende da cosa c'è da sistemare, e lo si capisce in sopralluogo.

Se hai una casa fra Baronia e Gallura e ti stai facendo la stessa domanda, il modo più veloce per avere una risposta è farcela vedere.""",
    },
]


def crea(apps, schema_editor):
    Article = apps.get_model("blog", "Article")
    for dati in ARTICOLI:
        dati = dict(dati)
        dati["pubblicato"] = True
        # `save()` del modello vero qui non gira — nelle migration i modelli
        # sono storici — quindi slug e minuti si scrivono a mano.
        parole = len(dati["corpo"].split())
        dati.setdefault("tempo_lettura", max(1, round(parole / 200)))
        Article.objects.update_or_create(slug=dati["slug"], defaults=dati)


def elimina(apps, schema_editor):
    Article = apps.get_model("blog", "Article")
    Article.objects.filter(slug__in=[a["slug"] for a in ARTICOLI]).delete()


class Migration(migrations.Migration):

    dependencies = [("blog", "0001_initial")]

    operations = [migrations.RunPython(crea, elimina)]
