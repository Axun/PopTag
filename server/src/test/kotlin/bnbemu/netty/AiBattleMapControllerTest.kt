package bnbemu.netty

import bnbemu.packet.PracticeStartInfo
import bnbemu.packet.encodeName
import bnbemu.server.*
import io.netty.buffer.Unpooled
import io.netty.channel.embedded.EmbeddedChannel
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class AiBattleMapControllerTest {
    @Test fun aiBattleElectsTheLocalScriptControllerWithoutReplacingItsTeamColor() {
        val socket=ClientSocket();val channel=EmbeddedChannel(socket)
        val user=User(socket,19125,"ai-map-owner-test")
        val oldMode=Room.localGameMode;val saved=Room.slots.map { it.user to it.meta.copyOf() }
        try {
            Room.reset();Room.slots.forEach { it.user=null }
            Room.slots[0].user=user;Room.slots[0].color=3
            for(mode in listOf(0,15,16)) {
                Room.localGameMode=mode
                val b=Unpooled.buffer()
                try {
                    PracticeStartInfo(user=user).encode(SendPacketBase(b,3))
                    val raw=ByteArray(b.readableBytes());b.getBytes(0,raw)
                    val token=encodeName(user.name)
                    val at=(5..raw.size-token.size).first { n -> token.indices.all { raw[n+it]==token[it] } }
                    val meta=(((raw[at-5].toInt() and 255) shl 8) or (raw[at-4].toInt() and 255)) xor 0xa569
                    assertEquals(2,meta and 2,"Mode $mode must retain local map-script control after S100")
                    val color=(raw[at-3].toInt() and 255) xor 0x5a
                    assertEquals(if(mode==16)0 else 3,color,"AI battle keeps its native team color")
                } finally { b.release() }
            }
        } finally {
            Room.reset();Room.localGameMode=oldMode
            Room.slots.forEachIndexed { i,s -> s.user=saved[i].first;saved[i].second.copyInto(s.meta) }
            channel.finishAndReleaseAll()
        }
    }
}
