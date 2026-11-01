# Bewijs voor de handmatige statusleestest

Bron: talentosmart_2_3_9_2700.apk, SHA256 `f8669604adc5f1429811957b325c33ccd3a77f8a9bbae67c7cc5dbeca92e5cdd`.
Bestandsnaamversie is 2.3.9/build 2700; manifestversie en uitgevershandtekening zijn niet onafhankelijk gecontroleerd. Onderstaande offsets zijn IL-offsets binnen methoden, geen APK-bestandsoffsets.

- `Base.dll`, `Graesslin.V16.Core.Base.Channel.get_ChannelNr`, IL 0001–0009: `Id + 1`; de eerste kanaal-ID is nulgebaseerd. De test gebruikt alleen het eerste timerkanaal, nummer 1.
- `Base.dll`, `PackageCreator.AssembleChannelIdPackage`, IL 0001–000d: characteristic-type 4, één byte, kanaalnummer op index 0.
- `Base.dll`, `WriteCommandCreator.ChannelId`: gebruikt ConfigService en characteristic-type 4. De test selecteert kanaal 1 met `01`; dit is geen relaiscommando.
- `Base.dll`, `BluetoothConnection.<ReadChannelState>d__113.MoveNext`: selectiewrite op IL 0109–012c, Delay(1000) op IL 01a4–01a9, ReadSettingsCharacteristic(type 8) op IL 0224–023d.
- Het overeenkomstige pad in `BluetoothConnectionNew` doet eveneens kanaalselectie, Delay(1000), daarna een read van type 8. De test implementeert geen van beide authenticatiehandshakes.
- `Base.dll`, `PackageReader.DisassembleChannelState`: gebruikt byte 0 voor `ChannelTypeFromByte` en `RelaisStateFromByte`.
- `ChannelTypeFromByte` (switch vanaf IL 000d): 0/1 = AUTO, 2 = enum 2 (FixON), 3 = enum 3 (FixOFF), 4/5 = enum 1 (OVR).
- `RelaisStateFromByte`, IL 000e–0019: true bij 1, 2, 4; anders false. De test combineert die regels alleen voor 00–05 en weigert andere waarden als geïnterpreteerde toestand.
- UUID-opbouw: `Interfaces.dll`, `ConnectionProtocolManager.InitTimerConnectionProtocol`, prefix EC04 en suffix 04DA-47E5-ADD4-8ED1C9D52FEC; `AConnectionProtocol.GetGuidByString` en type-UUID-conversie. ConfigService is EC040000; kanaalselectie EC040004; status EC040008.

De GATT-export van de gebruiker bevestigde beide characteristics in de config-service met read, write en write-without-response. Dat is geen bewijs van autorisatie of toegestane toegang zonder PIN. De test kiest een write met response wanneer de characteristic dat aanbiedt, anders zonder response. Er worden geen abonnements- of authenticatiewrites gedaan. Alleen de selectiewrite en statusread worden uitgevoerd; geen CRC wordt toegevoegd, omdat deze serializer één byte produceert. Dit bewijst niet dat overige protocolpaden geen checksums hebben.

## Schrijfpad voor FIX en AUTO (2026.11.2)

`Base.dll`, `BluetoothConnection.<WriteChannelState>d__112.MoveNext` schrijft eerst ChannelId (IL 0109–012c), wacht de meegegeven delay (01c6–01cc) en schrijft daarna ChannelState (025a–027d). `WriteCommandCreator.ChannelState` richt de payload op ConfigService/type 8. `PackageCreator.AssembleChannelStatePackage` maakt één byte via `ChannelStateToByte` (switch vanaf IL 000d). Enumwaarden in Interfaces.dll: AUTO=0, OVR=1, FixON=2, FixOFF=3; de encoder vertaalt naar respectievelijk 00, 03, 01, 02.

De integratie implementeert alleen AUTO=00, FIX_ON=01 en FIX_OFF=02. De kanaalselectie en wachttijd zijn gelijk aan de inmiddels werkende statusleestest. Een extra pre-read en een readback na de opdracht zijn integratiecontroles; de wachttijd van één seconde na de relaiswrite is een conservatieve testinstelling en nog niet hardwaregevalideerd. De statuswrite wordt éénmaal met response uitgevoerd en niet opnieuw geprobeerd. Na een tweede kanaalselectie en één seconde wachten moet de teruggelezen modus overeenkomen; FIX controleert tevens de relaisstand. AUTO controleert de modus zonder een bepaalde relaisstand te eisen.

Hardwarebewijs tot nu toe: de aangeleverde diagnostiek van versie 2026.11.1 bevat raw_hex=00, mode=AUTO, relay=false, zonder leesfout; de gebruiker bevestigde dat het relais fysiek UIT stond. Dit valideert nog niet de schakelopdrachten of andere statuswaarden.

## Resterende verificatie

Vergelijk ruwe status met fysieke relaisstand in AUTO, FIX en OVR. Bij fouten: diagnostiek met stap en foutklasse. Voor PIN-apparaten en verdere bediening blijven volledige statische analyse en waar nodig officiële-app HCI-captures nodig. Hogere statuswaarden (zoals 08–0d) hebben in de APK afwijkende/ambigue relaisinterpretatie en worden bewust niet vertaald. Er is geen betrouwbare live-status of permanente bereikbaarheid aangetoond.
