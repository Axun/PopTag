package bnbemu.netty

import bnbemu.data.FxdynMapInfo
import bnbemu.handler.room.mapIdTable
import bnbemu.server.LocalMapBounds
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class DungeonMapsTest {
    @Test fun everyDungeonBoardHasAUniquePlayableEntryAndNativeResourceIndex() {
        val rows=FxdynMapInfo.gameRecords.filter {it.flag==0 && it.group=="Tomb"}
        assertEquals(23,rows.size)
        val native=javaClass.getResourceAsStream("/data/ported-native-map-indices.tsv")!!.bufferedReader().useLines {
            it.associate {line -> line.substringAfter('\t') to line.substringBefore('\t').toInt()}
        }
        for(i in 1..22) {
            val name="Tomb"+i.toString().padStart(2,'0')
            val row=rows.single {it.name==name}
            assertEquals(native[name],row.sortOrder)
            assertEquals("Tomb",row.stage)
            assertEquals(0,row.subtype)
            assertEquals(1,mapIdTable.values.count {it.name==name})
            assertEquals(15,LocalMapBounds.forBoard(name)?.width)
            assertEquals(13,LocalMapBounds.forBoard(name)?.height)
            assertEquals("地牢"+i.toString().padStart(2,'0'),FxdynMapInfo.localizedRecords.single {it.flag==0 && it.name==name}.display)
        }
        val group=rows.single {it.name=="TombRandom"}
        assertEquals("none",group.stage)
        assertEquals(1,group.subtype)
    }
}
