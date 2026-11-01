# Programma-uitlezing: APK-bewijs

Bron: dezelfde APK en SHA256 als [status-protocol.md](status-protocol.md). Versie in de bestandsnaam is 2.3.9/build 2700; appmanifest en ondertekening zijn niet onafhankelijk gecontroleerd. Deze programmauitlezing is nog niet op echte C15-hardware bevestigd.

## Overdracht

- `Base.dll`, `BluetoothConnection.<ReceiveTimerProgram>d__116.MoveNext`, IL 00b9–00e0: schrijf DirectionRead via WriteCommandCreator.Direction. IL 013e–0143: Delay(500). IL 019d–01a4: ReadTimerProgramAsync. BluetoothConnectionNew heeft dezelfde volgorde.
- `Interfaces.dll`, `AConnectionProtocol` statische initialisatie: DirectionRead=0, DirectionWrite=1. De integratie schrijft uitsluitend 00. PackageCreator.AssembleDirectionPackage produceert één byte; WriteCommandCreator.Direction gebruikt MemoryService/type 11.
- `ReadTimerProgramAsync` leest type 12 voor het pakketaantal (IL 002f–0049), daarna precies zoveel reads van type 14 (00dd–00f7). Er is geen write naar count, inhoud of confirmatie nodig in dit leespunt.
- `PackageReader.DisassemblePackageCount` combineert byte 1 << 8 met byte 0: little-endian UInt16.
- `Mobile.dll`, BluetoothService.<ReadMemoryCharacteristic>d__55: gebruikt protocol.MemoryService, GetCharacteristic(type).UUID en ReadCharacteristic. Het pad vereist hier geen notificatieabonnement.
- MemoryService=`ec04000a-04da-47e5-add4-8ed1c9d52fec`; Direction/type 11=`ec04000b-...`; PackageCount/type 12=`ec04000c-...`; Content/type 14=`ec04000e-...`. De suffix is steeds `04da-47e5-add4-8ed1c9d52fec`.
- GetCharacteristicByteSizes in Interfaces.dll definieert type 12 als 2 bytes en type 14 als 14 bytes.

De gebruiker heeft de memory-service en deze characteristics via GATT-diagnostiek aangetoond. Dat bewijst nog niet de daadwerkelijke inhoud of toegang op iedere firmware/PIN-configuratie. De integratie begrenst de overdracht op 90 seconden en 2048 pakketten als eigen beschermingsgrenzen, niet als protocolconstanten. Na een pakketfout wordt niet blind verdergelezen of opnieuw geprobeerd; de volgende handmatige poging begint opnieuw met leesrichting 00.

## Pakketinterpretatie

`PackageReader.DisassembleContentBufferPackage` gebruikt `byte0 & 0x1c` als type: 0 programmakop, 4 datumperiode, 8 schakelopdracht, 12 kanaalnaam. Programma-ID is `((byte0 & 1) << 8) | byte1`; dit is een groeps-ID, niet een oplopend ontvangstvolgnummer. QueueProcessor.TimerProgramFromQueue/ProcessTimerProgramPackageQueue koppelt datumperiodes en opdrachten aan hun programmakop, ook als die later in de ontvangstqueue komt.

- ProgramHeaderFromByteArray: naam bytes 2–12, prioriteit byte 13. De serializer zet bit 1 van byte 0 wanneer er datumperiodes zijn.
- DateRangeFromByteArray: start jaar/maand/dag op 2/3/4, eind op 5/6/7. Jaaroffset 1900; jaar/maand 255 betekent wildcard.
- TimeCommandFromByteArray: action/timetype byte 2, kanaalmasker byte 3, signed offset byte 4, weekdagmasker byte 5. De offset blijft voorlopig als ruwe signed waarde zichtbaar.
- TypesToByte en TimeCommandTypeFromByte, plus CommandType-constanten: AAN=16, UIT=8, PULS=4, CYCLUS=2, WILLEKEURIG_AAN=17, WILLEKEURIG_UIT=9 in de laagste vijf bits. Niet-herkende acties worden niet naar AAN teruggezet.
- TimeTypeFromByte en enum TimeType: 0 vaste tijd, bit 6 zonsopkomst, bit 5 zonsondergang.
- ChannelsFromByte gebruikt bitindexen vanaf nul; het overzicht toont die als kanaalnummer index+1. WeekdaysFromByte gebruikt .NET DayOfWeek: zondag bit 0, maandag bit 1, enzovoort.
- TimeSpanFromByte: vijf lage bits voor uur, zes lage bits voor minuut/seconde. Vaste tijd op bytes 6/7; puls/cyclusduration op 8–10, pause op 11–13. De hoge bits van het eerste tijdbyte kunnen dagen bevatten; deze eerste decoder weigert zulke waarden en bewaart het pakket als waarschuwing in plaats van een onjuist tijdstip te tonen.
- De app gebruikt CP1252 met aanvullende Tsjechische/Poolse vervangingen voor namen. Die speciale vervangingen zijn niet geïmplementeerd; namen met hoge bytes krijgen daarom een coderingswaarschuwing. Ruwe blokken blijven behouden.

Er is geen checksum aangetroffen in dit afgebakende leespad; dit bewijst niets over andere overdrachtspaden. Er is geen programmeringseditor of uploadfunctie toegevoegd. De decoderresultaten moeten nog vergeleken worden met een echt schema uit de officiële app, vooral complexe astro-, datum-, puls- en cyclusregels.
