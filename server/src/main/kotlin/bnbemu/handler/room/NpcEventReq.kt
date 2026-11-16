package bnbemu.handler.room

import bnbemu.netty.Decode2
import bnbemu.netty.PKTHandler
import bnbemu.packet.NpcEvent
import bnbemu.server.Room

// EN op156 is emitted by NPC room timers (0x52D56E) and battle AI events.
// It is unrelated to the legacy TW AirplaneReq that previously disconnected EN.
val NpcEventReq = PKTHandler { c ->
    if (readableBytes() != 6 || Room.localGameMode != 16) return@PKTHandler
    val slot = Decode2
    val event = Decode2
    val parameter = Decode2
    if (slot !in 4..7 || !Room.slots[slot].isAI) return@PKTHandler
    val response = NpcEvent(slot, event, parameter)
    if (Room.uniqueClients.any()) Room BC response else c send response
}
