# Talento smart BLE

[![Controles](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/check.yml/badge.svg?branch=main&event=push)](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/check.yml)
[![Release](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/release.yml/badge.svg)](https://github.com/NickBootOne/talento-smart-ble/actions/workflows/release.yml)

Home Assistant-integratie voor de Grässlin talento smart C15, via een ESPHome Bluetooth Proxy of lokale Bluetooth-adapter. Actuele versie: **2026.11.4**.

## Functies

- Relaisstatus en modus van kanaal 1 uitlezen, circa elke 30 seconden.
- Relais bedienen met FIX AAN en FIX UIT.
- AUTO herstellen zodat het bestaande tijdprogramma weer de schakelingen bepaalt.
- Iedere schakelopdracht teruglezen en controleren.
- GATT-inspectie en downloadbare diagnostiek.

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

**FIX blijft actief totdat je AUTO herstelt.** De schakelaar kan in AUTO de relaisstand tonen, maar bedienen schakelt expliciet over op FIX. AUTO is geen UIT-opdracht: afhankelijk van het tijdprogramma kan het relais aan of uit staan.

Na een update: herstart Home Assistant, activeer zo nodig Bluetooth en gebruik **Kanaal 1 status vernieuwen**. De bestaande configuratie, unique IDs en entity IDs blijven behouden. De automatisch aangemaakte integratietitel wordt bijgewerkt; zelf gekozen namen blijven staan. Handmatig gekozen entiteitsnamen kun je zelf aanpassen. Oude entity IDs kunnen nog `test` bevatten: ze worden niet gewijzigd om dashboards en automatiseringen te behouden.

## Status en bereikbaarheid

Home Assistant leest circa elke 30 seconden zolang de entiteiten geladen zijn en polling niet bij de systeemopties is uitgeschakeld. Na opstarten kan de eerste automatische meting ongeveer 30 seconden duren. Tijdens normaal uitlezen blijft de vorige verse meting zichtbaar; tijdens een schakelopdracht wordt deze ongeldig totdat teruglezen de opdracht bevestigt.

Bij een mislukte read wordt de status unavailable. Zonder nieuwe resultaten verloopt een meting na circa twee minuten. Onbekende retourwaarden worden alleen als ruwe waarde getoond; relais en modus blijven dan unavailable. Bij een fout na een schakelwrite kan het relais al zijn geschakeld. De integratie schrijft niet automatisch opnieuw of een tegengesteld commando. Controleer de C15, lees opnieuw en herstel zo nodig AUTO op het apparaat of in de officiële app.

Automatische polling garandeert niet dat een gesloten Bluetooth-venster op de C15 opnieuw geopend kan worden. Bij wegvallende status: controleer proxyplaatsing en Bluetooth-activering en download de diagnostiek terwijl de fout optreedt.

## Diagnostiek

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
