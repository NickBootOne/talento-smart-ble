# Talento smart BLE — onderzoeksversie 0.1.0

Home Assistant-custom integration voor het verzamelen van GATT-metadata van een Grässlin talento smart C15. Dit is een ontwikkelbasis voor HACS, geen werkende relaisschakelaar. FIX, override, PIN-authenticatie en actuele relaisstatus zijn nog niet geïmplementeerd. Er worden geen characteristic-values gelezen of geschreven. De inspectie maakt wel een BLE-verbinding en vraagt GATT-metadata op.

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

Voor volgende releases: pas `version` in het manifest aan, werk de code bij en push een overeenkomstige tag, bijvoorbeeld `v0.1.1`. De Release-workflow voert transporttests uit, controleert de versie en publiceert een GitHub-release. Publiceer alleen versies die klaar zijn voor de gebruikers van dit onderzoeksproject. De controles bewijzen geen werking op hardware.

Onderstaande stappen gelden wanneer je een eigen kopie van de repository wilt publiceren:

1. Maak een eigen GitHub-repository aan.
2. Voer lokaal `python prepare_repository.py JOUW_GITHUB_NAAM/talento-smart-ble` uit. Dit vervangt de expliciete `REPLACE_OWNER`-plaatsaanduiding in het manifest en vult de beheerder in.
3. Zet de inhoud van deze map in de hoofdmap van die repository. `custom_components` en `hacs.json` horen direct in de hoofdmap. De meegeleverde `brand/icon.png` is het projecticoon.
4. Open HACS → menu → Aangepaste repositories. Voeg de repository-URL toe als type Integratie, download en herstart Home Assistant.
5. Voeg vervolgens de integratie toe via Apparaten & diensten.

Deze structuur volgt de HACS-documentatie: https://www.hacs.xyz/docs/publish/integration/ . Publicatie en HACS-validatie zijn niet uitgevoerd. De ZIP bevat de volledige broncode; een release is optioneel.

## Bluetooth Proxy en eerste test

Gebruik een reeds in Home Assistant opgenomen ESPHome Bluetooth Proxy met `bluetooth_proxy: active: true` (als YAML: `bluetooth_proxy:` met daaronder ingesprongen `active: true`). Plaats deze in de buurt van de C15. Een lokale Bluetooth-adapter werkt ook. Home Assistant selecteert de bereikbare connectable adapter; deze versie dwingt geen specifieke proxy af. Er is geen directe ESPHome-API-client of aparte BLE-scanner in deze integratie.

1. Sluit de officiële app en nRF Connect zodat zij geen verbinding vasthouden.
2. Activeer Bluetooth op de C15 volgens de handleiding.
3. Open het toegevoegde apparaat en druk op **GATT inspecteren**. Er is geen automatische polling of automatische verbinding bij opstarten.
4. De sensor toont `expected_uuids_found` wanneer de twee verwachte characteristics onder de config-service gevonden zijn, of `expected_uuids_missing`. Dit zegt alleen iets over UUID-aanwezigheid, niet over authenticatie, relaisstatus of schrijfbaarheid.
5. De sensor toont `unavailable` na een mislukte inspectie. De knop blijft beschikbaar om opnieuw te proberen. Controleer de tijd `scanned_at`: een geslaagde inspectie blijft als historische uitslag staan en bewijst geen huidige verbinding.
6. Download bij de integratie de diagnostiek via het menu en stuur dat JSON-bestand terug. Het bevat service-UUID's en characteristic-properties, geen MAC-adres, PIN of characteristicwaarden. Bij fouten blijven eerdere succesvolle metadata behouden, expliciet als `last_successful_scan`.
7. Controleer dat er geen relaisactie plaatsvindt. Test ook met gesloten Bluetooth-venster en herhaal na opnieuw activeren. Een verbinding kan circa 55 seconden kosten inclusief opruimen.

Voor betrouwbaar schakelen zijn daarnaast Android HCI-captures nodig van verbinden/authenticatie, status lezen, FIX AAN/UIT, AUTO en override vanuit beide relaistoestanden, inclusief tijdstippen en fysieke relaisindicatie. Deze versie verzamelt die protocolpayloads niet.

## Implementatie en verificatie

De transportlaag gebruikt `bluetooth.async_ble_device_from_address(..., connectable=True)` en `bleak_retry_connector.establish_connection`. Daarmee volgt deze de HA-route voor lokale en proxy-adapters: https://developers.home-assistant.io/docs/bluetooth/ . De verbinding wordt na de inspectie gesloten. Er worden geen willekeurige reads, writes, pairing of firmwareacties uitgevoerd.

Lokaal gecontroleerd: Python-syntax, JSON, pakketstructuur en geïsoleerde transporttests met namaakapparaten. Niet uitgevoerd: laden in een echte Home Assistant-installatie, hassfest/HACS-validator, een echte ESPHome-proxyverbinding of C15-hardwaretest. Dit pakket mag daarom niet als hardwaregetest worden beschouwd.

Transporttests: `python -m unittest discover -s tests -v`. Deze vereisen geen Home Assistant of Bluetooth-hardware.

Verwijderen: verwijder eerst de integratie via Apparaten & diensten, verwijder daarna via HACS of de map in custom_components en herstart Home Assistant.
