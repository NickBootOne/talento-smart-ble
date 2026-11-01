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

## Nog nodig

Vergelijk ruwe status met fysieke relaisstand in AUTO, FIX en OVR. Bij fouten: diagnostiek met stap en foutklasse. Voor PIN-apparaten en verdere bediening blijven volledige statische analyse en waar nodig officiële-app HCI-captures nodig. Hogere statuswaarden (zoals 08–0d) hebben in de APK afwijkende/ambigue relaisinterpretatie en worden bewust niet vertaald. Er is geen betrouwbare live-status of permanente bereikbaarheid aangetoond.
