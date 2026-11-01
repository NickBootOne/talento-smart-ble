# Talento smart BLE — onderzoeksversie 2026.11.3

[![Controles](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/check.yml/badge.svg?branch=main&event=push)](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/check.yml)
[![Release](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/release.yml/badge.svg)](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/release.yml)

Home Assistant-custom integration voor een Grässlin talento smart C15, met experimentele FIX AAN/UIT-bediening en AUTO herstellen, vooraf lezen en verplicht teruglezen na een write. Versie 2026.11.3 voegt automatisch statuslezen toe, circa elke 30 seconden. Geen override-bediening of PIN-handshake. De gebruiker heeft AUTO/UIT (`00`) fysiek bevestigd en meldt werkende schakeling via een ESP32-proxy. De laatste diagnostiek bevestigt de opdracht AUTO; langdurige bereikbaarheid en automatische polling moeten nog worden getest.

## Statusverversing vanaf 2026.11.3

De vorige versie las uitsluitend op verzoek en liet de meting na twee minuten verlopen. Nu plant Home Assistant circa elke 30 seconden een statusread zolang de entiteiten geladen zijn en polling niet is uitgeschakeld bij de systeemopties van de integratie. Na opstarten kan de eerste automatische meting dus ongeveer 30 seconden duren; de leesknop blijft bruikbaar voor direct verversen.

Tijdens normaal uitlezen blijft de vorige verse waarde zichtbaar. Er wordt pas een nieuwe waarde getoond zodra de read slaagt. Tijdens schakelen wordt de oude waarde wel ongeldig gemaakt, totdat teruglezen de opdracht bevestigt. Bij een mislukte read wordt de status unavailable: een oude meting wordt niet als actuele relaisstand voorgesteld. Als een meting zonder nieuwe resultaten ouder dan twee minuten wordt, verloopt deze eveneens. De leeftijd wordt met een monotone klok gemeten zodat een systeemklokcorrectie niet tot vroegtijdig verlopen leidt.

Test na de update minimaal vijf minuten. De meettijd hoort periodiek vooruit te lopen. Een automatische tijdschakeling of fysieke bediening moet bij de volgende geslaagde read zichtbaar worden. Bij opnieuw wegvallende status: download de diagnostiek terwijl het probleem optreedt. `freshness_reason` onderscheidt `never_read`, `fresh`, `expired` en `last_read_failed`; `failure` geeft de foutstap en `measurement_age_seconds` de meetleeftijd.

Automatisch lezen garandeert niet dat een gesloten Bluetooth-venster op de C15 opnieuw geopend kan worden. Test ook na het verstrijken van dat venster en zo nodig met opnieuw activeren op het apparaat. Er worden bij polling uitsluitend kanaalselectie en statusreads uitgevoerd, geen relaiscommando's.

## Schakelbediening testen

1. Update via HACS naar **2026.11.3** en herstart Home Assistant volledig. Laat de proxy op de werkende plaats staan.
2. Activeer Bluetooth op de C15, sluit de officiële app en druk op **Kanaal 1 status lezen (test)**. Zonder een verse, herkenbare meting is de nieuwe schakelaar unavailable.
3. Gebruik **Relais (FIX-bediening, test)**: AAN verstuurt FIX AAN; UIT verstuurt FIX UIT. De weergegeven stand komt uitsluitend uit de teruggelezen relaisstatus. In AUTO toont de schakelaar dus ook de actuele relaisstand; bedienen zet de modus expliciet op FIX.
4. Controleer na AAN de fysieke relaisindicatie en modus: verwacht FIX_ON en ruwe status `02`. Controleer na UIT: FIX_OFF en `03`. Wacht telkens tot de opdracht klaar is.
5. Druk na de test op **AUTO herstellen (test)** om het tijdprogramma weer te laten bepalen wanneer het relais schakelt. AUTO is geen UIT-opdracht; de teruggelezen stand kan aan of uit zijn. De integratie verstuurt geen programmawijzigingen, maar het fysieke gedrag moet nog worden gecontroleerd.
6. Download na de test de diagnostiek. Vermeld welke acties fysiek werkten. `status_test.last_command` toont confirmed, not_sent of unconfirmed en `status_test.failure` vermeldt stap, foutklasse en of het commando mogelijk al is uitgevoerd.

**FIX blijft actief totdat je AUTO herstelt.** Bij een fout na de write kan het relais al geschakeld zijn, ook als HA unavailable toont. Er wordt niet automatisch opnieuw geschreven. Lees opnieuw of controleer de C15 en herstel zo nodig AUTO via het apparaat of de officiële app. Een terugleesfout geeft geen automatische tegengestelde opdracht.

Het volledige selecteer-/lees-/schrijf-/terugleespad wordt onder dezelfde vergrendeling uitgevoerd als GATT-inspectie en handmatig/automatisch lezen. Toegestane relaiswrite-payloads zijn uitsluitend AUTO `00`, FIX AAN `01`, FIX UIT `02`. De retourcodering verschilt: `01` als antwoord betekent AUTO/AAN, niet FIX AAN. Onbekende beginstatus blokkeert een relaiswrite. De verse meetwaarde wordt automatisch vernieuwd zolang de C15 bereikbaar is.

Override blijft buiten deze release: de APK bevat een OVR-moduscommando, maar de precieze toggle-/richtingsemantiek is nog onvoldoende op hardware vastgesteld.

## Status testen na de update

1. Installeer de actuele versie via de HACS-update en herstart Home Assistant volledig. Je bestaande configuratie blijft behouden.
2. Laat de ESP32 staan waar GATT-inspectie werkte, sluit de officiële telefoonapp en activeer Bluetooth op de C15.
3. Druk op **Kanaal 1 status lezen (test)** voor direct uitlezen; automatisch lezen gebeurt circa elke 30 seconden.
4. Noteer **Ruwe kanaalstatus (test)**, **Modus laatste testmeting** en **Relais laatste testmeting**. Vergelijk het relais met het scherm van de C15 en controleer dat de meettijd blijft vooruitlopen.
5. Laat de C15 via zijn eigen bediening of tijdprogramma in de andere relaisstand komen en druk opnieuw op de leesknop. De leesknop zelf schakelt het relais niet.
6. Download daarna de diagnostiek en deel de waarden, tijdstippen en de werkelijk waargenomen relaisstand. `status_test.failure` meldt bij fouten in welke stap de test stopte. De ESP32/proxy wordt nog niet afzonderlijk geïdentificeerd in diagnostiek.

Een geslaagde GATT-scan bewijst geen toegestane characteristic-toegang. Een apparaat met PIN-beveiliging kan deze test weigeren; er worden geen PIN's geraden of willekeurige initialisatiewrites gedaan. Een fout kan ook door bereik of een bezette verbinding komen. Bij onbekende statusbytes toont alleen de ruwe sensor een meetwaarde; relais en modus blijven unavailable. Een ongeldige lengte levert een fout op met maximaal 16 ruwe bytes in de diagnostiek.

Voor de eerste hardwaretest worden alleen de ondubbelzinnige APK-retourwaarden `00`–`05` vertaald. Waarden met extra bits worden bewaard maar nog niet geïnterpreteerd. Zie [protocolbewijs](docs/status-protocol.md). Gebruik deze testmetingen nog niet voor automatiseringen.

## Nu handmatig installeren

1. Pak de ZIP uit op je computer.
2. Kopieer `custom_components/talento_smart_ble` naar `/config/custom_components/talento_smart_ble` in Home Assistant. Voorkom een extra mapniveau.
3. Herstart Home Assistant volledig.
4. Ga naar Instellingen → Apparaten & diensten → Integratie toevoegen → Talento smart BLE (onderzoek).
5. Vul het Bluetooth-MAC-adres van de C15 in. Dit vind je bijvoorbeeld met nRF Connect of de Bluetooth-advertenties in Home Assistant. Het is niet het MAC-adres van de ESP32.

Installatie controleert uitsluitend het adresformaat en kan dus ook offline worden voltooid. Home Assistant installeert de dependency bleak-retry-connector; internettoegang is daarvoor vereist. De opgegeven minimale HA-versie is een ontwikkeldoel, geen geteste compatibiliteitsgarantie.

## Via HACS installeren na publicatie

Projectrepository: https://github.com/NickBootOne/talento-smart-ble . Voeg deze URL in HACS toe via het menu → Aangepaste repositories → type Integratie. Download de integratie, herstart Home Assistant en voeg haar toe via Apparaten & diensten.

HACS controleert periodiek op nieuwe versies; een GitHub-release verschijnt dus niet gegarandeerd onmiddellijk. Installeren gebeurt via de update-entiteit. Automatisch installeren vereist een eigen Home Assistant-automatisering met `update.install`; gewijzigde Python-code wordt na een herstart actief. Deze repository wijzigt geen Home Assistant-automatiseringen en voert geen herstarts uit. De update-entiteit-ID moet na installatie in je eigen Home Assistant worden vastgesteld.

Versienummers volgen `JAAR.MAAND.VOLGNUMMER`: `2026.10.1` is de eerste release van oktober 2026, `2026.10.2` de tweede. Het laatste getal is geen dagnummer. Bij een nieuwe maand begint de teller opnieuw op 1, bijvoorbeeld `2026.11.1`. Git-tags krijgen het voorvoegsel `v`.

Voor volgende releases: pas `version` in het manifest en de diagnostiek aan, werk de code en README bij en push een overeenkomstige tag, bijvoorbeeld `v2026.10.2`. De Release-workflow voert transporttests uit, controleert de versie en publiceert een GitHub-release. Publiceer alleen versies die klaar zijn voor de gebruikers van dit onderzoeksproject. De controles bewijzen geen werking op hardware.

Onderstaande stappen gelden wanneer je een eigen kopie van de repository wilt publiceren:

1. Maak een eigen GitHub-repository aan.
2. Voer lokaal `python prepare_repository.py JOUW_GITHUB_NAAM/talento-smart-ble` uit. Dit vervangt de expliciete `REPLACE_OWNER`-plaatsaanduiding in het manifest en vult de beheerder in.
3. Zet de inhoud van deze map in de hoofdmap van die repository. `custom_components` en `hacs.json` horen direct in de hoofdmap. De meegeleverde `brand/icon.png` is het projecticoon.
4. Open HACS → menu → Aangepaste repositories. Voeg de repository-URL toe als type Integratie, download en herstart Home Assistant.
5. Voeg vervolgens de integratie toe via Apparaten & diensten.

Deze structuur volgt de HACS-documentatie: https://www.hacs.xyz/docs/publish/integration/ . De repository is gepubliceerd; HACS-validatie is nog niet uitgevoerd. De broncode is beschikbaar via GitHub-releases.

## Bluetooth Proxy en eerste test

Gebruik een reeds in Home Assistant opgenomen ESPHome Bluetooth Proxy met `bluetooth_proxy: active: true` (als YAML: `bluetooth_proxy:` met daaronder ingesprongen `active: true`). Plaats deze in de buurt van de C15. Een lokale Bluetooth-adapter werkt ook. Home Assistant selecteert de bereikbare connectable adapter; deze versie dwingt geen specifieke proxy af. Er is geen directe ESPHome-API-client of aparte BLE-scanner in deze integratie.

1. Sluit de officiële app en nRF Connect zodat zij geen verbinding vasthouden.
2. Activeer Bluetooth op de C15 volgens de handleiding.
3. Open het toegevoegde apparaat en druk op **GATT inspecteren**. GATT-inspectie zelf blijft handmatig; statuslezen maakt wel automatisch verbinding.
4. De sensor toont `expected_uuids_found` wanneer de twee verwachte characteristics onder de config-service gevonden zijn, of `expected_uuids_missing`. Dit zegt alleen iets over UUID-aanwezigheid, niet over authenticatie, relaisstatus of schrijfbaarheid.
5. De sensor toont `unavailable` na een mislukte inspectie. De knop blijft beschikbaar om opnieuw te proberen. Controleer de tijd `scanned_at`: een geslaagde inspectie blijft als historische uitslag staan en bewijst geen huidige verbinding.
6. Download bij de integratie de diagnostiek via het menu en stuur dat JSON-bestand terug. Het bevat service-UUID's en characteristic-properties, geen MAC-adres, PIN of characteristicwaarden. Bij fouten blijven eerdere succesvolle metadata behouden, expliciet als `last_successful_scan`.
7. Controleer dat er geen relaisactie plaatsvindt. Test ook met gesloten Bluetooth-venster en herhaal na opnieuw activeren. Een verbinding kan circa 55 seconden kosten inclusief opruimen.

Voor betrouwbaar schakelen zijn daarnaast Android HCI-captures nodig van verbinden/authenticatie, status lezen, FIX AAN/UIT, AUTO en override vanuit beide relaistoestanden, inclusief tijdstippen en fysieke relaisindicatie. Deze versie verzamelt die protocolpayloads niet.

## Implementatie en verificatie

De transportlaag gebruikt `bluetooth.async_ble_device_from_address(..., connectable=True)` en `bleak_retry_connector.establish_connection`. Daarmee volgt deze de HA-route voor lokale en proxy-adapters: https://developers.home-assistant.io/docs/bluetooth/ . De verbinding wordt na elke test gesloten. Alle transacties delen één verbindingsvergrendeling. Er worden geen pairing-, programma- of firmwareacties uitgevoerd. Relaiswrites zijn uitsluitend de drie hierboven beschreven FIX/AUTO-commando's.

Gecontroleerd met geïsoleerde tests: kanaalselectie, wachttijd/read-volgorde, foutafhandeling, opruimen en statusdecodering. De vorige GATT-inspectie werkte volgens de aangeleverde diagnostiek op HA 2026.10.4; de gebruiker bevestigde gebruik van een ESP32-proxy. De nieuwe statusleestest, PIN-authenticatie, continue bereikbaarheid en fysieke statusbetekenis zijn nog niet op hardware getest. Hassfest/HACS-validator en volledige HA-runtime-tests zijn nog niet uitgevoerd.

Transporttests: `python -m unittest discover -s tests -v`. Deze vereisen geen Home Assistant of Bluetooth-hardware.

Verwijderen: verwijder eerst de integratie via Apparaten & diensten, verwijder daarna via HACS of de map in custom_components en herstart Home Assistant.
