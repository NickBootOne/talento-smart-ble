# Talento smart BLE

[![Controles](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/check.yml/badge.svg?branch=main&event=push)](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/check.yml)
[![Release](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/release.yml/badge.svg)](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/release.yml)

Home Assistant-integratie voor de Grässlin talento smart C15, via een ESPHome Bluetooth Proxy of lokale Bluetooth-adapter. Actuele versie: **2026.11.6**.

## Functies

- Relaisstatus en modus van kanaal 1 uitlezen, circa elke 30 seconden.
- Relais bedienen met FIX AAN en FIX UIT.
- AUTO herstellen zodat het bestaande tijdprogramma weer de schakelingen bepaalt.
- Iedere schakelopdracht teruglezen en controleren.
- GATT-inspectie en downloadbare diagnostiek.
- Opgeslagen programmering ophalen en programmanamen, weekdagen, tijden en datumperiodes bekijken.

FIX/AUTO-bediening werkt volgens de praktijktest van de gebruiker via een ESP32-proxy. AUTO/UIT is fysiek bevestigd; de aangeleverde diagnostiek bevestigt AUTO als laatste opdracht. Langdurige bereikbaarheid, alle firmwarevarianten en PIN-beveiligde apparaten zijn niet volledig gevalideerd. Override, PIN-authenticatie en tijdprogramma's bewerken worden nog niet ondersteund. Deze naamwijziging voegt geen nieuwe protocolfuncties toe.

## Installeren via HACS

1. Open HACS → menu → Aangepaste repositories.
2. Voeg `https://github.com/NickBootOne/talento-smart-ble` toe als type **Integratie**.
3. Download de integratie en herstart Home Assistant volledig.
4. Ga naar Instellingen → Apparaten & diensten → Integratie toevoegen → **Talento smart BLE**.
5. Voer het Bluetooth-MAC-adres van de C15 in, niet dat van de ESP32.

Het MAC-adres staat op de C15 onder Menu → Config/Konfig → Bluetooth → Smart Link. Gebruik de notatie `AA:BB:CC:DD:EE:FF`.

Handmatig installeren kan ook: kopieer `custom_components/talento_smart_ble` uit de broncode naar `/config/custom_components/talento_smart_ble` en herstart Home Assistant. Home Assistant installeert bleak-retry-connector; hiervoor is internettoegang nodig. Installatie valideert het adresformaat, niet meteen de bereikbaarheid van het apparaat.

## Bluetooth Proxy

Gebruik een ESPHome Bluetooth Proxy die al aan Home Assistant is toegevoegd, met actieve verbindingen:

```yaml
bluetooth_proxy:
  active: true
```

Plaats de proxy dicht genoeg bij de C15. Sluit de officiële telefoonapp of nRF Connect tijdens bediening vanuit HA. Activeer zo nodig Bluetooth op de C15. Home Assistant kiest een bereikbare connectable adapter; de integratie legt geen specifieke proxy vast.

## Bediening

| Naam | Functie |
|---|---|
| Relais (FIX-bediening) | AAN = FIX AAN, UIT = FIX UIT; weergegeven toestand komt uit de relaisreadback |
| AUTO herstellen | Het tijdprogramma weer laten bepalen wanneer het relais schakelt |
| Kanaal 1 status vernieuwen | Direct een nieuwe meting opvragen |
| Modus | AUTO, FIX_ON, FIX_OFF of OVR, indien de retourwaarde herkend wordt |
| Relaisstatus | De uitgelezen relaisstand |
| Ruwe kanaalstatus | De ontvangen statusbyte |
| GATT inspecteren | Services en characteristic-properties verzamelen |
| Laatste GATT-inspectie | Historische uitslag van de handmatige inspectie |
| Programmering ophalen | Een momentopname van de opgeslagen programmering uitlezen |
| Programmering | Uitleesresultaat, aantallen en het programma-overzicht in de attributen |

**FIX blijft actief totdat je AUTO herstelt.** De schakelaar kan in AUTO de relaisstand tonen, maar bedienen schakelt expliciet over op FIX. AUTO is geen UIT-opdracht: afhankelijk van het tijdprogramma kan het relais aan of uit staan.

Na een update: herstart Home Assistant, activeer zo nodig Bluetooth en gebruik **Kanaal 1 status vernieuwen**. De bestaande configuratie, unique IDs en entity IDs blijven behouden. De automatisch aangemaakte integratietitel wordt bijgewerkt; zelf gekozen namen blijven staan. Handmatig gekozen entiteitsnamen kun je zelf aanpassen. Oude entity IDs kunnen nog `test` bevatten: ze worden niet gewijzigd om dashboards en automatiseringen te behouden.

## Status en bereikbaarheid

Home Assistant leest circa elke 30 seconden zolang de entiteiten geladen zijn en polling niet bij de systeemopties is uitgeschakeld. Na opstarten kan de eerste automatische meting ongeveer 30 seconden duren. Tijdens normaal uitlezen blijft de vorige verse meting zichtbaar; tijdens een schakelopdracht wordt deze ongeldig totdat teruglezen de opdracht bevestigt.

Bij een mislukte read wordt de status unavailable. Zonder nieuwe resultaten verloopt een meting na circa twee minuten. Onbekende retourwaarden worden alleen als ruwe waarde getoond; relais en modus blijven dan unavailable. Bij een fout na een schakelwrite kan het relais al zijn geschakeld. De integratie schrijft niet automatisch opnieuw of een tegengesteld commando. Controleer de C15, lees opnieuw en herstel zo nodig AUTO op het apparaat of in de officiële app.

Automatische polling garandeert niet dat een gesloten Bluetooth-venster op de C15 opnieuw geopend kan worden. Bij wegvallende status: controleer proxyplaatsing en Bluetooth-activering en download de diagnostiek terwijl de fout optreedt.

## Diagnostiek

### Programma-overzicht op je dashboard

1. Update naar **2026.11.6**, herstart Home Assistant en druk opnieuw op **Programmering ophalen**.
2. Open [de kant-en-klare dashboardkaart](examples/programmering-kaart.yaml) en kopieer de volledige YAML-inhoud.
3. Open je HA-dashboard → Bewerken → Kaart toevoegen → Handmatig en plak de inhoud. Sla de kaart op.

De kaart zoekt zelf de programmeringssensoren van deze integratie op via een herkenningsattribuut. Je hoeft geen entity-ID in te vullen en er is geen extra frontendplugin nodig. De kaart is een standaard Markdown-kaart; zij wordt niet automatisch aan je dashboard toegevoegd door de integratie-update.

Je ziet programma, compacte weekdagen, tijd, actie en kanaal in een tabel, met datumperiodes en ophaaltijd eronder. Identieke regels binnen hetzelfde programma worden alleen voor de weergave samengevoegd; de kaart vermeldt het aantal herhalingen. Ruwe pakketten, de oorspronkelijke regels en aantallen blijven in de diagnostiek behouden. Dit lost de nog onbekende oorzaak van de herhaalde pakketten niet op. De naamdecoder controleert nu uitsluitend bytes vóór het einde van een naam, zodat opvulbytes geen onterechte coderingswaarschuwing meer geven.

De sensor **Programmering** toont nu het aantal programma's. `display_rows` bevat de tabelregels, `display_rule_count` het unieke aantal en `duplicate_rule_count` het aantal samengevoegde herhalingen. `complete` blijft aangeven of alle ontvangen structuren herkend zijn; de kaart toont een melding bij onvolledige interpretatie. Dit is een momentopname, geen berekening van het volgende schakelmoment.

### Programmering ophalen

1. Werk bij naar **2026.11.5**, herstart Home Assistant en activeer zo nodig Bluetooth op de C15.
2. Druk op **Programmering ophalen**. Dit gebeurt alleen op verzoek, niet iedere 30 seconden.
3. Open de entiteit **Programmering** en bekijk de attributen: `overview` bevat maximaal 30 herkenbare regels met programmanamen, weekdagen, tijd of astrotype, actie en kanaal. `program_summaries` bevat maximaal 20 programma's met naam, prioriteit en maximaal twee datumperiodes per programma. Een jaartal of maand met `null` betekent een wildcard.
4. Vergelijk het resultaat met de officiële app. De nieuwe uitleesfunctie is nog niet op C15-hardware bevestigd. Deel de diagnostiek na de eerste uitlezing, ook bij een fout.

Het volledige resultaat, alle datumperiodes, waarschuwingen en ruwe pakketten staan in de gedownloade diagnostiek onder `programming.snapshot`. Programmanamen en tijdschema's kunnen persoonlijke routines beschrijven; controleer deze voordat je het bestand openbaar deelt. Attribuutvlaggen geven aan of het zichtbare overzicht is ingekort. `rule_count` telt alleen herkende regels.

De sensor toont het aantal programma's. Het attribuut `complete` geeft aan of alle ontvangen blokken herkend zijn; dit is nog geen garantie van hardwaregevalideerde interpretatie. Bij `complete: false` zijn sommige regels/velden niet veilig vertaald. De ruwe gegevens blijven behouden en ontbrekende regels worden niet gegokt. Grote puls-/cyclusduren en speciale naamcoderingen kunnen nog aanvullend werk vragen. Astrotijden worden als zonsopkomst/zonsondergang weergegeven, met de ruwe offset; er wordt geen volgend schakelmoment berekend. Extra astrocorrectievlaggen blijven als ruwe gegevens bewaard met waarschuwing.

De momentopname wordt niet automatisch vernieuwd na wijzigingen in de officiële app en verdwijnt na een HA-herstart. Druk opnieuw op de ophaalknop om haar te vernieuwen. Tijdens de overdracht (maximaal circa 100 seconden inclusief afsluiten) wachten statuslezen en schakelopdrachten op dezelfde verbindingsvergrendeling.

De enige write in dit pad is leesrichting `00` naar de overdrachtscharacteristic. Er worden geen programma's, pakkettellers, klokinstellingen of relaiscommando's geschreven. [Protocolbewijs en grenzen](docs/program-protocol.md).

Download de diagnostiek bij Instellingen → Apparaten & diensten → Talento smart BLE → menu. Vanaf 2026.11.4 heet de hoofdsectie `status` (voorheen `status_test`).

- `last_command`: laatste opdracht en confirmed/not_sent/unconfirmed.
- `measurement`: ruwe status, modus, relaisstand en meettijd.
- `failure`: stap, foutklasse en eventueel of het commando mogelijk al uitgevoerd is.
- `freshness_reason`: never_read, fresh, expired of last_read_failed.
- `measurement_age_seconds` en `poll_interval_seconds`: meetleeftijd en verversinterval.

De eigen integratiediagnostiek bevat geen MAC-adres, PIN of authenticatiepayloads. HA voegt algemene installatiegegevens toe; controleer het bestand voordat je het openbaar deelt.

## Ontwikkeling en updates

[Vervolgstappen en open issues](https://github.com/NickBootOne/talento-smart-ble/issues) · [APK-protocolbewijs](docs/status-protocol.md) · [Releases](https://github.com/NickBootOne/talento-smart-ble/releases)

Versies volgen **JAAR.MAAND.VOLGNUMMER**: 2026.11.1, 2026.11.2 enzovoort. Het laatste getal is geen dagnummer; de teller begint iedere maand op 1. Werk manifest, diagnostiek en README bij en push de overeenkomstige tag, bijvoorbeeld `v2026.11.5`. De Release-workflow controleert de versie, draait de tests en publiceert een release. HACS controleert periodiek op updates; installeren en een HA-herstart gebeuren niet vanzelf. Automatisch installeren vereist een eigen automatisering met `update.install`.

Geïsoleerde tests uitvoeren: `python -m unittest discover -s tests -v`. Deze controleren protocol, transacties en coordinatorgedrag met namaakafhankelijkheden. Volledige HA-runtime-tests, hassfest/HACS-validator en langdurige hardwareverificatie zijn nog niet uitgevoerd. De minimale HA-versie in hacs.json is een ontwikkeldoel, geen volledige compatibiliteitsgarantie.

Voor een eigen fork: `python prepare_repository.py EIGENAAR/REPOSITORY` vult de manifestlinks en codeowner in. Zet custom_components, hacs.json en brand rechtstreeks in de repositoryhoofdmap.

Verwijderen: verwijder de integratie via Apparaten & diensten, daarna via HACS of de map in custom_components en herstart HA.
