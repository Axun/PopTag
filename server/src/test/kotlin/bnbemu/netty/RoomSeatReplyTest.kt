package bnbemu.netty

import bnbemu.server.*
import io.netty.buffer.Unpooled
import io.netty.channel.embedded.EmbeddedChannel
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class RoomSeatReplyTest {
    @Test fun allSeatRequestsAcknowledgeWithoutLosingEitherHuman() {
        OpcodeManager.recvOps
        val c=ClientSocket();val ch=EmbeddedChannel(c)
        val saved=Room.slots.map {Triple(it.user,it.isAI,it.meta.copyOf())};val mode=Room.localGameMode
        try {
            c.users.addAll(listOf(User(c,29312,"seat-human-one"),User(c,29313,"seat-human-two")))
            for(m in listOf(0,14,15,16)) for(seat in 0..7) for(action in 0..1) {
                Room.reset();Room.localGameMode=m
                Room.slots.forEach {it.user=null;it.isAI=false;it.state=1}
                c.users.forEachIndexed {i,u->Room.slots[i].user=u;Room.slots[i].state=0}
                val b=Unpooled.buffer();SendPacketBase(b,3).apply {Encode2(89);Encode1((seat shl 4) or action)}
                ch.writeInbound(b)
                var response:Int?=null
                while(true) {
                    val p=ch.readOutbound<PKT>() ?: break
                    if(OpcodeManager.getSendOp(p::class.java)==106) {
                        val wire=Unpooled.buffer()
                        try {p.encode(SendPacketBase(wire,3));response=wire.Decode1} finally {wire.release()}
                    }
                }
                assertNotNull(response,"S106 unlock required: mode=$m seat=$seat action=$action")
                assertEquals(seat,response!! ushr 4)
                assertEquals(if(Room.slots[seat].state.toInt() and FLAG_CLOSED != 0) 1 else 0,response!! and 1)
                assertSame(c.users[0],Room.slots[0].user);assertSame(c.users[1],Room.slots[1].user)
                assertFalse(Room.slots[1].isAI)
                if(m in 14..15 || (m==16 && seat<4))assertFalse(Room.slots[seat].isAI)
            }
        } finally {
            Room.reset();Room.localGameMode=mode
            Room.slots.forEachIndexed {i,s->s.user=saved[i].first;s.isAI=saved[i].second;saved[i].third.copyInto(s.meta)}
            ch.finishAndReleaseAll()
        }
    }
}
